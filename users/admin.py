from django.contrib import admin
from users.models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "phone", "first_name", "last_name", "is_active", "is_staff", "is_superuser", "date_joined")
    list_filter = ("is_active", "is_staff", "is_superuser")
    ordering = ("-date_joined",)
    search_fields = ("email", "phone", "first_name", "last_name")
    list_per_page = 10
    list_max_show_all = 100
    list_editable = ("is_active", "is_staff", "is_superuser")
    list_display_links = ("email", "phone", "first_name", "last_name")
