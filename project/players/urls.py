from django.urls import path
from .views import (
    PlayerListView,
    PlayerDetailView,
    PlayerCreateView,
    PlayerUpdateView,
    PlayerDeleteView,
)

app_name = "players"

urlpatterns = [
    path("", PlayerListView.as_view(), name="player_list"),
    path("create/", PlayerCreateView.as_view(), name="player_create"),
    path("<int:pk>/", PlayerDetailView.as_view(), name="player_detail"),
    path("<int:pk>/update/", PlayerUpdateView.as_view(), name="player_update"),
    path("<int:pk>/delete/", PlayerDeleteView.as_view(), name="player_delete"),
]