import datetime

from django.forms import DateTimeInput

from air_service.celery import app
from flights.models import *
from django import forms
from django.utils import timezone

from flights.utils import clean_or_errors
from django.contrib.auth.models import User, Group
from flights.tasks import flight_expiration_task, logger, ticket_expiration_task


class AssignRoleForm(forms.ModelForm):
    ROLE_CHOICES = [
        ('', '---------'),
        ('remove_role', 'Remove role'),
    ]

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        required=False,
        help_text="Select the role you want to assign to the user, "
                  "or select 'Remove role' to remove the role, or leave it blank to do nothing."
    )

    class Meta:
        model = User
        fields = ('role',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = self.ROLE_CHOICES + [(group.pk, group.name) for group in Group.objects.all()]

    def save(self, *args, **kwargs):
        user = super().save(commit=False)

        if self.cleaned_data['role']:
            if self.cleaned_data['role'] == 'remove_role':
                user.groups.clear()
            else:
                user.groups.set([self.cleaned_data['role']])

        user.save()
        return user


class StaffCheckInForm(forms.ModelForm):
    check_in = forms.ChoiceField(choices=Ticket.Checking.choices,
                                 widget=forms.Select(attrs={'class': 'form-select custom-select-centered'}),
                                 required=False)
    onboard = forms.ChoiceField(choices=Ticket.Checking.choices,
                                widget=forms.Select(attrs={'class': 'form-select custom-select-centered'}),
                                required=False)

    class Meta:
        model = Ticket
        fields = ['check_in', 'onboard']


class StaffExtraForm(forms.ModelForm):
    class Meta:
        model = Extra
        fields = ('name', 'description', 'available', 'price')


class FlightCreateForm(forms.ModelForm):
    class Meta:
        model = Flight
        fields = (
            'name', 'departure_time', 'arrival_time', 'aircraft', 'origin_airport', 'destination_airport', 'economy_seats',
            'business_seats', 'first_class_seats')
        widgets = {
            'departure_time': DateTimeInput(attrs={'type': 'datetime-local'}),
            'arrival_time': DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        aircraft = cleaned_data['aircraft']
        clean_or_errors(cleaned_data, aircraft, self.add_error)
        return cleaned_data

    def save(self, commit=True):
        flight = super(FlightCreateForm, self).save(commit=False)

        if commit:
            flight.save()
            eta = flight.departure_time
            task = flight_expiration_task.apply_async(args=[flight.id], eta=eta)  # Передайте flight.id, а не сам объект flight
            flight.task_id = task.id
            flight.save()

        return flight


class FlightUpdateForm(forms.ModelForm):
    class Meta:
        model = Flight
        fields = (
            'name', 'departure_time', 'arrival_time', 'aircraft', 'origin_airport', 'destination_airport', 'economy_seats',
            'business_seats', 'first_class_seats')
        widgets = {
            'departure_time': DateTimeInput(attrs={'type': 'datetime-local'}),
            'arrival_time': DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def save(self, commit=True):
        flight = super(FlightUpdateForm, self).save(commit=False)

        if commit:
            # Изменить статус полета в случае если полет ранее просрочен
            if flight.departure_time > timezone.make_aware(datetime.datetime.now()):
                flight.expire = Expiring.ACTIVE
                flight.save()

            # Отменить текущую задачу
            if flight.task_id:
                try:
                    app.control.revoke(flight.task_id)
                    logger.info(f"Задача рейса с номером {flight.name} успешно уделена")
                except Exception as e:
                    logger.error(f"Ошибка при отмене задачи с ID {flight.task_id}: {e}")

            # Создать новую задачу с обновленным временем отправления
            eta = flight.departure_time
            task = flight_expiration_task.apply_async(args=[flight.id], eta=eta)
            flight.task_id = task.id
            flight.save()

            # Удалить задачу на билете и создать новую
            tickets = Ticket.objects.filter(flight=flight.id)
            for ticket in tickets:

                # Вернуть существующим билетам статус Active если ранее они были неактивны
                if ticket.flight.departure_time > timezone.make_aware(datetime.datetime.now()):
                    ticket.expire = Expiring.ACTIVE
                    ticket.save()

                if ticket.task_id:
                    try:
                        app.control.revoke(ticket.task_id)
                        logger.info(f"Задача билета с номером {ticket.code} успешно уделена")
                    except Exception as e:
                        logger.error(f"Ошибка при отмене задачи билета с номером {ticket.code}: {e}")

                    eta = ticket.flight.departure_time
                    task = ticket_expiration_task.apply_async(args=[ticket.id], eta=eta)
                    ticket.task_id = task.id
                    ticket.save()

        return flight

    def clean(self):
        cleaned_data = super().clean()
        aircraft = self.instance.aircraft
        clean_or_errors(cleaned_data, aircraft, self.add_error)
        return cleaned_data


class AircraftCreateForm(forms.ModelForm):
    class Meta:
        model = Aircraft
        fields = '__all__'


class AirportForm(forms.ModelForm):
    class Meta:
        model = Airport
        fields = '__all__'
