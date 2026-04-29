from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model; User = get_user_model()
from django.utils import timezone

import re




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

