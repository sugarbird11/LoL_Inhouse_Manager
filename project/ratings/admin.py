from django.contrib import admin
from .models import RatingHistory

@admin.register(RatingHistory)
class RatingHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "player",
        "match",
        "rating_before",
        "rating_after",
        "delta_total",
        "delta_base",
        "delta_kp",
        "delta_role",
        "lane_preference_type",
        "created_at",
    )
    search_fields = ("player__player_id", "match__match_id")
    ordering = ("-created_at",)