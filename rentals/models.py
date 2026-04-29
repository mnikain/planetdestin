from django.conf import settings
from django.db import models


class Reservation(models.Model):
    STATUS = [
        ("archived", "Archived"),
        ("inquiry", "Inquiry"),
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
    ]
    UNITS = [(810, "810"), (910, "910"), (1108, "1108"), (1109, "1109")]
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.IntegerField(default=0)
    unit = models.CharField(max_length=20, choices=UNITS)
    uid = models.CharField(max_length=200, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservations",
    )
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS, default="Inquiry")

    def __str__(self) -> str:
        return f"{self.uid} - {self.customer} - {self.check_in} to {self.check_out} - {self.unit}"


class Units(models.Model):
    unit = models.CharField(max_length=20, choices=Reservation.UNITS)
    vendor = models.CharField(max_length=20, choices=[("vrbo", "VRBO")])
    property_id = models.CharField(max_length=20, blank=True, null=True)
    url = models.URLField(max_length=200)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)
    info = models.TextField(blank=True, null=True)
    sleeps = models.IntegerField(default=6)

    def __str__(self) -> str:
        return f"{self.unit} - {self.vendor}"


class Codes(models.Model):
    ctype = models.TextField(
        choices=[
            ("pool", "Pool"),
            ("pickleball", "Pickleball"),
            ("entry", "Door Entry"),
            ("wifi-ssid", "WiFi SSID"),
            ("wifi-password", "WiFi Password"),
            ("checkin-checkout", "Check-in/Check-out instructions"),
        ]
    )
    value = models.CharField(max_length=20)
    activation_date = models.DateField(blank=True, null=True)
    expiration_date = models.DateField(blank=True, null=True)
    unit = models.ForeignKey(Units, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.unit} - {self.ctype} - {self.value}"
