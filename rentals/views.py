from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from datetime import datetime

from .forms import RenterRegistrationForm, ReservationSearchForm
from .models import Reservation, Units
import requests
from icalendar import Calendar
from django.db import IntegrityError

PENDING_INQUIRY_SESSION_KEY = "pending_inquiry"


def _build_inquiry_payload(request: HttpRequest):
    unit = request.POST.get("unit")
    check_in_raw = request.POST.get("check_in")
    check_out_raw = request.POST.get("check_out")

    if not (unit and check_in_raw and check_out_raw):
        return None, "Missing information for inquiry."

    try:
        check_in = datetime.fromisoformat(check_in_raw).date()
        check_out = datetime.fromisoformat(check_out_raw).date()
    except ValueError:
        return None, "Invalid dates for inquiry."

    return {
        "unit": unit,
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat(),
    }, None


def _create_inquiry_from_payload(payload: dict) -> None:
    check_in = datetime.fromisoformat(payload["check_in"]).date()
    check_out = datetime.fromisoformat(payload["check_out"]).date()
    unit = payload["unit"]
    uid = f"inquiry-{unit}-{check_in.isoformat()}-{check_out.isoformat()}"

    Reservation.objects.get_or_create(
        uid=uid,
        defaults={
            "unit": unit,
            "check_in": check_in,
            "check_out": check_out,
            "status": "inquiry",
            "guests": 0,
            "customer": None,
            "notes": "Discounted price inquiry created from website.",
        },
    )


def _complete_pending_inquiry(request: HttpRequest) -> bool:
    payload = request.session.pop(PENDING_INQUIRY_SESSION_KEY, None)
    if not payload:
        return False
    _create_inquiry_from_payload(payload)
    return True


def home(request: HttpRequest) -> HttpResponse:
    amenities = [
        "Right on the beach",
        "Floor-to-ceiling ocean view windows",
        "Private balcony with sunset views",
        "Pools, Pickelball, Mini Golf, and more",
        "BBQ Grills and Fully stocked chef’s kitchen",
        "High-speed Wi‑Fi and smart TV",
        "In‑unit washer & dryer",
        "Free parking",
        "Beach chairs, umbrellas, and towels",
    ]
    context = {
        "amenities": amenities,
    }
    return render(request, "rentals/home.html", context)


def get_available_units(check_in, check_out):
    """
    Stub function: replace with real database-backed availability lookup.

    It should return an iterable of room-like objects or dicts describing
    which rooms are free between check_in and check_out (exclusive).
    """
    #get reservations that matter
    subset = Reservation.objects.filter(status__in=['confirmed', 'pending'])
    #find reservations that overlap with check_in and check_out (check_out=check_in is ok)
    checkin_overlap = subset.filter(check_in__gte=check_in, check_in__lt=check_out)

    checkout_overlap = subset.filter(check_out__gt=check_in, check_out__lte=check_out)

    fully_contained = subset.filter(check_in__lte=check_in, check_out__gte=check_out)

    #get the units that are not in any of the overlapping reservations
    available_units = Units.objects.exclude(
            unit__in=checkin_overlap.values_list('unit', flat=True)
        ).exclude(
            unit__in=checkout_overlap.values_list('unit', flat=True)
        ).exclude(
            unit__in=fully_contained.values_list('unit', flat=True)
        )
    return available_units


def pull_vrbo_calendar(request: HttpRequest) -> HttpResponse:
    """
    Pull the calendar data from VRBO and load it into the database.
    """
    units = Units.objects.filter(vendor="vrbo")

    # Collect all reservation data from calendars first (in memory)
    to_create = []
    by_uid = {}

    for unit in units:
        response = requests.get(unit.url, timeout=10)
        response.raise_for_status()
        cal = Calendar.from_ical(response.text)
        for component in cal.walk():
            if component.name != "VEVENT":
                continue
            raw_uid = component.get("uid")
            if not raw_uid:
                continue
            uid = str(raw_uid)
            dtstart = component.get("dtstart")
            dtend = component.get("dtend")
            check_in = dtstart.dt if dtstart else None
            check_out = dtend.dt if dtend else None
            summary = component.get("summary")
            notes = str(summary) if summary is not None else None

            if check_in is None or check_out is None:
                continue

            # Remember the latest data we saw for this UID
            by_uid[uid] = {
                "unit": unit.unit,
                "check_in": check_in,
                "check_out": check_out,
                "status": "confirmed",
                "guests": 0,
                "customer": None,
                "notes": notes,
            }

    if by_uid:
        uids = list(by_uid.keys())
        existing = {
            r.uid: r
            for r in Reservation.objects.filter(uid__in=uids)
        }

        to_update = []
        for uid, data in by_uid.items():
            if uid in existing:
                obj = existing[uid]
                obj.unit = data["unit"]
                obj.check_in = data["check_in"]
                obj.check_out = data["check_out"]
                obj.status = data["status"]
                obj.guests = data["guests"]
                obj.customer = data["customer"]
                obj.notes = data["notes"]
                to_update.append(obj)
            else:
                to_create.append(Reservation(uid=uid, **data))

        if to_create:
            # One INSERT for all new rows; ignore_conflicts is safe with a PK/unique UID
            Reservation.objects.bulk_create(to_create, ignore_conflicts=True)

        if to_update:
            # One UPDATE per row, batched
            Reservation.objects.bulk_update(
                to_update,
                ["unit", "check_in", "check_out", "status", "guests", "customer", "notes"],
            )

    vrbo_uptodate = True

    return reservation_search(request, vrbo_uptodate=vrbo_uptodate)

def reservation_search(request: HttpRequest, vrbo_uptodate: bool = False) -> HttpResponse:
    available_units = None
    check_in = None
    check_out = None

    if request.method == "POST":
        form = ReservationSearchForm(request.POST)
        if form.is_valid():
            check_in = form.cleaned_data["check_in"]
            check_out = form.cleaned_data["check_out"]
            available_units = get_available_units(check_in, check_out)
    else:
        form = ReservationSearchForm()

    context = {
        "form": form,
        "available_rooms": available_units,
        "vrbo_uptodate": vrbo_uptodate,
        "check_in": check_in,
        "check_out": check_out,
    }
    return render(request, "rentals/reservations.html", context)


@require_POST
def create_inquiry(request: HttpRequest) -> HttpResponse:
    """
    Create a Reservation row representing a discounted price inquiry.
    """
    payload, error = _build_inquiry_payload(request)
    if error:
        messages.error(request, error)
        return redirect("reservations")

    if not request.user.is_authenticated:
        request.session[PENDING_INQUIRY_SESSION_KEY] = payload
        messages.info(request, "Create an account to finish your discounted price inquiry.")
        return redirect("register")

    _create_inquiry_from_payload(payload)

    messages.success(
        request,
        "Your discounted price inquiry has been recorded. We'll follow up with details.",
    )
    return redirect("reservations")


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
        form = RenterRegistrationForm(request.POST)
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
        form = RenterRegistrationForm()

    return render(request, "rentals/register.html", {"form": form})


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

    return render(request, "rentals/login.html", {"form": form})


def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    context = {
        "entry_code": settings.RENTER_ENTRY_CODE,
        "pool_code": settings.POOL_ACCESS_CODE,
        "wifi_name": settings.WIFI_NETWORK_NAME,
        "wifi_password": settings.WIFI_PASSWORD,
        "house_manual": settings.HOUSE_MANUAL_TEXT,
    }
    return render(request, "rentals/dashboard.html", context)

