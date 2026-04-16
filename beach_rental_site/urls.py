from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Include the rentals app’s URLs without a namespace so names like "home"
    # are available directly to templates using `{% url 'home' %}`.
    path("", include("rentals.urls")),
    path("users/", include("users.urls")),
]



