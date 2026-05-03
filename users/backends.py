from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
import phonenumbers

User = get_user_model()

class PhoneOrEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            phone = phonenumbers.format_number(phonenumbers.parse(username, "US"), phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            phone = None
        try:
            user = User.objects.get(Q(email=username) | Q(phone=phone))
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None