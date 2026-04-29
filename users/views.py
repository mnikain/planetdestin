from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect
from users.forms import UserRegistrationForm
from django.db import IntegrityError
from django.contrib.auth import get_user_model

PENDING_INQUIRY_SESSION_KEY = "pending_inquiry"


def test_view(request: HttpRequest) -> HttpResponse:
    user = get_user_model().objects.all()
    user_list = []
    
    for user in user:
        user_list.append(user)
    return HttpResponse("Users: " + str(user_list))    


# Create your views here.
def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        next = request.GET.get("next", "dashboard")
        return redirect(next)

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                next = request.GET.get("next", "dashboard")
                return redirect(next)
            else:
                messages.error(request, "Invalid username or password.")
                return redirect("users:login")
        else:
            messages.error(request, "Invalid username or password.")
            return redirect("users:login")
    else:
        next = request.GET.get("next", "dashboard")
        form = AuthenticationForm()

    return render(request, "users/login.html", {"form": form, "next": next})

def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")

def register_view(request: HttpRequest) -> HttpResponse:
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
            messages.success(request, "Your account has been created. Welcome!")
            next = request.GET.get("next", "dashboard")
            return redirect(next)
    else:
        form = UserRegistrationForm()

    return render(request, "users/register.html", {"form": form})
