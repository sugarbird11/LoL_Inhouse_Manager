from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .models import Player
from .forms import PlayerForm


class PlayerListView(ListView):
    model = Player
    template_name = "players/players_list.html"
    context_object_name = "players"

    VALID_SORT_FIELDS = {"player_id", "player_power_score"}
    VALID_SORT_DIRECTIONS = {"asc", "desc"}

    def get_queryset(self):
        sort_by = self.request.GET.get("sort_by", "player_id")
        direction = self.request.GET.get("direction", "asc")

        if sort_by not in self.VALID_SORT_FIELDS:
            sort_by = "player_id"

        if direction not in self.VALID_SORT_DIRECTIONS:
            direction = "asc"

        order_by = sort_by if direction == "asc" else f"-{sort_by}"

        # 동일 값일 때 정렬이 흔들리지 않도록 보조 정렬 추가
        if sort_by == "player_id":
            return Player.objects.all().order_by(order_by, "key")
        return Player.objects.all().order_by(order_by, "player_id", "key")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_sort_by = self.request.GET.get("sort_by", "player_id")
        current_direction = self.request.GET.get("direction", "asc")

        if current_sort_by not in self.VALID_SORT_FIELDS:
            current_sort_by = "player_id"

        if current_direction not in self.VALID_SORT_DIRECTIONS:
            current_direction = "asc"

        def next_direction_for(column_name):
            """
            현재 정렬 기준 열을 다시 누르면 방향 토글,
            다른 열로 바꾸면 기본 방향 부여
            - 소환사명: 기본 asc
            - 파워 스코어: 기본 desc
            """
            if current_sort_by == column_name:
                return "desc" if current_direction == "asc" else "asc"

            if column_name == "player_power_score":
                return "desc"

            return "asc"

        context["current_sort_by"] = current_sort_by
        context["current_direction"] = current_direction
        context["next_name_direction"] = next_direction_for("player_id")
        context["next_ps_direction"] = next_direction_for("player_power_score")

        return context


class PlayerDetailView(DetailView):
    model = Player
    template_name = "players/players_detail.html"
    context_object_name = "player"


class PlayerCreateView(CreateView):
    model = Player
    form_class = PlayerForm
    template_name = "players/players_form.html"


class PlayerUpdateView(UpdateView):
    model = Player
    form_class = PlayerForm
    template_name = "players/players_form.html"


class PlayerDeleteView(DeleteView):
    model = Player
    template_name = "players/players_confirm_delete.html"
    success_url = reverse_lazy("players:player_list")
