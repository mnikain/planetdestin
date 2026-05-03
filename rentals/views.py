from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from datetime import datetime, time, timedelta
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone
from django.urls import reverse
from django.core.cache import cache

from beach_rental_site.settings import LOGIN_URL

from .forms import ReservationSearchForm
from .models import Codes, Reservation, Units
import requests
from icalendar import Calendar
import uuid
import pandas as pd
import threading
import io
import msoffcrypto
import re
from django.contrib.auth import get_user_model

PENDING_INQUIRY_SESSION_KEY = "pending_inquiry"
User = get_user_model()

def send_email(subject: str, message: str):
    for email in settings.NOTIFICATION_EMAIL_LIST:
        send_mail(subject, message, settings.EMAIL_HOST_USER, [email], fail_silently=False)

def send_inquiry_email():
    # check cache to see if we have already sent the email within the past 30 minutes
    if cache.get("last_inquiry_email_sent"):
        return None
    cache.set("last_inquiry_email_sent", timezone.now(), timeout=settings.MIN_EMAIL_INTERVAL)
    try:
        #include all inquiries for all units
        inquiries = Reservation.objects.filter(status="inquiry")
        message = "New inquiries:\n"
        for inquiry in inquiries:
            email = inquiry.customer.email if inquiry.customer else "Unknown"
            message += f"{inquiry.unit} - {inquiry.created_at.strftime('%Y-%m-%d %H:%M:%S')} - {email} - {inquiry.check_in} to {inquiry.check_out}\n"
        send_email("New inquiries", message)
    except Exception as e:
        return f"Error sending inquiry email: {e}"
    return None

def send_new_user_emails(request: HttpRequest) -> HttpResponse:
    #for now send a message saying function not yet implemented 
    messages.error(request, "Function not yet implemented")
    return render(request, "rentals/operations.html", {})

    #IMPLEMENT LATER
    new_users = User.objects.filter(is_new=True)
    for user in new_users:
        send_email("New user", f"A new user has been created: {user.email}")
    return render(request, "rentals/operations.html", {})

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

    errors = []
    for unit in units:
        try:
            response = requests.get(unit.url, timeout=10)
        except requests.exceptions.RequestException as e:
           errors.append(f"Error pulling calendar for {unit.unit}: {e}")
           continue
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

    if errors:
        messages.error(request, "\n".join(errors))
    else:
        messages.success(request, "VRBO calendar has been pulled successfully.")    
    return render(request, "rentals/operations.html", {}) 

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
        #also kick off the vrbo calendar pull in a thread if none ran within the last 30 minutes
        if not cache.get("last_vrbo_calendar_pull"):
            threading.Thread(target=pull_vrbo_calendar).start()    
            cache.set("last_vrbo_calendar_pull", timezone.now(), timeout=settings.MIN_VRBO_CALENDAR_PULL_INTERVAL)
        form = ReservationSearchForm()

    context = {
        "form": form,
        "available_rooms": available_units,
        "vrbo_uptodate": vrbo_uptodate,
        "check_in": check_in,
        "check_out": check_out,
    }
    return render(request, "rentals/reservations.html", context)


def _complete_pending_inquiry(request: HttpRequest) -> HttpResponse:
    payload = request.session.pop(PENDING_INQUIRY_SESSION_KEY, None)
    try:
        Reservation.objects.get_or_create(
            uid=str(uuid.uuid4()),
            defaults={
                "unit": payload["unit"],
                "check_in": datetime.fromisoformat(payload["check_in"]).date(),
                "check_out": datetime.fromisoformat(payload["check_out"]).date(),
                "status": "inquiry",
                "guests": 0,
                "customer": request.user,
                "notes": "Discounted price inquiry created from website.",
            },
        )
    except Exception as e:
        messages.error(request, f"Sorry for the hassle! Having difficulty creating your inquiry, would you call us to take care of it for you?: {e}")
        return redirect("reservations")

    error = send_inquiry_email()
    #TODO add some logging for the error
    if error:
        print(error)
    messages.success(request, "Your discounted price inquiry has been recorded. We'll follow up with details.")

    #at this point, the user is authenticated, so we can create the inquiry and send him to the dashboard
    return redirect("dashboard")

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
        messages.info(request, "Login or create an account to finish your discounted price inquiry.")
        login_url = reverse("users:login")
        return redirect(f"{login_url}?next={reverse('_complete_pending_inquiry')}")
    else:
        return _complete_pending_inquiry(request)

 

