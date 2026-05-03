from django.db import models
from django.contrib.auth.models import AbstractUser,BaseUserManager
from django import forms
import re
import phonenumbers


class CustomUserManager(BaseUserManager):
    def create_user(self, email, phone, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        user = self.model(email=self.normalize_email(email), phone=phone, first_name=first_name, last_name=last_name,
        **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self, email, phone, first_name, last_name, password=None):
        user = self.create_user(email, phone, first_name, last_name, password)
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save(using=self._db)
        return user

#Create a custom user model
class CustomUser(AbstractUser):
    username = None
    phone = models.CharField(max_length=200, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    reset_emails = models.IntegerField(default=0)
    last_reset_email = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["phone", "first_name", "last_name"]

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if self.phone:
            self.phone = phonenumbers.format_number(phonenumbers.parse(self.phone, "US"), phonenumbers.PhoneNumberFormat.E164)
        else:
            self.phone = None

        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.email
