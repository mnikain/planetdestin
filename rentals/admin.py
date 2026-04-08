from django.contrib import admin

from .models import User, Customer, Reservation, Units

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "phone", "is_active", "created_at", "updated_at")
    ordering = ("-created_at",)

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "user", "address", "city", "state", "zipcode", "country", "created_at", "updated_at")
    ordering = ("-created_at",)

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("customer", "check_in", "check_out", "guests", "unit", "status", "created_at", "updated_at")
    list_filter = ("status",)
    ordering = ("-created_at",)

@admin.register(Units)
class UnitsAdmin(admin.ModelAdmin):
    list_display = ("unit", "vendor", "url", "updated_at", "notes")
    ordering = ("-updated_at",)