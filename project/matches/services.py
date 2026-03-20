from __future__ import annotations

import os
import uuid

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
from django.db import transaction

from players.models import Player
from .models import Match, MatchPlayerDetail
from .scoreboard_parser import parse_scoreboard_image
from .name_matcher import match_player_name
from ratings.services import apply_ratings_for_match, rollback_ratings_for_match

def build_initial_details_from_lobby(lobby_state):
    """
    lobbies 세션 상태를 기반으로 match 상세 입력 10개를 초기화한다.
    """
    if not lobby_state:
        return []

    selected_player_ids = lobby_state.get("selected_player_ids", [])
    team1_ids = lobby_state.get("team1_ids", [])
    team2_ids = lobby_state.get("team2_ids", [])
    position_map = lobby_state.get("position_map", {})

    if len(selected_player_ids) != 10:
        return []

    players = Player.objects.filter(key__in=selected_player_ids)
    player_map = {player.key: player for player in players}

    initial_rows = []

    for player_id in team1_ids:
        if player_id in player_map:
            initial_rows.append(
                {
                    "player": player_map[player_id],
                    "player_team": 1,
                    "player_kda": "",
                    "player_selected_lane": position_map.get(str(player_id), player_map[player_id].player_main_position),
                    "player_gold": "",
                }
            )

    for player_id in team2_ids:
        if player_id in player_map:
            initial_rows.append(
                {
                    "player": player_map[player_id],
                    "player_team": 2,
                    "player_kda": "",
                    "player_selected_lane": position_map.get(str(player_id), player_map[player_id].player_main_position),
                    "player_gold": "",
                }
            )

    return initial_rows[:10]

def save_temp_uploaded_file(uploaded_file):
    """
    OCR용 임시 업로드 파일 저장
    """
    ext = os.path.splitext(uploaded_file.name)[1]
    temp_name = f"match_temp/{uuid.uuid4().hex}{ext}"
    saved_path = default_storage.save(temp_name, uploaded_file)
    return saved_path

def auto_fill_match_result_from_image(image_path: str, initial_details: list[dict]):
    """
    스크린샷에서 OCR 결과를 파싱하고,
    로비에서 넘어온 10명 정보(initial_details)에 매칭해서 자동 채움 결과를 만든다.
    """
    parsed_rows = parse_scoreboard_image(image_path)

    player_candidates = [
        row["player"].player_id if hasattr(row["player"], "player_id") else str(row["player"])
        for row in initial_details
    ]

    candidate_map = {
        row["player"].player_id if hasattr(row["player"], "player_id") else str(row["player"]): row
        for row in initial_details
    }

    used_names = set()
    output_rows = []

    for parsed in parsed_rows:
        matched_name = match_player_name(parsed["ocr_name"], player_candidates)

        # 이미 매칭된 이름이면 팀/행 순서 fallback
        if matched_name in used_names:
            matched_name = None

        if matched_name is not None:
            base_row = dict(candidate_map[matched_name])
            used_names.add(matched_name)
        else:
            # fallback: 팀과 row 순서를 활용
            team_rows = [row for row in initial_details if int(row["player_team"]) == int(parsed["team"])]
            fallback_idx = parsed["row_index"]
            if fallback_idx < len(team_rows):
                base_row = dict(team_rows[fallback_idx])
            else:
                base_row = dict(initial_details[len(output_rows)])

        if parsed["player_kda"]:
            base_row["player_kda"] = parsed["player_kda"]

        if parsed["player_gold"] is not None:
            base_row["player_gold"] = parsed["player_gold"]

        # OCR은 팀 정보도 row 위치 기준으로 갖고 있으므로 덮어씀
        base_row["player_team"] = parsed["team"]

        output_rows.append(base_row)

    return output_rows[:10]

def save_match_with_details(match_form, detail_forms, temp_screenshot_path=None):
    """
    경기 정보와 플레이어 상세 10명을 저장하고,
    Player의 승/패 기록도 갱신한다.
    """
    screenshot_file = match_form.cleaned_data.get("screenshot")

    match = Match.objects.create(
        match_id=match_form.cleaned_data["match_id"],
        win_team=int(match_form.cleaned_data["win_team"]),
    )

    if screenshot_file:
        match.screenshot = screenshot_file
        match.save()
    elif temp_screenshot_path:
        absolute_path = os.path.join(settings.MEDIA_ROOT, temp_screenshot_path)
        if os.path.exists(absolute_path):
            with open(absolute_path, "rb") as fp:
                match.screenshot.save(os.path.basename(temp_screenshot_path), File(fp), save=True)

    used_player_ids = set()

    for form in detail_forms:
        player = form.cleaned_data["player"]
        player_team = int(form.cleaned_data["player_team"])
        player_kda = form.cleaned_data.get("player_kda", "")
        player_selected_lane = form.cleaned_data["player_selected_lane"]
        player_gold = form.cleaned_data.get("player_gold") or 0

        if player.key in used_player_ids:
            raise ValueError(f"{player.player_id} 플레이어가 중복 입력되었습니다.")

        used_player_ids.add(player.key)

        MatchPlayerDetail.objects.create(
            match=match,
            player=player,
            player_team=player_team,
            player_kda=player_kda,
            player_selected_lane=player_selected_lane,
            player_gold=player_gold,
        )

        if player_team == match.win_team:
            player.player_win += 1
        else:
            player.player_lose += 1

        player.save()

    from ratings.services import apply_ratings_for_match
    apply_ratings_for_match(match)

    return match

@transaction.atomic
def rollback_match_result(match):
    """
    경기 삭제/수정 전에:
    1. 승패 집계 롤백
    2. PS 롤백
    """
    details = list(match.player_details.select_related("player").all())

    rollback_ratings_for_match(match)

    for detail in details:
        player = detail.player

        if detail.player_team == match.win_team:
            if player.player_win > 0:
                player.player_win -= 1
        else:
            if player.player_lose > 0:
                player.player_lose -= 1

        player.save(update_fields=["player_win", "player_lose"])

@transaction.atomic
def update_match_and_reapply(match, match_form, formset):
    """
    경기 결과 수정:
    1. 기존 반영 롤백
    2. Match 수정
    3. MatchPlayerDetail 수정
    4. 승패 다시 반영
    5. PS 다시 반영
    """
    rollback_match_result(match)

    old_details = list(match.player_details.all())
    for old_detail in old_details:
        old_detail.delete()

    updated_match = match_form.save()

    new_details = formset.save(commit=False)
    for obj in new_details:
        obj.match = updated_match
        obj.save()

    for detail in updated_match.player_details.select_related("player").all():
        player = detail.player

        if detail.player_team == updated_match.win_team:
            player.player_win += 1
        else:
            player.player_lose += 1

        player.save()

    apply_ratings_for_match(updated_match)

    return updated_match