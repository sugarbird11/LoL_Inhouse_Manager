from django.contrib import admin
from .models import Player


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = (
        "key",
        "player_id",
        "player_power_score",
        "player_main_position",
        "player_secondary_position",
        "player_win",
        "player_lose",
        "created_at",
    )
    search_fields = ("player_id",)
    list_filter = ("player_main_position", "player_secondary_position")
    ordering = ("player_id",)