def _aware_local(dt: datetime) -> datetime:
    tz = timezone.get_current_timezone()
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, tz)
    return timezone.localtime(dt, tz)


def _active_codes_queryset(unit: Units):
    today = timezone.localdate()
    return Codes.objects.filter(unit=unit).filter(
        Q(activation_date__isnull=True) | Q(activation_date__lte=today),
        Q(expiration_date__isnull=True) | Q(expiration_date__gte=today),
    )


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    today = timezone.localdate()
    now = timezone.now()

    confirmed_records = (
        Reservation.objects.filter(
            customer=request.user,
            status="confirmed",
            check_out__gte=today,
        )
        .select_related("customer")
        .order_by("check_in")
    )
    active_inquiries = Reservation.objects.filter(
        customer=request.user,
        status="inquiry",
        check_out__gte=today,
    ).order_by("check_in")

    reservation = None
    check_in_moment = None
    checkout_moment = None
    codes_visible_after = None
    show_codes = False
    too_early_for_codes = False
    unit_obj = None
    code_by_type: dict[str, str] = {}

    # Pick the first confirmed reservation that has not passed checkout time.
    for candidate in confirmed_records:
        candidate_check_in = _aware_local(datetime.combine(candidate.check_in, time(15, 0)))
        candidate_checkout = _aware_local(datetime.combine(candidate.check_out, time(11, 0)))
        if now >= candidate_checkout:
            continue

        reservation = candidate
        check_in_moment = candidate_check_in
        checkout_moment = candidate_checkout
        codes_visible_after = check_in_moment - timedelta(hours=48)
        show_codes = codes_visible_after <= now < checkout_moment
        too_early_for_codes = now < codes_visible_after
        break

    if show_codes and reservation:
        unit_obj = Units.objects.filter(unit=reservation.unit).first()
        if unit_obj:
            for row in _active_codes_queryset(unit_obj):
                code_by_type[row.ctype] = row.value

    context = {
        "reservation": reservation,
        "active_inquiries": active_inquiries,
        "show_codes": show_codes,
        "too_early_for_codes": too_early_for_codes,
        "codes_visible_after": codes_visible_after,
        "checkout_moment": checkout_moment,
        "unit_obj": unit_obj,
        "code_by_type": code_by_type,
        "entry_code": code_by_type.get("entry") or settings.RENTER_ENTRY_CODE,
        "pool_code": code_by_type.get("pool") or settings.POOL_ACCESS_CODE,
        "pickleball_code": code_by_type.get("pickleball") or settings.POOL_ACCESS_CODE,
        "wifi_name": code_by_type.get("wifi-ssid") or settings.WIFI_NETWORK_NAME,
        "wifi_password": code_by_type.get("wifi-password") or settings.WIFI_PASSWORD,
        "house_manual": code_by_type.get("checkin-checkout") or settings.HOUSE_MANUAL_TEXT,
    }
    return render(request, "rentals/dashboard.html", context)

def operations(request: HttpRequest) -> HttpResponse:
    return render(request, "rentals/operations.html", {})


