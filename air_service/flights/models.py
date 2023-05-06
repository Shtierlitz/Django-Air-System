import datetime

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class Status(models.TextChoices):
    PAID = 'PAID'
    UNPAID = 'UNPAID'


class User(AbstractUser):
    class Genders(models.TextChoices):
        MALE = 'Male'
        FEMALE = 'Female'
        X = 'X'
    username = models.CharField(max_length=50, verbose_name="User name", unique=True)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    email_verify = models.BooleanField(default=False)
    phone = models.CharField(max_length=13, null=True, default='+380666666666')
    gender = models.CharField(max_length=10, choices=Genders.choices, default=Genders.X)

    def __str__(self):
        return self.username

    class Meta:
        ordering = ("id",)


class Expiring(models.TextChoices):
    ACTIVE = 'ACTIVE'
    EXPIRED = 'EXPIRED'


class Ticket(models.Model):

    class Meta:
        permissions = [
            ("can_approve_check_in", "Can approve check-in"),
            ("can_approve_onboard", "Can approve onboard"),
        ]

    class Checking(models.TextChoices):
        APPROVED = 'APPROVED'
        NOT_APPROVED = 'NOT APPROVED'

    code = models.CharField(max_length=6, unique=True, null=True)
    status = models.TextField(choices=Status.choices, default=Status.UNPAID)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    flight = models.ForeignKey('Flight', on_delete=models.CASCADE, related_name='tickets', null=True)
    price = models.FloatField(default=100.0)
    seat = models.ForeignKey('Seat', on_delete=models.PROTECT, null=True)
    booking_date = models.DateTimeField(auto_now_add=True, null=True)
    check_in = models.TextField(choices=Checking.choices, default=Checking.NOT_APPROVED)
    onboard = models.TextField(choices=Checking.choices, default=Checking.NOT_APPROVED)
    expire = models.TextField(choices=Expiring.choices, default=Expiring.ACTIVE)
    task_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Ticket of {self.user}"

class ClassType(models.TextChoices):
    ECONOMY = '1.2'
    BUSINESS = '2.3'
    FIRST = '3.0'


class Extra(models.Model):
    class Meta:
        permissions = [
            ("can_manage_extras", "Can manage extras"),
        ]
    name = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True)
    available = models.BooleanField(default=True)
    price = models.FloatField(max_length=50, default=10)
    tickets = models.ManyToManyField(Ticket, related_name='tickets_extras')
    def __str__(self):
        return self.name


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, null=True)
    price = models.CharField(max_length=255, default='0')
    date = models.DateTimeField(auto_now_add=True)
    cardholder_name = models.CharField(max_length=255, null=True)


class TextClassType(models.TextChoices):
    ECONOMY = 'Economy'
    BUSINESS = 'Business'
    FIRST = 'First'


class Seat(models.Model):
    class Meta:
        permissions = [
            ("can_manage_seats", "Can manage seats"),
        ]
    class SeatRows(models.TextChoices):
        A = 'A'
        B = 'B'
        C = 'C'
    row_letter = models.CharField(max_length=1, choices=SeatRows.choices, null=True)
    seat_number = models.IntegerField(null=True)
    seat_type = models.CharField(max_length=50, choices=TextClassType.choices, default=TextClassType.ECONOMY)

    def __str__(self):
        return str(self.pk)
        # return f"{self.row_letter}{self.seat_number} {self.seat_type}"


class Flight(models.Model):
    class Meta:
        permissions = [
            ("can_manage_flights", "Can manage flights"),
        ]

    name = models.CharField(max_length=255, default='Test')
    departure_time = models.DateTimeField(null=True)
    arrival_time = models.DateTimeField(null=True)
    aircraft = models.ForeignKey('Aircraft', on_delete=models.CASCADE, null=True)
    origin_airport = models.ForeignKey('Airport', on_delete=models.CASCADE, related_name='orig_airport', null=True)
    destination_airport = models.ForeignKey('Airport', on_delete=models.CASCADE, related_name='dest_airport', null=True)
    economy_seats = models.IntegerField(null=True)
    business_seats = models.IntegerField(null=True)
    first_class_seats = models.IntegerField(null=True)
    seats = models.ManyToManyField(Seat, related_name='flights_seats')
    users = models.ManyToManyField(User, related_name='users_flights')
    expire = models.TextField(choices=Expiring.choices, default=Expiring.ACTIVE)
    task_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Origin airport: {self.origin_airport}"

    def get_absolute_url(self):
        return reverse('flight', kwargs={'flight_id': self.pk})

    def total_seats(self):
        return self.economy_seats + self.business_seats + self.first_class_seats


class AircraftTypes(models.TextChoices):
    BOEING = 'Boeing'
    AIRBUS = 'Airbus'
    EMBRAER = 'Embraer'
    CESSNA = 'Cessna'


class Aircraft(models.Model):
    class Meta:
        permissions = [
            ("can_manage_aircraft", "Can manage aircraft"),
        ]

    model = models.CharField(max_length=255, null=True, unique=True)
    aircraft_type = models.CharField(max_length=255, choices=AircraftTypes.choices, default=AircraftTypes.BOEING, null=True)
    total_seats = models.IntegerField(null=True)

    def __str__(self):
        return f"{self.model}, seats = {self.total_seats}"


class Airport(models.Model):
    class Meta:
        permissions = [
            ("can_manage_airports", "Can manage airports"),
        ]
    name = models.CharField(max_length=255, null=True, unique=True)
    code = models.CharField(max_length=3, null=True)
    city = models.CharField(max_length=255, null=True)
    country = models.CharField(max_length=2, null=True)

    def __str__(self):
        return f'{self.name}, {self.city}, {self.code}, {self.country}'






