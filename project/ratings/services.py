from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from django.db import transaction

from .models import RatingHistory


# -----------------------------------
# 하이퍼파라미터
# -----------------------------------

# 1. 승패 기본 점수
BASE_WIN_SCORE = 50
BASE_LOSE_SCORE = -50

# 2. 개인 추가 점수 가중치
KDA_WEIGHT = 0.35
GOLD_WEIGHT = 0.35
KP_WEIGHT = 0.30

# 3. 스케일 파라미터
GOLD_SCALE = 5000.0
KP_SCALE = 0.20
EPSILON = 0.1

# 4. 개인 추가 점수 범위 제한
PERSONAL_DELTA_MIN = -50.0
PERSONAL_DELTA_MAX = 50.0

# 5. PS 1000 회귀 파라미터
REGRESSION_CENTER = 1000.0
REGRESSION_SCALE = 400.0
REGRESSION_ALPHA = 0.25

WIN_FACTOR_MIN = 0.60
LOSE_FACTOR_MAX = 1.40


# -----------------------------------
# 데이터 파싱용
# -----------------------------------

@dataclass
class ParsedKDA:
    kills: int
    deaths: int
    assists: int


def parse_kda(kda_str: str) -> ParsedKDA:
    """
    '10/2/8' 형태의 문자열을 파싱한다.
    """
    try:
        k, d, a = map(int, kda_str.split("/"))
        return ParsedKDA(kills=k, deaths=d, assists=a)
    except Exception:
        return ParsedKDA(kills=0, deaths=0, assists=0)


# -----------------------------------
# 공통 유틸
# -----------------------------------

def clip(value: float, min_value: float, max_value: float) -> float:
    """
    값을 범위 내로 제한한다.
    """
    return max(min_value, min(value, max_value))


def safe_tanh(value: float) -> float:
    """
    tanh 래퍼
    """
    return math.tanh(value)


def get_lane_preference_type(player, selected_lane: str) -> str:
    """
    주포지션 / 부포지션 / 비선호 포지션 판정
    """
    if selected_lane == player.player_main_position:
        return "MAIN"

    if selected_lane == player.player_secondary_position:
        return "SECONDARY"

    return "OFFROLE"


def calculate_team_total_kills(details: Iterable) -> int:
    """
    팀 총 킬 계산
    """
    total = 0
    for detail in details:
        parsed = parse_kda(detail.player_kda)
        total += parsed.kills
    return total


def calculate_kill_participation(detail, team_kills: int) -> float:
    """
    킬 관여율 계산
    KP = (킬 + 어시스트) / 팀 총 킬
    """
    if team_kills <= 0:
        return 0.0

    parsed = parse_kda(detail.player_kda)
    return (parsed.kills + parsed.assists) / team_kills


def calculate_kda_ratio(detail) -> float:
    """
    KDA 비율 계산
    KDA = (킬 + 어시스트) / max(1, 데스)
    """
    parsed = parse_kda(detail.player_kda)
    return (parsed.kills + parsed.assists) / max(1, parsed.deaths)


def get_opponent_by_lane(detail, opponent_team_details):
    """
    같은 라인의 맞라이너를 찾는다.
    """
    for opponent in opponent_team_details:
        if opponent.player_selected_lane == detail.player_selected_lane:
            return opponent
    return None


# -----------------------------------
# 개인 점수 계산
# -----------------------------------

def calculate_kda_comparison_score(detail, opponent_detail) -> float:
    """
    맞라이너와의 KDA 비율 비교 점수
    범위는 대체로 (-1, 1)
    """
    if opponent_detail is None:
        return 0.0

    my_kda = calculate_kda_ratio(detail)
    opp_kda = calculate_kda_ratio(opponent_detail)

    value = math.log((my_kda + EPSILON) / (opp_kda + EPSILON))
    return safe_tanh(value)


