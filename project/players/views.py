from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .models import Player
from .forms import PlayerForm


class PlayerListView(ListView):
    model = Player
    template_name = "players/players_list.html"
    context_object_name = "players"


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