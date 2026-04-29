from django.contrib import admin

from .models import Reservation, Units, Codes
from .views import pull_vrbo_calendar as pull_vrbo_calendar_view
from django.contrib.auth import get_user_model


User = get_user_model()

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("customer__first_name", "customer__last_name", "check_in", "check_out", "guests", "unit", "status", "created_at", "updated_at")
    list_filter = ("status",)
    ordering = ("-created_at",)
    actions = ["pull_vrbo_calendar_action"]

    @admin.action(description="Pull VRBO calendar")
    def pull_vrbo_calendar_action(self, request, queryset):
        # Sync is global; selected rows are ignored.
        pull_vrbo_calendar_view(request)
        self.message_user(request, "VRBO calendar pull started and reservation availability refreshed.")

@admin.register(Units)
class UnitsAdmin(admin.ModelAdmin):
    list_display = ("unit", "vendor", "url", "updated_at", "notes")
    ordering = ("-updated_at",)

@admin.register(Codes)
class CodesAdmin(admin.ModelAdmin):
    list_display = ("unit", "ctype", "value", "activation_date", "expiration_date", "created_at")
    list_filter = ("ctype",)
    ordering = ("-created_at",)
    search_fields = ("unit__unit", "ctype", "value")
    list_per_page = 10
    list_max_show_all = 100
    list_editable = ("activation_date", "expiration_date")
    list_display_links = ("unit", "ctype", "value")
    list_select_related = ("unit",)
    list_prefetch_related = ("unit",)
    list_filter = ("ctype",)
    ordering = ("-created_at",)