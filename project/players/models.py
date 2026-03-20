from django.db import models
from django.urls import reverse


class Player(models.Model):
    POSITION_CHOICES = [
        ("TOP", "탑"),
        ("JGL", "정글"),
        ("MID", "미드"),
        ("ADC", "원딜"),
        ("SUP", "서폿"),
    ]

    key = models.AutoField(primary_key=True)
    player_id = models.CharField(max_length=30, unique=True, verbose_name="소환사명")
    player_power_score = models.IntegerField(default=1000, verbose_name="파워 스코어")
    player_main_position = models.CharField(max_length=3, choices=POSITION_CHOICES, verbose_name="주 포지션")
    player_secondary_position = models.CharField(max_length=3, choices=POSITION_CHOICES, verbose_name="부 포지션")
    player_win = models.IntegerField(default=0, verbose_name="승")
    player_lose = models.IntegerField(default=0, verbose_name="패")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["player_id"]
        verbose_name = "플레이어"
        verbose_name_plural = "플레이어 목록"

    def __str__(self):
        return f"{self.player_id} ({self.player_power_score})"

    def get_absolute_url(self):
        return reverse("players:player_detail", kwargs={"pk": self.pk})
    
    @property
    def total_games(self):
        return self.player_win + self.player_lose
    
    @property
    def win_rate(self):
        total = self.total_games
        if total == 0:
            return 0
        return round((self.player_win / total * 100), 2)