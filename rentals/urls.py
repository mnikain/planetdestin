from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("reservations/", views.reservation_search, name="reservations"),
    path("reservations/inquiry/", views.create_inquiry, name="create_inquiry"),
    path("register/", views.register_view, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("pull_vrbo_calendar/", views.pull_vrbo_calendar, name="pull_vrbo_calendar"),
]

