from django.db import models
from players.models import Player


class RatingHistory(models.Model):
    LANE_PREF_CHOICES = [
        ("MAIN", "주포지션"),
        ("SECONDARY", "부포지션"),
        ("OFFROLE", "비선호 포지션"),
    ]

    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name="rating_histories",
        verbose_name="플레이어",
    )
    match = models.ForeignKey(
        "matches.Match",
        on_delete=models.CASCADE,
        related_name="rating_histories",
        verbose_name="경기",
    )

    # 경기 수정 이력 추적용
    revision = models.PositiveIntegerField(default=1, verbose_name="경기 반영 리비전")

    rating_before = models.IntegerField(verbose_name="반영 전 PS")
    rating_after = models.IntegerField(verbose_name="반영 후 PS")

    delta_total = models.IntegerField(verbose_name="총 변화량")
    delta_base = models.FloatField(verbose_name="승패 기반 변화량")
    delta_kp = models.FloatField(verbose_name="킬관여율 보정")
    delta_role = models.FloatField(verbose_name="포지션 보정")

    expected_score = models.FloatField(verbose_name="기대 승률")
    actual_score = models.FloatField(verbose_name="실제 결과")

    kill_participation = models.FloatField(verbose_name="킬관여율")
    team_kills = models.PositiveIntegerField(verbose_name="팀 총 킬")

    lane_preference_type = models.CharField(
        max_length=20,
        choices=LANE_PREF_CHOICES,
        verbose_name="포지션 선호도 유형",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "레이팅 이력"
        verbose_name_plural = "레이팅 이력 목록"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.player.player_id} / {self.match.match_id} / {self.delta_total:+d}"