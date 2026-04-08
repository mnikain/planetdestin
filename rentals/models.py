from django.db import models



class User(models.Model):
    email = models.CharField(max_length=200, unique=True)
    phone = models.CharField(max_length=200, unique=True)
    password = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)    
    def __str__(self) -> str:
        return f"{self.email} - {self.phone}"

class Customer(models.Model):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=200)
    zipcode = models.CharField(max_length=200)
    country = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} - {self.user}"

class Reservation(models.Model):
    STATUS = [('archived','Archived'),('inquiry','Inquiry'),('pending', 'Pending'),('confirmed', 'Confirmed'),('cancelled', 'Cancelled')]
    UNITS = [(810, '810'),(910, '910'),(1108, '1108'),(1109, '1109')]
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.IntegerField(default=0)
    unit = models.CharField(max_length=20, choices=UNITS)
    uid = models.CharField(max_length=200, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS, default='Inquiry')

        

    def __str__(self) -> str:
        return f"{self.uid} - {self.customer} - {self.check_in} to {self.check_out} - {self.unit}"

class Units(models.Model):
    unit = models.CharField(max_length=20, choices=Reservation.UNITS)
    vendor = models.CharField(max_length=20, choices=[('vrbo', 'VRBO')])
    url = models.URLField(max_length=200)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)
    info = models.TextField(blank=True, null=True)
    sleeps = models.IntegerField(default=6)
    def __str__(self) -> str:
        return f"{self.unit} - {self.vendor}"