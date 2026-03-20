import json

from django.contrib import messages
from django.shortcuts import redirect, render

from players.models import Player
from .services import auto_assign_teams


POSITION_CHOICES = [
    ("TOP", "탑"),
    ("JGL", "정글"),
    ("MID", "미드"),
    ("ADC", "원딜"),
    ("SUP", "서폿"),
]

POSITION_ORDER = {
    "TOP": 0,
    "JGL": 1,
    "MID": 2,
    "ADC": 3,
    "SUP": 4,
}

def _to_int_list(values):
    result = []
    for value in values:
        try:
            result.append(int(value))
        except (TypeError, ValueError):
            continue
    return result


def _safe_json_load(text, default):
    if not text:
        return default
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return default


def _get_lobby_state(request):
    return request.session.get(
        "lobby_state",
        {
            "selected_player_ids": [],
            "team1_ids": [],
            "team2_ids": [],
            "locked_player_ids": [],
            "position_map": {},
        },
    )


def _save_lobby_state(request, state):
    request.session["lobby_state"] = state
    request.session.modified = True


def _player_to_dict(player):
    return {
        "id": player.key,
        "name": player.player_id,
        "score": player.player_power_score,
        "main_pos": player.player_main_position,
        "sub_pos": player.player_secondary_position,
    }


def _build_player_cards(players, position_map, locked_ids):
    cards = []
    locked_set = set(locked_ids)

    for player in players:
        selected_position = position_map.get(str(player.key), player.player_main_position)

        cards.append(
            {
                "id": player.key,
                "name": player.player_id,
                "score": player.player_power_score,
                "main_position": player.player_main_position,
                "secondary_position": player.player_secondary_position,
                "selected_position": selected_position,
                "is_locked": player.key in locked_set,
            }
        )

    cards.sort(key=lambda card: POSITION_ORDER.get(card["selected_position"], 99))
    return cards


def _get_effective_score(player, assigned_position):
    if assigned_position == player.player_main_position:
        return player.player_power_score
    if assigned_position == player.player_secondary_position:
        return round(player.player_power_score * 0.95)
    return round(player.player_power_score * 0.90)


def _calculate_effective_team_score(team_players, position_map):
    total = 0
    for player in team_players:
        assigned_position = position_map.get(str(player.key), player.player_main_position)
        total += _get_effective_score(player, assigned_position)
    return total


def lobby_view(request):
    all_players = list(Player.objects.all().order_by("player_id"))
    state = _get_lobby_state(request)

    if request.method == "POST":
        action = request.POST.get("action")

        selected_ids = _to_int_list(request.POST.getlist("selected_players"))
        team1_ids = _to_int_list(_safe_json_load(request.POST.get("team1_ids_json"), []))
        team2_ids = _to_int_list(_safe_json_load(request.POST.get("team2_ids_json"), []))
        locked_ids = _to_int_list(request.POST.getlist("locked_players"))

        # save_layout 용
        posted_position_map = _safe_json_load(request.POST.get("position_map_json"), {})
        posted_position_map = {str(k): v for k, v in posted_position_map.items()}

        if action == "update_selection":
            if len(selected_ids) != 10:
                messages.error(request, "참가자는 정확히 10명을 선택해야 합니다.")
            else:
                state["selected_player_ids"] = selected_ids
                state["team1_ids"] = []
                state["team2_ids"] = []
                state["locked_player_ids"] = []
                state["position_map"] = {}
                _save_lobby_state(request, state)
                messages.success(request, "참가자 10명이 등록되었습니다.")

            return redirect("lobbies:lobby")

        if action == "save_layout":
            state["selected_player_ids"] = selected_ids
            state["team1_ids"] = team1_ids
            state["team2_ids"] = team2_ids
            state["locked_player_ids"] = locked_ids
            state["position_map"] = posted_position_map
            _save_lobby_state(request, state)
            messages.success(request, "현재 팀 배치와 잠금/포지션 설정을 저장했습니다.")
            return redirect("lobbies:lobby")

        if action == "auto_assign":
            if len(selected_ids) != 10:
                messages.error(request, "자동 팀 배정을 하려면 참가자 10명이 먼저 선택되어야 합니다.")
                return redirect("lobbies:lobby")

            state["selected_player_ids"] = selected_ids
            state["locked_player_ids"] = locked_ids

            # 처음 자동배정이면 현재 선택 순서대로 임시 5:5 분할
            if not team1_ids and not team2_ids:
                team1_ids = selected_ids[:5]
                team2_ids = selected_ids[5:10]

            selected_players = Player.objects.filter(key__in=selected_ids)
            player_dicts = [_player_to_dict(player) for player in selected_players]

            try:
                result = auto_assign_teams(
                    players=player_dicts,
                    current_team1_ids=team1_ids,
                    current_team2_ids=team2_ids,
                    locked_player_ids=locked_ids,
                )
            except ValueError as error:
                messages.error(request, str(error))
                return redirect("lobbies:lobby")

            state["team1_ids"] = result["team1_ids"]
            state["team2_ids"] = result["team2_ids"]
            state["position_map"] = result["position_map"]

            _save_lobby_state(request, state)

            messages.success(
                request,
                f"자동 팀 배정을 완료했습니다. 팀1 PS: {result['team1_score']}, 팀2 PS: {result['team2_score']}, 차이: {result['score_diff']}",
            )
            return redirect("lobbies:lobby")

    selected_ids = state.get("selected_player_ids", [])
    team1_ids = state.get("team1_ids", [])
    team2_ids = state.get("team2_ids", [])
    locked_ids = state.get("locked_player_ids", [])
    position_map = state.get("position_map", {})

    player_map = {player.key: player for player in all_players}
    selected_players = [player_map[player_id] for player_id in selected_ids if player_id in player_map]
    team1_players = [player_map[player_id] for player_id in team1_ids if player_id in player_map]
    team2_players = [player_map[player_id] for player_id in team2_ids if player_id in player_map]

    selected_set = set(selected_ids)
    available_players = [player for player in all_players if player.key not in selected_set]

    context = {
        "available_players": available_players,
        "selected_players": selected_players,
        "selected_player_ids": selected_ids,
        "team1_cards": _build_player_cards(team1_players, position_map, locked_ids),
        "team2_cards": _build_player_cards(team2_players, position_map, locked_ids),
        "team1_score_total": _calculate_effective_team_score(team1_players, position_map),
        "team2_score_total": _calculate_effective_team_score(team2_players, position_map),
        "position_choices": POSITION_CHOICES,
        "locked_player_ids": locked_ids,
    }
    return render(request, "lobbies/lobby.html", context)