from django.urls import path
from . import views

app_name = "ratings"

urlpatterns = [
    path("", views.rating_list_view, name="rating_list"),
    path("history/", views.rating_history_view, name="rating_history"),
]