def calculate_gold_comparison_score(detail, opponent_detail) -> float:
    """
    맞라이너와의 골드 차이 비교 점수
    """
    if opponent_detail is None:
        return 0.0

    gold_diff = float(detail.player_gold - opponent_detail.player_gold)
    return safe_tanh(gold_diff / GOLD_SCALE)


def calculate_kp_score(detail, team_kills: int, team_avg_kp: float) -> float:
    """
    팀 내 평균 킬관여율 대비 점수
    """
    kp = calculate_kill_participation(detail, team_kills)
    return safe_tanh((kp - team_avg_kp) / KP_SCALE)


def calculate_personal_score(detail, opponent_detail, team_kills: int, team_avg_kp: float) -> tuple[float, dict]:
    """
    개인 추가 점수의 원천이 되는 종합 점수 계산
    반환:
    - personal_delta: (-50, 50) 범위
    - debug_info: 각 요소 값
    """
    s_kda = calculate_kda_comparison_score(detail, opponent_detail)
    s_gold = calculate_gold_comparison_score(detail, opponent_detail)
    s_kp = calculate_kp_score(detail, team_kills, team_avg_kp)

    personal_score = (
        KDA_WEIGHT * s_kda +
        GOLD_WEIGHT * s_gold +
        KP_WEIGHT * s_kp
    )

    personal_delta = 50.0 * personal_score
    personal_delta = clip(personal_delta, PERSONAL_DELTA_MIN, PERSONAL_DELTA_MAX)

    debug_info = {
        "score_kda": s_kda,
        "score_gold": s_gold,
        "score_kp": s_kp,
        "personal_score": personal_score,
    }

    return personal_delta, debug_info


# -----------------------------------
# 1000 회귀 보정
# -----------------------------------

def get_regression_factor(current_ps: int, raw_delta: float) -> float:
    """
    1000을 향하도록 만드는 회귀 계수

    - PS가 1000보다 높으면:
      승리 시 덜 얻고, 패배 시 더 잃는다.
    - PS가 1000보다 낮으면:
      승리 시 더 얻고, 패배 시 덜 잃는다.
    """
    d = (current_ps - REGRESSION_CENTER) / REGRESSION_SCALE

    if raw_delta >= 0:
        # 이기는 방향 변화량
        factor = 1.0 - REGRESSION_ALPHA * d
        return max(WIN_FACTOR_MIN, factor)

    # 지는 방향 변화량
    factor = 1.0 + REGRESSION_ALPHA * d
    return min(LOSE_FACTOR_MAX, factor)


# -----------------------------------
# 핵심 계산식
# -----------------------------------

def calculate_player_delta(detail, my_team_details, opponent_team_details, did_win: bool) -> tuple[int, dict]:
    """
    플레이어 1명의 최종 PS 변화량 계산

    최종 구조:
    delta_raw = team_delta + personal_delta
    delta_final = delta_raw * regression_factor
    """
    current_ps = detail.player.player_power_score

    # 1. 팀 승패 기본 점수
    team_delta = BASE_WIN_SCORE if did_win else BASE_LOSE_SCORE

    # 2. 팀 평균 킬관여율
    team_total_kills = calculate_team_total_kills(my_team_details)
    kp_values = [calculate_kill_participation(d, team_total_kills) for d in my_team_details]
    team_avg_kp = sum(kp_values) / len(kp_values) if kp_values else 0.0

    # 3. 맞라이너 찾기
    opponent_detail = get_opponent_by_lane(detail, opponent_team_details)

    # 4. 개인 추가 점수
    personal_delta, debug_info = calculate_personal_score(
        detail=detail,
        opponent_detail=opponent_detail,
        team_kills=team_total_kills,
        team_avg_kp=team_avg_kp,
    )

    # 5. 회귀 전 점수
    raw_delta = team_delta + personal_delta

    # 6. 1000 회귀 계수
    regression_factor = get_regression_factor(current_ps, raw_delta)

    # 7. 최종 점수
    final_delta = round(raw_delta * regression_factor)

    debug_info.update(
        {
            "team_delta": team_delta,
            "personal_delta": personal_delta,
            "raw_delta": raw_delta,
            "regression_factor": regression_factor,
            "final_delta": final_delta,
            "kill_participation": calculate_kill_participation(detail, team_total_kills),
            "team_kills": team_total_kills,
            "lane_preference_type": get_lane_preference_type(detail.player, detail.player_selected_lane),
        }
    )

    return final_delta, debug_info


