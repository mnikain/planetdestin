from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model; User = get_user_model()
from django.utils import timezone
from phonenumber_field.formfields import PhoneNumberField
from users.models import CustomUser
import re



class LoginForm (AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)   
        self.fields['username'].label = 'Email or Phone Number'
        self.fields['password'].label = 'Password'

class UserRegistrationForm(UserCreationForm):
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
    class Meta(UserCreationForm.Meta):
        model = User
        #fields = UserCreationForm.Meta.fields + ("email", "phone")
        fields = ('first_name', 'last_name', 'email', 'phone', 'password1', 'password2')

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
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.phone = self.cleaned_data["phone"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user = get_user_model().objects.create_user(
                email=self.cleaned_data["email"],
                phone=self.cleaned_data["phone"],
                first_name=self.cleaned_data["first_name"],
                last_name=self.cleaned_data["last_name"],
                password=self.cleaned_data["password1"]
            )
        return user