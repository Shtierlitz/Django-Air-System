from datetime import datetime
from unittest.mock import patch
from django.contrib.auth.models import User, Group
from django.test import Client, TestCase, RequestFactory
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from django.test import override_settings
from flights.forms import ChangeProfileForm
from flights.models import Ticket, Flight, Aircraft, AircraftTypes, Airport, Extra, Seat, TextClassType, Expiring, \
    Payment, User, Status
l

# User = get_user_model()


class TestViews(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user1 = User.objects.create_user(username='test_username_1', first_name='test_first_name_1',
                                              last_name='test_last_name_1',
                                              email='rollbar1990@gmail.com',
                                              email_verify=True,
                                              password='test_password')
        self.client.login(username='test_username_1', password='test_password')
        self.aircraft = Aircraft.objects.create(model="MODEL", aircraft_type=AircraftTypes.BOEING, total_seats=10)
        self.airport = Airport.objects.create(name='AIRPORT', code="AAA", city="CITY", country="COUNTRY")
        self.flight = Flight.objects.create(
            name='FLIGHT',
            departure_time=timezone.make_aware(datetime(23, 12, 12, 0, 0, 0, 0)),
            arrival_time=timezone.make_aware(datetime(23, 12, 13, 0, 0, 0, 0)),
            aircraft=self.aircraft,
            origin_airport=self.airport,
            destination_airport=self.airport,
            economy_seats=2,
            business_seats=2,
            first_class_seats=2,
            expire='ACTIVE')
        self.extra = Extra.objects.create(
            name="EXTRA",
            description="EXTRA_DESCRIPTION",
            available=True,
            price=Decimal('100.00'),
        )
        self.extra2 = Extra.objects.create(
            name="EXTRA",
            description="EXTRA_DESCRIPTION",
            available=True,
            price=Decimal('200.00'),
        )
        self.extra3 = Extra.objects.create(
            name="EXTRA",
            description="EXTRA_DESCRIPTION",
            available=True,
            price=Decimal('300.00'),
        )
        self.seat = Seat.objects.create(row_letter=Seat.SeatRows.A, seat_number=1, seat_type=TextClassType.FIRST)
        self.flight.seats.add(self.seat)
        self.ticket = Ticket.objects.create(code='CODE',
                                            status='UNPAID',
                                            user=self.user1,
                                            flight=self.flight,
                                            price=Decimal('100.00'),
                                            seat=self.seat,
                                            booking_date=timezone.make_aware(datetime(23, 12, 12, 0, 0, 0, 0)),
                                            check_in=Ticket.Checking.NOT_APPROVED,
                                            onboard=Ticket.Checking.NOT_APPROVED,
                                            expire=Expiring.ACTIVE
                                            )
        self.post_data = {
            'card_number': '4242-4242-4242-4242',  # Тестовый номер карты Stripe
            'exp_month': '12',
            'exp_year': '23',
            'cvc': '123',
            'cardholder_name': 'Dredd',
        }
        self.session_data = {
            'data': {
                'seat': 'A1',
                'extras': [self.extra.id],
                'row_letter': 'A',
                'seat_number': 1,
                'seat_type': 'Business',
                'price': '100'
            }
        }
        self.session_data_booking = {
            'price': '100',
            'extras': [1, 2, 3],
            'row_letter': 'A',
            'seat_number': '1',
            'seat_type': TextClassType.ECONOMY,
            'flight': self.flight.id,
            'user': self.user1.id,
            'status': Status.UNPAID,
        }

    def test_RegisterUser_get(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')

    def test_RegisterUser_post(self):
        response = self.client.post(reverse('register'), {
            'username': 'test_username',
            'email': 'test@email.com',
            'password1': 'register_test_password_007',
            'password2': 'register_test_password_007',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(User.objects.all()), 2)

    def test_LoginUser_get(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_LoginUser_post(self):
        response = self.client.post(reverse('login'), {
            'username': 'test_username_1',
            'password': 'test_password'
        })
        self.assertEqual(response.status_code, 302)

    def test_ConfirmEmailView(self):
        response = self.client.get(reverse('confirm_email'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/confirm_email.html')

    def test_InvalidVerifyView(self):
        response = self.client.get(reverse('invalid_verify'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/invalid_verify.html')

    def test_EmailVerify(self):
        response = self.client.get(reverse('verify_email', args=[1, 2]))
        self.assertEqual(response.status_code, 302)

    def test_payment_view_get(self):
        response = self.client.get(reverse('payment', args=[1]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'flights/payment.html')

    @patch('flights.views.send_ticket_to_email')
    def test_payment_view_post(self, mail_mock):
        mail_mock.return_data = None
        response = self.client.post(reverse('payment', args=[1]), data=self.post_data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/profile/tickets/')

        payment = Payment.objects.filter(user=self.user1, ticket=self.ticket)
        self.assertTrue(payment.exists())
        self.assertEqual(payment.first().price, str(int(self.ticket.price)))
        self.assertEqual(payment.first().cardholder_name, self.post_data['cardholder_name'])

    def test_payment_view_post_invalid_form(self):
        invalid_post_data = self.post_data.copy()
        invalid_post_data['card_number'] = '1234567890123456'  # Недопустимый номер карты

        response = self.client.post(f'/payment/{self.ticket.pk}/', data=invalid_post_data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'flights/payment.html')

        payment = Payment.objects.filter(user=self.user1, ticket=self.ticket)
        self.assertFalse(payment.exists())

    def test_get_profile_view(self):
        response = self.client.get(reverse('profile', args=[1]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(response, 'flights/profile.html')

    def test_ProfileTicketListView(self):
        response = self.client.get(reverse('profile_tickets'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(response, 'flights/profile_ticket_list.html')

    def test_change_profile_view_success(self):
        url = reverse('change_profile', args=[1])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], ChangeProfileForm)
        self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(response, 'flights/change_profile.html')

    def test_change_profile_view_post(self):
        url = reverse('change_profile', args=[1])
        response = self.client.post(url, {
            'username': 'newusername',
            'first_name': 'newfirstname',
            'last_name': 'newlastname',
            'email': 'newemail@example.com',
            'phone': '1234567890',
            'gender': User.Genders.MALE,
        })
        self.assertEqual(response.status_code, 302)
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.username, 'newusername')
        self.assertEqual(self.user1.first_name, 'newfirstname')
        self.assertEqual(self.user1.last_name, 'newlastname')
        self.assertEqual(self.user1.email, 'newemail@example.com')
        self.assertEqual(self.user1.phone, '1234567890')
        self.assertEqual(self.user1.gender, User.Genders.MALE)

    def test_change_profile_view_invalid_form(self):
        url = reverse('change_profile', args=[1])
        response = self.client.post(url, {
            'username': 'test_name',
            'first_name': 'тест',
            'last_name': 'тест',
            'email': '1',
            'phone': '7656"#45678',
            'gender': User.Genders.MALE,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(len(response.context['form'].errors), 4)

    def test_get_request(self):
        self.client.login(username='test_username_1', password='test_password')
        session = self.client.session
        session['data'] = self.session_data_booking
        session.save()
        response = self.client.get(reverse('confirm', args=[self.flight.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'flights/booking_confirmation.html')

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_post_request(self):
        self.client.login(username='test_username_1',
                          password='test_password')
        session = self.client.session
        session['data'] = self.session_data_booking
        session.save()

        response = self.client.post(reverse('confirm', args=[self.flight.id]), data=self.session_data_booking)

        self.assertEqual(response.status_code, 302)
        seat = Seat.objects.filter(row_letter='A', seat_number='1', seat_type=TextClassType.ECONOMY).first()
        self.assertTrue(Ticket.objects.filter(user=self.user1, seat=seat).exists())

    def test_invalid_form(self):
        self.client.login(username='test_username_1', password='test_password')
        session = self.client.session
        session['data'] = self.session_data_booking
        session.save()
        response = self.client.post(reverse('confirm', args=[self.flight.id]),
                                    data={'seat': ''})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'row_letter', 'This field is required.')
        self.assertFormError(response, 'form', 'seat_number', 'This field is required.')
        self.assertFormError(response, 'form', 'seat_type', 'This field is required.')

    def test_get_seat(self):
        # Тестирование GET-запроса
        self.client.login(username='test_username_1', password='test_password')
        session = self.client.session
        session['data'] = self.session_data_booking
        session.save()
        response = self.client.get(reverse('seat', args=[self.flight.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'flights/seat.html')

    def test_post_seat(self):
        seat_data = {
            'row_letter': 'B',
            'seat_number': '2',
            'seat_type': 'Economy',
            'extra': [1, 2],
            'flight': self.flight.id
        }
        self.client.login(username='test_username_1', password='test_password')
        response = self.client.post(reverse('seat', args=[self.flight.id]), data=seat_data)
        self.assertEqual(response.status_code, 302)

    def test_invalid_form_seat(self):
        self.client.login(username='test_username_1', password='test_password')
        session = self.client.session
        session['data'] = self.session_data_booking
        session.save()
        response = self.client.post(reverse('seat', args=[self.flight.id]),
                                    data={'row_letter': '', 'seat_number': '', 'seat_type': '',
                                          'flight': self.flight.id})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'row_letter', 'This field is required.')
        self.assertFormError(response, 'form', 'seat_number', 'This field is required.')
        self.assertFormError(response, 'form', 'seat_type', 'This field is required.')

    def test_invalid_more_errors_form_seat(self):
        for i in range(600):
            Ticket.objects.create(code=i, user=self.user1, flight=self.flight, seat=self.seat, task_id=i)
            self.flight.seats.add(self.seat)
        self.client.login(username='test_username_1', password='test_password')
        session = self.client.session
        session['data'] = self.session_data_booking
        session.save()
        response = self.client.post(reverse('seat', args=[self.flight.id]),
                                    data={'row_letter': self.seat.row_letter, 'seat_number': self.seat.seat_number,
                                          'seat_type': self.seat.seat_type,
                                          'flight': self.flight.id})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', None, 'This seat is already booked for the flight.')

    def test_no_economy_seats_left(self):
        self.flight.economy_seats = 0
        self.flight.save()

        self.client.login(username='test_username_1', password='test_password')
        session = self.client.session
        session['data'] = self.session_data_booking
        session.save()

        response = self.client.post(reverse('seat', args=[self.flight.id]),
                                    data={'row_letter': 'B', 'seat_number': 1, 'seat_type': TextClassType.ECONOMY,
                                          'flight': self.flight.id})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', None, 'There are no more seats available for economy class seats.')

    def test_no_first_seats_left(self):
        self.flight.first_class_seats = 0
        self.flight.save()

        self.client.login(username='test_username_1', password='test_password')
        session = self.client.session
        session['data'] = self.session_data_booking
        session.save()

        response = self.client.post(reverse('seat', args=[self.flight.id]),
                                    data={'row_letter': 'B', 'seat_number': 1, 'seat_type': TextClassType.FIRST,
                                          'flight': self.flight.id})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', None, 'There are no more seats available for a first class seats.')

    def test_no_business_seats_left(self):
        self.flight.business_seats = 0
        self.flight.save()

        self.client.login(username='test_username_1', password='test_password')
        session = self.client.session
        session['data'] = self.session_data_booking
        session.save()

        response = self.client.post(reverse('seat', args=[self.flight.id]),
                                    data={'row_letter': 'B', 'seat_number': 1, 'seat_type': TextClassType.BUSINESS,
                                          'flight': self.flight.id})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', None, 'There are no more seats available for business class seats.')

    def test_ticket_view(self):
        self.client.login(username='test_username_1', password='test_password')
        response = self.client.get(reverse('ticket', args=[self.ticket.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'flights/ticket.html')
        self.assertEqual(response.context['ticket'], self.ticket)

    def test_ticket_delete(self):
        self.client.login(username='test_username_1', password='test_password')

        initial_economy_seats = self.flight.economy_seats
        initial_business_seats = self.flight.business_seats
        initial_first_class_seats = self.flight.first_class_seats

        response = self.client.post(reverse('ticket', args=[self.ticket.id]), {'delete_ticket': True})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('profile_tickets'))

        with self.assertRaises(Ticket.DoesNotExist):
            Ticket.objects.get(id=self.ticket.id)

        self.flight.refresh_from_db()
        if self.ticket.seat.seat_type == TextClassType.ECONOMY:
            self.assertEqual(self.flight.economy_seats, initial_economy_seats + 1)
        elif self.ticket.seat.seat_type == TextClassType.BUSINESS:
            self.assertEqual(self.flight.business_seats, initial_business_seats + 1)
        else:
            self.assertEqual(self.flight.first_class_seats, initial_first_class_seats + 1)

    def test_about_view(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'flights/about.html')

    def test_pdf_view(self):
        response = self.client.get(reverse('pdf_view', args=[self.ticket.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_download_pdf(self):
        response = self.client.get(reverse('pdf_download', args=[self.ticket.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(response['Content-Disposition'], "attachment; filename='Invoice_12341231.pdf'")

    @patch('flights.views.send_ticket_to_email')
    def test_send_ticket(self, mock_send_ticket_to_email):
        mock_send_ticket_to_email.return_value = None
        response = self.client.get(reverse('send_ticket', args=[self.ticket.id]))
        self.assertEqual(response.url, reverse('ticket', args=[self.ticket.id]))
        mock_send_ticket_to_email.assert_called_once()

class TestMainPage(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group = Group.objects.create(name='test_group')
        cls.user = User.objects.create_user(username='testuser', password='testpassword')
        cls.user.groups.add(cls.group)
        cls.user.save()
        cls.airport = Airport.objects.create(name='Airport', code='ARP', city='test_city', country='Country_test')
        cls.aircraft = Aircraft.objects.create(model='Boeing 747', aircraft_type=AircraftTypes.BOEING, total_seats=500)
        cls.flight1 = Flight.objects.create(
            name='Test Flight 1',
            departure_time=timezone.make_aware(datetime(23, 12, 12, 0, 0, 0, 0)),
            arrival_time=timezone.make_aware(datetime(23, 12, 13, 0, 0, 0, 0)),
            aircraft=cls.aircraft,
            origin_airport=cls.airport,
            destination_airport=cls.airport,
            economy_seats=2,
            business_seats=2,
            first_class_seats=2,
            expire='ACTIVE')
        cls.flight2 = Flight.objects.create(
            name='Test Flight 2',
            departure_time=timezone.make_aware(datetime(23, 12, 14, 0, 0, 0, 0)),
            arrival_time=timezone.make_aware(datetime(23, 12, 15, 0, 0, 0, 0)),
            aircraft=cls.aircraft,
            origin_airport=cls.airport,
            destination_airport=cls.airport,
            economy_seats=2,
            business_seats=2,
            first_class_seats=2,
            expire='ACTIVE')


    def setUp(self):
        self.client.login(username='testuser', password='testpassword')

    def test_main_page_output(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Flight 1")
        self.assertContains(response, "Test Flight 2")

    def test_main_page_search(self):
        response = self.client.get(reverse('home'), {'search': 'Test Flight 1'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Flight 1")
        self.assertNotContains(response, "Test Flight 2")

