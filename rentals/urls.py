from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("reservations/", views.reservation_search, name="reservations"),
    path("reservations/inquiry/", views.create_inquiry, name="create_inquiry"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("complete_pending_inquiry/", views._complete_pending_inquiry, name="_complete_pending_inquiry"),
    path("pull_vrbo_calendar/", views.pull_vrbo_calendar, name="pull_vrbo_calendar"),
    path("operations/", views.operations, name="operations"),
    path("upload_accounting_file/", views.upload_accounting_file, name="upload_accounting_file"),
]

