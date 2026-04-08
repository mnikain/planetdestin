from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from phonenumber_field.formfields import PhoneNumberField
import re


class RenterRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text="Optional.")
    last_name = forms.CharField(max_length=30, required=False, help_text="Optional.")
    email = forms.EmailField(
        max_length=254,
        required=True,
        help_text="Required. We’ll send booking details here.",
    )
    phone = PhoneNumberField(
        required=False,
        region="US",
        help_text="optional, if provided, you can use login using phone or email",
    )
    class Meta:
        model = User
        fields = (
            "email",
            "phone",
            "first_name",
            "last_name",
            "password1",
            "password2",
        )

    def clean_phone(self):
        raw_phone = (self.data.get("phone") or "").strip()
        digits_only = re.sub(r"\D", "", raw_phone)

        # If someone enters exactly 10 digits, assume a US number.
        if raw_phone and len(digits_only) == 10 and not raw_phone.startswith("+"):
            raw_phone = f"+1{digits_only}"

        cleaned_phone = self.fields["phone"].clean(raw_phone)
        if cleaned_phone:
            return cleaned_phone.as_e164
        return cleaned_phone


class ReservationSearchForm(forms.Form):
    check_in = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Check-in",
    )
    check_out = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Check-out",
    )

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get("check_in")
        check_out = cleaned_data.get("check_out")

        if check_in and check_out and check_in >= check_out:
            raise forms.ValidationError("Check-out date must be after check-in date.")

        if check_in and check_in < timezone.localdate():
            raise forms.ValidationError("Check-in date cannot be in the past.")

        return cleaned_data