def _split_name(name_str):
    """
    Extracts the first and last name from a string, handling titles, 
    suffixes, middle initials, and dual-person names.
    """
    if not name_str:
        return None, None

    # 1. Remove common titles and suffixes (case-insensitive)
    # This cleans "Dr. Jane Doe Jr." -> "Jane Doe"
    noise = r'\b(Mr|Ms|Mrs|Miss|Dr|Prof|Sr|Jr|III|II|IV|PhD|MD)\b\.?'
    clean_name = re.sub(noise, '', name_str, flags=re.IGNORECASE).strip()
    
    # 2. Handle "Person A and Person B Lastname"
    # Matches: "Alice and Bob Johnson" or "Alice & Bob Johnson"
    # Logic: Capture the very first name and the very last name.
    dual_pattern = r'^([\w-]+)\s+(?:and|&)\s+[\w-]+\s+([\w-]+)$'
    dual_match = re.search(dual_pattern, clean_name, re.IGNORECASE)
    if dual_match:
        return dual_match.group(1), dual_match.group(2)

    # 3. Standard parsing
    # Split by whitespace and filter out any empty strings
    parts = clean_name.split()
    
    if len(parts) == 0:
        return None, None
    if len(parts) == 1:
        return parts[0], None
    
    # In "First Middle Last" or "First M. Last", 
    # the first element is the First Name and the last is the Last Name.
    first_name = parts[0]
    last_name = parts[-1]
    
    return first_name, last_name


def upload_accounting_file(request: HttpRequest) -> HttpResponse:
# Create a temporary, in-memory file-like object
    if request.method == "POST":
        decrypted_workbook = io.BytesIO()
        f = request.FILES["excel_file"]
        office_file = msoffcrypto.OfficeFile(f)
        office_file.load_key(password=settings.ACCOUNTING_PASSWORD)
        office_file.decrypt(decrypted_workbook)

        columns = {'first_name': 'first_name',
                'last_name': 'last_name',
                'DATE': 'checkin', 
                'UNIT': 'unit', 
                'GUEST RESERVATION ID': 'resid', 
                'GUEST EMAIL': 'email',
                'GUEST PHONE': 'phone'}
        # first and last name will be extracted from DESCRIPTION and don't yet exist so has to be here too
        str_columns = {x: str for x in columns.keys() if x not in ['first_name', 'last_name', 'DATE']}

        # Now use pandas or openpyxl to read the decrypted file
        # Example with Pandas:
        df = pd.read_excel(decrypted_workbook, sheet_name=settings.ACCOUNTING_SHEET, converters=str_columns)

        #fix the date so missing dates won't error out (but will get filtered)
        df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
        cutoff_date = timezone.localdate() - timedelta(weeks=settings.WEEK_WINDOW)
        cutoff_ts = pd.Timestamp(cutoff_date)
        df = df[(df['CATEGORY'] == 'Rental Income') & (df['DATE'] >= cutoff_ts)]
        df[['first_name','last_name'] ] = pd.DataFrame(
                [_split_name(x) for x in df['DESCRIPTION']], index=df.index)

        #get rid of the unused columns and rename to our column names
        df = df[columns.keys()]
        df = df.rename(columns={x[0]: x[1] for x in columns.items() if x[0] != x[1]})

        #find reservation objects that have the same unit name and checkin dates and update those reservations with the new information otherwise create new reservations
        count = 0
        new_reservation_count = 0
        new_user_count = 0
        for index, row in df.iterrows():
            reservation = Reservation.objects.filter(unit=row['unit'], check_in=row['checkin']).first()
            user = User.objects.filter(Q(email=row['email']) | Q(phone=row['phone'])).first()
            if not user:
                #create a user object with the email and phone number
                user = User.objects.create(
                    email=row['email'],
                    phone=row['phone'],
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                )
                new_user_count += 1
            if reservation:
                reservation.customer = user
                reservation.save()
                count += 1
            else:
                Reservation.objects.create(
                    unit=row['unit'],
                    check_in=row['checkin'],
                    check_out=row['checkin'],  # spreadsheet doesn't have check out date, put it the same so we can check later
                    customer=user,
                    notes=f"Imported from accounting spreadsheet for {row['first_name']} {row['last_name']}",
                    status="review",
                )
                new_reservation_count += 1
            
        messages.success(request, f"Updated: {count}, added: {new_reservation_count}, new users: {new_user_count}, total records: {len(df)}")
        return render(request, "rentals/operations.html", {})

