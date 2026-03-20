from django import forms
from players.models import Player


class LobbySetupForm(forms.Form):
    players = forms.ModelMultipleChoiceField(
        queryset=Player.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="참가자 선택",
    )

    def clean_players(self):
        players = self.cleaned_data["players"]
        if len(players) != 10:
            raise forms.ValidationError("참가자는 반드시 10명을 선택해야 합니다.")
        return players