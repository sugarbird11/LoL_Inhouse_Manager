from django.urls import path
from . import views

app_name = "matches"

urlpatterns = [
    path("", views.match_list_view, name="match_list"),
    path("upload/", views.match_upload_view, name="match_upload"),
    path("<int:pk>/", views.match_detail_view, name="match_detail"),
    path("<int:pk>/delete/", views.match_delete_view, name="match_delete"),
]