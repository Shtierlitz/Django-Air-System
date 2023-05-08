from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, RequestFactory
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal

from flights.models import Ticket, Flight, Aircraft, AircraftTypes, Airport, Extra, Seat, TextClassType, Expiring, \
    Payment
from flights.views import PaymentView

User = get_user_model()


class TestViews(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user1 = User.objects.create_user(username='test_username_1', first_name='test_first_name_1',
                                              last_name='test_last_name_1',
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
            price=100,
        )
        self.seat = Seat.objects.create(row_letter=Seat.SeatRows.A, seat_number=1, seat_type=TextClassType.FIRST)
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
            'cardholder_name': 'Test User',
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


    def test_payment_view_post(self):
        response = self.client.post(reverse('payment', args=[1]), data=self.post_data)
        print(response.content.decode())

        # Проверьте статус ответа и перенаправление после успешной оплаты
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/profile_tickets/')  # Замените на соответствующий путь для успешной оплаты

        # Проверьте, что платеж был успешно создан и связан с билетом
        payment = Payment.objects.filter(user=self.user1, ticket=self.ticket)
        self.assertTrue(payment.exists())
        self.assertEqual(payment.first().price, self.ticket.price)
        self.assertEqual(payment.first().cardholder_name, self.post_data['cardholder_name'])

    # def test_payment_view_post_invalid_form(self):
    #     # Измените начальные данные для отправки недопустимой формы
    #     invalid_post_data = self.post_data.copy()
    #     invalid_post_data['card_number'] = '1234567890123456'  # Недопустимый номер карты
    #
    #     response = self.client.post(f'/payment/{self.ticket.pk}/', data=invalid_post_data)
    #
    #     # Проверьте статус ответа и убедитесь, что пользователь остается на странице оплаты
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'flights/payment.html')
    #
    #     # Убедитесь, что платеж не был создан
    #     payment = Payment.objects.filter(user=self.user, ticket=self.ticket)
    #     self.assertFalse(payment.exists())
