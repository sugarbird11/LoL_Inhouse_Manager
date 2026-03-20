from django.urls import path
from . import views

app_name = "lobbies"

urlpatterns = [
    path("", views.lobby_view, name="lobby"),
]