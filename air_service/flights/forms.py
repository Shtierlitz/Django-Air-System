import secrets

from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from flights.models import *
from django import forms
from flights.tasks import ticket_expiration_task


class RegisterUserForm(UserCreationForm):
    username = forms.CharField(label='User Name', widget=forms.TextInput(
        attrs={'type': "text", 'id': "form3Example1cg", 'class': "form-control form-control-lg"}))
    password1 = forms.CharField(label='Password',
                                widget=forms.PasswordInput(attrs={'type': "password", 'id': "form3Example4cg",
                                                                  'class': "form-control form-control-lg"}))
    password2 = forms.CharField(label='Repeat password',
                                widget=forms.PasswordInput(attrs={'type': "password", 'id': "form3Example4cg",
                                                                  'class': "form-control form-control-lg"}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(
        attrs={'type': "email", 'id': "form3Example3cg", 'class': "form-control form-control-lg"}))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class LoginUserForm(AuthenticationForm):
    username = forms.CharField(label='User name', widget=forms.TextInput(
        attrs={'type': "text", 'id': "form3Example1cg", 'class': "form-control form-control-lg"}))
    password = forms.CharField(label='Password',
                               widget=forms.PasswordInput(attrs={'type': "password", 'id': "form3Example4cg",
                                                                 'class': "form-control form-control-lg"}))


class FlightBookingForm(forms.ModelForm):
    class Meta:
        model = Flight
        fields = ['id', 'departure_time', 'arrival_time', 'aircraft', 'origin_airport', 'destination_airport']


class ExtraForm(forms.ModelForm):
    class Meta:
        model = Extra
        fields = ['name', 'description', 'available']


class StripeForm(forms.Form):
    cardholder_name = forms.CharField(label='Name of card owner:', max_length=100)
    card_number = forms.CharField(label='Card Number:', max_length=20)
    exp_month = forms.CharField(label='MM:', max_length=2)
    exp_year = forms.CharField(label='YY:', max_length=2)
    cvc = forms.CharField(label='cvc:', max_length=100)

    def __init__(self, *args, **kwargs):
        context = kwargs.pop('context', None)
        super().__init__(*args, **kwargs)
        self.context = context

    def clean(self):
        cleaned_data = super().clean()

        cardholder_name = cleaned_data.get('cardholder_name')
        card_number = cleaned_data.get('card_number')
        cvc = cleaned_data.get('cvc')

        new_number = card_number.replace("-", '')

        if len(new_number) < 16 or len(new_number) > 16:
            self.add_error('card_number', "The card number must contain 16 numbers.")

        if not str(new_number).isdigit():
            self.add_error('card_number', 'The card number must consist of numbers and "-" only.')

        if len(cvc) != 3:
            self.add_error('cvc', 'The CVC code must contain 3 numbers.')
        for char in cardholder_name:
            if not (char.isalpha() or char.isspace()):
                self.add_error('cardholder_name', 'The Cardholder Name must consist of letters, not symbols or numbers.')
                break

        return cleaned_data

    def is_valid(self, request):
        is_valid = super().is_valid()
        if not is_valid:
            for field, errors in self.errors.items():
                for error in errors:
                    messages.error(request, error)
        return is_valid

    def save(self):
        flight = Flight.objects.get(pk=self.context['flight_id'])
        seat = self.context['seat']
        ticket = self.context['ticket']

        if self.context['user'] not in flight.users.all():
            flight.users.add(self.context['user'])

        if seat not in flight.seats.all():
            flight.seats.add(seat)

        ticket.status = Status.PAID
        ticket.save()

        return ticket


class SeatForm(forms.ModelForm):
    extra = forms.ModelMultipleChoiceField(
        queryset=Extra.objects.filter(available=True),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    flight = forms.CharField(max_length=4)

    class Meta:
        model = Seat
        fields = ['row_letter', 'seat_number', 'seat_type', 'extra', 'flight']
        widgets = {
            'seat_number': forms.TextInput(attrs={'class': 'form-control'}),
        }
        error_messages = {
            'seat_number': {
                'invalid': 'Field Seat Number must be an integer.',
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['extra'].widget.attrs['class'] = 'extra-checkbox form-check-input'
        for extra_obj in self.fields['extra'].queryset:
            self.fields['extra'].widget.attrs[f'data-price-factor-{extra_obj.pk}'] = extra_obj.price

    def clean(self):
        cleaned_data = super().clean()
        row_letter = cleaned_data.get("row_letter")
        seat_number = cleaned_data.get("seat_number")
        seat_type = cleaned_data.get("seat_type")
        flight_id = cleaned_data.get("flight")

        flight = Flight.objects.get(pk=flight_id)
        seats_in_flight = flight.seats.all()

        for i in seats_in_flight:
            if i.row_letter == row_letter and i.seat_number == seat_number and i.seat_type == seat_type:
                self.add_error(None, "This seat is already booked for the flight.")
        if seat_type == TextClassType.ECONOMY and flight.economy_seats <= 0:
            self.add_error(None, "There are no more seats available for economy class seats.")
        elif seat_type == TextClassType.BUSINESS and flight.business_seats <= 0:
            self.add_error(None, "There are no more seats available for business class seats.")
        elif seat_type == TextClassType.FIRST and flight.first_class_seats <= 0:
            self.add_error(None, "There are no more seats available for a first class seats.")

        return cleaned_data


class TicketConfirmForm(forms.ModelForm):
    extras = forms.MultipleChoiceField(widget=forms.MultipleHiddenInput(), required=False)
    row_letter = forms.CharField(max_length=250)
    seat_number = forms.CharField(max_length=250)
    seat_type = forms.CharField(max_length=250)

    class Meta:
        model = Ticket
        fields = ['flight', 'price', 'user', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['extras'].choices = [(extra.pk, extra.name) for extra in Extra.objects.all()]

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        flight = cleaned_data.get('flight')
        row_letter = cleaned_data.get('row_letter')
        seat_number = cleaned_data.get('seat_number')
        seat_type = cleaned_data.get('seat_type')
        seat = Seat.objects.filter(row_letter=row_letter,
                                   seat_number=seat_number,
                                   seat_type=seat_type).first()
        ticket = Ticket.objects.filter(user=user,
                                       flight=flight,
                                       seat=seat).first()
        if ticket is not None:
            self.add_error(None, 'You have already purchased this ticket!')

        return cleaned_data

    def save_ticket(self):
        user = self.cleaned_data.get('user')
        flight = self.cleaned_data.get('flight')
        price = self.cleaned_data.get('price')
        status = self.cleaned_data.get('status')
        extras = self.cleaned_data.get('extras')
        row_letter = self.cleaned_data.get('row_letter')
        seat_number = self.cleaned_data.get('seat_number')
        seat_type = self.cleaned_data.get('seat_type')

        code = secrets.token_hex(3).upper()

        while Ticket.objects.filter(code=code).exists():
            code = secrets.token_hex(3).upper()

        seat, created = Seat.objects.get_or_create(
            row_letter=row_letter,
            seat_number=seat_number,
            seat_type=seat_type
        )
        ticket, created = Ticket.objects.get_or_create(
            code=code,
            user=user,
            flight=flight,
            price=price,
            status=status,
            seat=seat
        )
        flight.seats.add(seat)

        if seat.seat_type == TextClassType.ECONOMY:
            flight.economy_seats -= 1
        elif seat.seat_type == TextClassType.BUSINESS:
            flight.business_seats -= 1
        else:
            flight.first_class_seats -= 1
        flight.save()

        if created:
            print("A new ticket was created.")
        else:
            print("An existing ticket was retrieved.")

        for i in extras:
            extra = Extra.objects.get(pk=i)
            ticket.tickets_extras.add(extra)

        # creating expiration task
        eta = ticket.flight.departure_time
        task = ticket_expiration_task.apply_async(args=[ticket.id], eta=eta)
        ticket.task_id = task.id
        ticket.save()

        return ticket


class AircraftForm(forms.ModelForm):
    class Meta:
        model = Aircraft
        fields = ['model', 'aircraft_type', 'total_seats']


class ChangeProfileForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Input new user name..."}), required=False)
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Input new first name..."}), required=False)
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Input new last name..."}), required=False)
    email = forms.EmailField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Input new email..."}), required=False)
    phone = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Input new phone number..."}), required=False)
    gender = forms.ChoiceField(choices=User.Genders.choices, widget=forms.Select(attrs={'class': 'form-control'}), required=False)


class AirportForm(forms.ModelForm):
    class Meta:
        model = Airport
        fields = ['name', 'code', 'city', 'country']
