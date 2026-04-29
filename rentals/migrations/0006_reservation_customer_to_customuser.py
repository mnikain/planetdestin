# Generated manually for Reservation.customer -> CustomUser

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def copy_customer_user_to_booking_guest(apps, schema_editor):
    Reservation = apps.get_model("rentals", "Reservation")
    Customer = apps.get_model("rentals", "Customer")
    for res in Reservation.objects.exclude(customer_id__isnull=True).iterator():
        try:
            cust = Customer.objects.get(pk=res.customer_id)
        except Customer.DoesNotExist:
            continue
        uid = getattr(cust, "user_id", None)
        if uid:
            Reservation.objects.filter(pk=res.pk).update(booking_guest_id=uid)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("rentals", "0005_alter_customer_user_alter_codes_ctype_delete_user"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="reservation",
            name="booking_guest",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(copy_customer_user_to_booking_guest, noop_reverse),
        migrations.RemoveField(
            model_name="reservation",
            name="customer",
        ),
        migrations.RenameField(
            model_name="reservation",
            old_name="booking_guest",
            new_name="customer",
        ),
        migrations.AlterField(
            model_name="reservation",
            name="customer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="reservations",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
