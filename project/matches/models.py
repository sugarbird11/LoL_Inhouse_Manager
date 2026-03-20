from django.db import models
from players.models import Player


class Match(models.Model):
    match_id = models.CharField(max_length=50, unique=True, verbose_name="경기 ID")
    win_team = models.IntegerField(verbose_name="승리 팀")
    screenshot = models.ImageField(
        upload_to="match_screenshots/",
        blank=True,
        null=True,
        verbose_name="경기 결과 스크린샷",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    is_rating_applied = models.BooleanField(default=False, verbose_name="레이팅 반영 여부")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.match_id} (승리 팀: {self.win_team})"


class MatchPlayerDetail(models.Model):
    LANE_CHOICES = [
        ("TOP", "탑"),
        ("JGL", "정글"),
        ("MID", "미드"),
        ("ADC", "원딜"),
        ("SUP", "서폿"),
    ]

    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name="player_details",
    )
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name="match_details",
    )
    player_team = models.IntegerField()
    player_kda = models.CharField(max_length=20)
    player_selected_lane = models.CharField(max_length=3, choices=LANE_CHOICES)
    player_gold = models.IntegerField()

    def __str__(self):
        return f"{self.match.match_id} - {self.player.player_id}"