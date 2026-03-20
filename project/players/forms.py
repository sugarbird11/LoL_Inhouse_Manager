from django import forms
from .models import Player


class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = [
            "player_id",
            "player_power_score",
            "player_main_position",
            "player_secondary_position",
        ]
        labels = {
            "player_id": "소환사명",
            "player_power_score": "파워 스코어",
            "player_main_position": "주 포지션",
            "player_secondary_position": "부 포지션",
        }
        widgets = {
            "player_id": forms.TextInput(attrs={"class": "form-control", "placeholder": "소환사명을 입력하세요"}),
            "player_power_score": forms.NumberInput(attrs={"class": "form-control", "placeholder": "예: 1000"}),
            "player_main_position": forms.Select(attrs={"class": "form-select"}),
            "player_secondary_position": forms.Select(attrs={"class": "form-select"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        main_pos = cleaned_data.get("player_main_position")
        secondary_pos = cleaned_data.get("player_secondary_position")

        if main_pos and secondary_pos and main_pos == secondary_pos:
            raise forms.ValidationError("주 포지션과 부 포지션은 서로 달라야 합니다.")

        return cleaned_data