# -----------------------------------
# 롤백
# -----------------------------------

@transaction.atomic
def rollback_ratings_for_match(match):
    """
    해당 경기의 RatingHistory를 이용해 각 플레이어의 PS를 rating_before로 되돌린다.
    최신 경기 삭제 전용으로 사용한다.
    """
    histories = list(
        RatingHistory.objects.filter(match=match).select_related("player")
    )

    if not histories:
        match.is_rating_applied = False
        match.save(update_fields=["is_rating_applied"])
        return

    for history in histories:
        player = history.player
        player.player_power_score = history.rating_before
        player.save(update_fields=["player_power_score"])

    RatingHistory.objects.filter(match=match).delete()

    match.is_rating_applied = False
    match.save(update_fields=["is_rating_applied"])


# -----------------------------------
# 반영
# -----------------------------------

@transaction.atomic
def apply_ratings_for_match(match):
    """
    경기 결과를 기반으로 players.player_power_score를 직접 갱신하고,
    RatingHistory를 남긴다.
    """
    # 이미 반영된 이력이 있으면 중복 반영 방지
    if RatingHistory.objects.filter(match=match).exists():
        match.is_rating_applied = True
        match.save(update_fields=["is_rating_applied"])
        return

    details = list(match.player_details.select_related("player").all())

    team1_details = [detail for detail in details if detail.player_team == 1]
    team2_details = [detail for detail in details if detail.player_team == 2]

    if len(team1_details) != 5 or len(team2_details) != 5:
        raise ValueError("레이팅 반영을 위해서는 팀 1, 팀 2가 각각 5명이어야 합니다.")

    # 팀 1 처리
    for detail in team1_details:
        player = detail.player
        before = player.player_power_score

        final_delta, debug_info = calculate_player_delta(
            detail=detail,
            my_team_details=team1_details,
            opponent_team_details=team2_details,
            did_win=(match.win_team == 1),
        )

        after = max(1, before + final_delta)

        player.player_power_score = after
        player.save(update_fields=["player_power_score"])

        RatingHistory.objects.create(
            player=player,
            match=match,
            revision=1,
            rating_before=before,
            rating_after=after,
            delta_total=final_delta,
            delta_base=debug_info["team_delta"],
            delta_kp=debug_info["score_kp"] * 50.0 * KP_WEIGHT,
            delta_role=0.0,
            expected_score=0.0,
            actual_score=1.0 if match.win_team == 1 else 0.0,
            kill_participation=debug_info["kill_participation"],
            team_kills=debug_info["team_kills"],
            lane_preference_type=debug_info["lane_preference_type"],
        )

    # 팀 2 처리
    for detail in team2_details:
        player = detail.player
        before = player.player_power_score

        final_delta, debug_info = calculate_player_delta(
            detail=detail,
            my_team_details=team2_details,
            opponent_team_details=team1_details,
            did_win=(match.win_team == 2),
        )

        after = max(1, before + final_delta)

        player.player_power_score = after
        player.save(update_fields=["player_power_score"])

        RatingHistory.objects.create(
            player=player,
            match=match,
            revision=1,
            rating_before=before,
            rating_after=after,
            delta_total=final_delta,
            delta_base=debug_info["team_delta"],
            delta_kp=debug_info["score_kp"] * 50.0 * KP_WEIGHT,
            delta_role=0.0,
            expected_score=0.0,
            actual_score=1.0 if match.win_team == 2 else 0.0,
            kill_participation=debug_info["kill_participation"],
            team_kills=debug_info["team_kills"],
            lane_preference_type=debug_info["lane_preference_type"],
        )

    match.is_rating_applied = True
    match.save(update_fields=["is_rating_applied"])