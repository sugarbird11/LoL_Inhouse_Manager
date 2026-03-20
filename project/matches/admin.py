from django.contrib import admin
from .models import Match, MatchPlayerDetail


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("match_id", "win_team", "created_at")
    search_fields = ("match_id",)
    ordering = ("-created_at",)


@admin.register(MatchPlayerDetail)
class MatchPlayerDetailAdmin(admin.ModelAdmin):
    list_display = (
        "match",
        "player",
        "player_team",
        "player_kda",
        "player_selected_lane",
        "player_gold",
    )
    list_filter = ("player_team", "player_selected_lane")