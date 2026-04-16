from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect
from rentals.views import _complete_pending_inquiry
from users.forms import UserRegistrationForm
from django.db import IntegrityError

PENDING_INQUIRY_SESSION_KEY = "pending_inquiry"


# Create your views here.
def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        if _complete_pending_inquiry(request):
            messages.success(
                request,
                "Your discounted price inquiry has been recorded. We'll follow up with details.",
            )
            return redirect("reservations")
        return redirect("dashboard")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if _complete_pending_inquiry(request):
                    messages.success(
                        request,
                        "You are now logged in, and your discounted price inquiry was submitted.",
                    )
                    return redirect("reservations")
                messages.success(request, "You are now logged in.")
                return redirect("dashboard")
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, "users/login.html", {"form": form})

def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")

def register_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        if _complete_pending_inquiry(request):
            messages.success(
                request,
                "Your discounted price inquiry has been recorded. We'll follow up with details.",
            )
            return redirect("reservations")
        return redirect("dashboard")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
            except IntegrityError as e:
                if "Duplicate entry" in str(e.args[1]):
                    messages.error(request, "Email or phone number already in use.")
                    return redirect("register") 
                else:
                    messages.error(request, f"Error creating account: {e}, please contact support.")
                    return redirect("register")
            login(request, user)
            if _complete_pending_inquiry(request):
                messages.success(
                    request,
                    "Account created. Your discounted price inquiry has been recorded.",
                )
                return redirect("reservations")
            messages.success(request, "Your account has been created. Welcome!")
            return redirect("dashboard")
    else:
        form = UserRegistrationForm()

    return render(request, "users/register.html", {"form": form})
