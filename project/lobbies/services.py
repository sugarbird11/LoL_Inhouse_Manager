from itertools import combinations, permutations


POSITIONS = ["TOP", "JGL", "MID", "ADC", "SUP"]


def get_effective_power_score(player, assigned_position):
    """
    assigned_position 기준 실효 파워 스코어 계산
    - 주포지션: 그대로
    - 부포지션: -5%
    - 그 외: -10%
    """
    base_score = player["score"]
    main_position = player["main_pos"]
    secondary_position = player["sub_pos"]

    if assigned_position == main_position:
        return base_score

    if assigned_position == secondary_position:
        return round(base_score * 0.95)

    return round(base_score * 0.90)


def calculate_team_score(team_players, assigned_positions):
    """
    team_players: [{id, name, score, main_pos, sub_pos}, ...] (길이 5)
    assigned_positions: ["TOP", "JGL", "MID", "ADC", "SUP"] (길이 5)
    """
    total = 0

    for player, position in zip(team_players, assigned_positions):
        total += get_effective_power_score(player, position)

    return total


def find_best_position_assignment(team_players):
    """
    주어진 5명 팀에 대해 가능한 모든 포지션 배치를 시도하고,
    팀 PS가 최대가 되는 배치를 반환한다.
    """
    best_score = None
    best_position_map = None

    for positions in permutations(POSITIONS):
        score = calculate_team_score(team_players, positions)

        if best_score is None or score > best_score:
            best_score = score
            best_position_map = {
                str(player["id"]): position
                for player, position in zip(team_players, positions)
            }

    return best_score, best_position_map


def auto_assign_teams(players, current_team1_ids, current_team2_ids, locked_player_ids):
    """
    규칙
    1. 먼저 5:5 팀 분할을 만든다.
    2. 각 팀 내부에서 포지션 배치를 최적화하여 최고 PS를 구한다.
    3. 양 팀 최고 PS 차이를 계산한다.
    4. 모든 5:5 경우에 대해 반복하여 최적 조합을 선택한다.
    5. 잠금된 인원은 현재 팀에 고정하고, 나머지만 자동 배정한다.
    6. 차이가 같으면 전체 PS 총합이 더 큰 경우를 선택한다.
    """
    player_map = {player["id"]: player for player in players}

    current_team1_ids = [player_id for player_id in current_team1_ids if player_id in player_map]
    current_team2_ids = [player_id for player_id in current_team2_ids if player_id in player_map]
    locked_player_ids = [player_id for player_id in locked_player_ids if player_id in player_map]

    current_team1_set = set(current_team1_ids)
    current_team2_set = set(current_team2_ids)

    locked_team1_ids = [player_id for player_id in locked_player_ids if player_id in current_team1_set]
    locked_team2_ids = [player_id for player_id in locked_player_ids if player_id in current_team2_set]

    locked_team1_ids = list(dict.fromkeys(locked_team1_ids))
    locked_team2_ids = list(dict.fromkeys(locked_team2_ids))

    if len(locked_team1_ids) > 5 or len(locked_team2_ids) > 5:
        raise ValueError("한 팀에 잠금된 인원이 5명을 초과할 수 없습니다.")

    locked_all_set = set(locked_team1_ids + locked_team2_ids)
    unlocked_players = [player for player in players if player["id"] not in locked_all_set]

    team1_needed = 5 - len(locked_team1_ids)
    team2_needed = 5 - len(locked_team2_ids)

    if team1_needed < 0 or team2_needed < 0:
        raise ValueError("잠금 상태가 잘못되었습니다.")

    if team1_needed + team2_needed != len(unlocked_players):
        raise ValueError("잠금된 인원 수와 선택된 인원 수가 맞지 않습니다.")

    best_result = None
    best_diff = None
    best_total = None

    for team1_unlocked_combo in combinations(unlocked_players, team1_needed):
        team1_unlocked_ids = [player["id"] for player in team1_unlocked_combo]
        team2_unlocked_ids = [
            player["id"] for player in unlocked_players
            if player["id"] not in team1_unlocked_ids
        ]

        final_team1_ids = locked_team1_ids + team1_unlocked_ids
        final_team2_ids = locked_team2_ids + team2_unlocked_ids

        final_team1_players = [player_map[player_id] for player_id in final_team1_ids]
        final_team2_players = [player_map[player_id] for player_id in final_team2_ids]

        # 각 팀에서 가장 PS가 높은 포지션 배치를 찾는다.
        team1_score, team1_position_map = find_best_position_assignment(final_team1_players)
        team2_score, team2_position_map = find_best_position_assignment(final_team2_players)

        diff = abs(team1_score - team2_score)
        total = team1_score + team2_score

        if (
            best_result is None
            or diff < best_diff
            or (diff == best_diff and total > best_total)
        ):
            best_result = {
                "team1_ids": final_team1_ids,
                "team2_ids": final_team2_ids,
                "team1_score": team1_score,
                "team2_score": team2_score,
                "score_diff": diff,
                "position_map": {
                    **team1_position_map,
                    **team2_position_map,
                },
            }
            best_diff = diff
            best_total = total

    if best_result is None:
        raise ValueError("자동 팀 배정 결과를 생성하지 못했습니다.")

    return best_result