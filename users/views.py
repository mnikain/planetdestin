from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect
from users.forms import UserRegistrationForm
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import send_mail
import secrets
import string
from datetime import timezone, timedelta, datetime

PENDING_INQUIRY_SESSION_KEY = "pending_inquiry"


def _build_temp_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _send_temporary_password(email: str, temp_password: str) -> None:
    send_mail(
        "Your temporary password",
        (
            "A temporary password was requested for your account.\n\n"
            f"Temporary password: {temp_password}\n\n"
            "Please log in and change your password right away."
        ),
        settings.EMAIL_HOST_USER,
        #[email],   #putting this back in will send the email to the user, but we don't want to spam them
        [settings.EMAIL_HOST_USER],
        fail_silently=False,
    )


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
    if request.method == "POST" and request.POST.get("action") == "send_temp_password":
        email = (request.POST.get("email") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        user_model = get_user_model()
        existing_user = None
        if email:
            existing_user = user_model.objects.filter(email__iexact=email).first()
        if existing_user is None and phone:
            existing_user = user_model.objects.filter(phone=phone).first()

        if existing_user and existing_user.email:
            if existing_user.last_reset_email and existing_user.last_reset_email < datetime.now() - timedelta(days=1):   
                existing_user.reset_emails = 0
                existing_user.last_reset_email = None
                existing_user.save(update_fields=["reset_emails", "last_reset_email"])
            
            if  existing_user.reset_emails > 3 and existing_user.last_reset_email > datetime.now() - timedelta(days=1):
                messages.error(request, "You have reached the maximum number of temporary password resets. Please contact support.")
                return redirect("users:register")

            if existing_user.last_reset_email and existing_user.last_reset_email > datetime.now() - timedelta(minutes=30):
                messages.error(request, "We don't want to spam anyone, so please wait 30 minutes before requesting another temporary password.")
                return redirect("users:register")

            temp_password = _build_temp_password()
            existing_user.set_password(temp_password)
            existing_user.reset_emails += 1
            existing_user.last_reset_email = datetime.now()
            existing_user.save(update_fields=["password", "reset_emails", "last_reset_email"])
            _send_temporary_password(existing_user.email, temp_password)
            messages.success(
                request,
                "Temporary passowrd sent to email.",
            )
            return redirect("users:login")

        messages.error(
            request,
            "We could not send a temporary password for that account. Please contact support.",
        )
        form = UserRegistrationForm(initial={"email": email, "phone": phone})
        return render(
            request,
            "users/register.html",
            {
                "form": form,
                "show_temp_password_option": True,
                "existing_email": email,
                "existing_phone": phone,
            },
        )

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        email = (request.POST.get("email") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        if form.is_valid():
            try:
                user = form.save()
            except IntegrityError as e:
                    messages.error(request, f"Error creating account: {e}, please contact support.")
                    return redirect("users:register")
            login(request, user)
            messages.success(request, "Your account has been created. Welcome!")
            next = request.GET.get("next", "dashboard")
            return redirect(next)
        else:
            # Model uniqueness can fail before save(); still offer temp-password recovery.
            user_model = get_user_model()
            email_exists = bool(email) and user_model.objects.filter(email__iexact=email).exists()
            phone_exists = bool(phone) and user_model.objects.filter(phone=phone).exists()
            if email_exists or phone_exists:
                messages.error(
                    request,
                    "Email and/or phone number is already registered",
                )
                return render(
                    request,
                    "users/register.html",
                    {
                        "form": form,
                        "show_temp_password_option": True,
                        "existing_email": email,
                        "existing_phone": phone,
                    },
                )
    else:
        form = UserRegistrationForm()

    return render(request, "users/register.html", {"form": form})
