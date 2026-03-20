from django.shortcuts import render
from players.models import Player
from .models import RatingHistory


def rating_list_view(request):
    players = Player.objects.all().order_by("-player_power_score")

    return render(
        request,
        "ratings/rating_list.html",
        {
            "players": players,
        },
    )


def rating_history_view(request):
    histories = RatingHistory.objects.select_related("player", "match").order_by("-created_at")[:200]

    return render(
        request,
        "ratings/rating_history.html",
        {
            "histories": histories,
        },
    )