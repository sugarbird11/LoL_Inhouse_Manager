from django import forms
from django.forms import formset_factory, modelformset_factory

from players.models import Player
from .models import Match, MatchPlayerDetail


class PlayerChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.player_id


class MatchUploadForm(forms.Form):
    match_id = forms.CharField(
        label="경기 ID",
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    win_team = forms.ChoiceField(
        label="승리 팀",
        choices=[(1, "팀 1"), (2, "팀 2")],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    screenshot = forms.ImageField(
        label="경기 결과 스크린샷",
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
    )
    temp_screenshot_path = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )


class MatchPlayerDetailForm(forms.Form):
    player = PlayerChoiceField(
        label="플레이어",
        queryset=Player.objects.all().order_by("player_id"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    player_team = forms.ChoiceField(
        label="팀",
        choices=[(1, "팀 1"), (2, "팀 2")],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    player_kda = forms.CharField(
        label="KDA",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "예: 10/2/8"}),
    )
    player_selected_lane = forms.ChoiceField(
        label="선택 라인",
        choices=MatchPlayerDetail.LANE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    player_gold = forms.IntegerField(
        label="골드",
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "예: 14500"}),
    )

    def clean_player_kda(self):
        value = self.cleaned_data.get("player_kda", "").strip()
        if value == "":
            return value

        parts = value.split("/")
        if len(parts) != 3:
            raise forms.ValidationError("KDA는 '킬/데스/어시스트' 형식으로 입력해야 합니다.")

        try:
            k, d, a = map(int, parts)
        except ValueError:
            raise forms.ValidationError("KDA는 숫자만 포함해야 합니다.")

        if k < 0 or d < 0 or a < 0:
            raise forms.ValidationError("KDA 값은 0 이상이어야 합니다.")

        return f"{k}/{d}/{a}"


MatchPlayerDetailFormSet = formset_factory(
    MatchPlayerDetailForm,
    extra=10,
    max_num=10,
    validate_max=True,
)


class MatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ["match_id", "win_team", "screenshot"]
        widgets = {
            "match_id": forms.TextInput(attrs={"class": "form-control"}),
            "win_team": forms.Select(attrs={"class": "form-select"}, choices=[(1, "팀 1"), (2, "팀 2")]),
            "screenshot": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


class MatchPlayerDetailModelForm(forms.ModelForm):
    player = PlayerChoiceField(
        queryset=Player.objects.all().order_by("player_id"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = MatchPlayerDetail
        fields = [
            "player",
            "player_team",
            "player_kda",
            "player_selected_lane",
            "player_gold",
        ]
        widgets = {
            "player_team": forms.Select(attrs={"class": "form-select"}, choices=[(1, "팀 1"), (2, "팀 2")]),
            "player_kda": forms.TextInput(attrs={"class": "form-control", "placeholder": "예: 10/2/8"}),
            "player_selected_lane": forms.Select(attrs={"class": "form-select"}),
            "player_gold": forms.NumberInput(attrs={"class": "form-control"}),
        }


MatchPlayerDetailModelFormSet = modelformset_factory(
    MatchPlayerDetail,
    form=MatchPlayerDetailModelForm,
    extra=0,
)