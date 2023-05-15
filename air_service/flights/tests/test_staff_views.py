# air_service/flights/tests/test_staff_views.py

from datetime import datetime
from unittest.mock import patch, Mock

from django.test import Client, TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import Group, Permission
from django.test import override_settings

from flights.models import User, Aircraft, Flight, Seat, Extra, AircraftTypes, Airport, Ticket, Expiring, TextClassType
from django.utils import timezone
from decimal import Decimal

from flights.staff_forms import FlightCreateForm


class TestStaffViews(TestCase):

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
        self.ticket_2 = Ticket.objects.create(code='CODE_2',
                                              status='PAID',
                                              user=self.user1,
                                              flight=self.flight,
                                              price=Decimal('100.00'),
                                              seat=self.seat,
                                              booking_date=timezone.make_aware(datetime(23, 12, 12, 0, 0, 0, 0)),
                                              check_in=Ticket.Checking.NOT_APPROVED,
                                              onboard=Ticket.Checking.NOT_APPROVED,
                                              expire=Expiring.ACTIVE
                                              )
        group = Group.objects.create(name='test_group')
        permission1 = Permission.objects.get(codename='can_approve_check_in')
        permission2 = Permission.objects.get(codename='can_approve_onboard')
        permission3 = Permission.objects.get(codename='can_manage_extras')
        permission4 = Permission.objects.get(codename='can_manage_flights')
        group.permissions.add(permission1, permission2, permission3, permission4)
        self.user1.groups.add(group)

    # def test_StaffMainPageView_output(self):
    #     response = self.client.get(reverse('staff_ticket_list'))
    #     self.assertEqual(response.status_code, 200)
    #     self.assertContains(response, "CODE")
    #     self.assertContains(response, "CODE_2")
    #
    # def test_StaffMainPageView_search(self):
    #     response = self.client.get(reverse('staff_ticket_list'), {'search': 'CODE'})
    #     self.assertEqual(response.status_code, 200)
    #     self.assertContains(response, "CODE")
    #     self.assertNotContains(response, "CODE_2")
    #
    # def test_TicketStaffView_get(self):
    #     response = self.client.get(reverse('staff_ticket', args=[self.ticket.id]))
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed('flights/staff/ticket.html')
    #
    # def test_TicketStaffView_post_unpaid(self):
    #     data = {
    #         'check_in': 'APPROVED'
    #     }
    #     response = self.client.post(reverse('staff_ticket', args=[self.ticket.id]), data=data)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertFormError(response, 'form', None, 'You cant approve an unpaid ticket.')
    #
    # # @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    # # @patch('flights.utils.send_status_update')
    # # @patch('flights.utils.onboard_message')
    # def test_TicketStaffView_post_not_checkin(self):
    #     # mock_message.return_value = None
    #     # status_message.return_value = None
    #     data = {
    #         'check_in': 'NOT APPROVED',
    #         'onboard': 'APPROVED'
    #     }
    #     response = self.client.post(reverse('staff_ticket', args=[self.ticket_2.id]), data=data)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertFormError(response, 'form', None,
    #                          'You cant change onboard status before it was approved by checkin manager.')
    #
    # def test_TicketStaffView_post_not_cant_change_check_in_and_onboard(self):
    #     self.ticket_2.check_in = Ticket.Checking.APPROVED
    #     self.ticket_2.onboard = Ticket.Checking.APPROVED
    #     self.ticket_2.save()
    #     data = {
    #         'check_in': 'NOT APPROVED',
    #         'onboard': 'NOT APPROVED'
    #     }
    #     response = self.client.post(reverse('staff_ticket', args=[self.ticket_2.id]), data=data)
    #     self.assertEqual(response.status_code, 200)
    #     expected_errors = [
    #         "You cant change check in status after it was approved.",
    #         "You cant change onboard status after it was approved.",
    #     ]
    #     self.assertCountEqual(response.context['form'].non_field_errors(), expected_errors)
    #
    # @patch('flights.utils.send_status_update')
    # def test_TicketStaffView_post_not_cant_change_check_in(self, status_message):
    #     status_message.return_value = None
    #     self.ticket_2.check_in = Ticket.Checking.APPROVED
    #     self.ticket_2.save()
    #     data = {
    #         'check_in': Ticket.Checking.NOT_APPROVED,
    #     }
    #     response = self.client.post(reverse('staff_ticket', args=[self.ticket_2.id]), data=data)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertFormError(response, 'form', None,
    #                          'You cant change check in status after it was approved.')
    #
    # @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    # @patch('flights.utils.send_status_update')
    # def test_user_has_permission_to_change_check_in_and_onboard_status(self, status_message):
    #     status_message.return_value = None
    #
    #     data = {
    #         'check_in': Ticket.Checking.APPROVED,
    #         'onboard': Ticket.Checking.APPROVED,
    #     }
    #     response = self.client.post(reverse('staff_ticket', args=[self.ticket_2.id]), data=data)
    #     self.assertEqual(response.status_code, 302)
    #
    #     self.ticket_2.refresh_from_db()
    #     self.assertEqual(self.ticket_2.check_in, Ticket.Checking.APPROVED)
    #     self.assertEqual(self.ticket_2.onboard, Ticket.Checking.APPROVED)
    #
    # @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    # @patch('flights.utils.send_status_update')
    # def test_user_does_not_have_permission_to_change_check_in_status(self, status_message):
    #     status_message.return_value = None
    #     self.user1.groups.clear()
    #     self.user1.user_permissions.add(Permission.objects.get(codename='can_approve_onboard'))
    #     data = {
    #         'check_in': Ticket.Checking.APPROVED,
    #     }
    #     response = self.client.post(reverse('staff_ticket', args=[self.ticket_2.id]), data=data)
    #     self.ticket_2.refresh_from_db()
    #     self.assertEqual(self.ticket_2.check_in, Ticket.Checking.NOT_APPROVED)
    #     self.assertFormError(response, 'form', None, 'You do not have permission to change the check-in status.')
    #
    # @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    # @patch('flights.utils.send_status_update')
    # def test_user_does_not_have_permission_to_change_onboard_status(self, status_message):
    #     status_message.return_value = None
    #     self.user1.groups.clear()
    #     self.user1.user_permissions.add(Permission.objects.get(codename='can_approve_check_in'))
    #     data = {
    #         'onboard': Ticket.Checking.APPROVED,
    #     }
    #     response = self.client.post(reverse('staff_ticket', args=[self.ticket_2.id]), data=data)
    #     self.ticket_2.refresh_from_db()
    #     self.assertEqual(self.ticket_2.onboard, Ticket.Checking.NOT_APPROVED)
    #     self.assertFormError(response, 'form', None, 'You do not have permission to change the onboard status.')
    #
    # def test_ExtraListView(self):
    #     response = self.client.get(reverse('staff_extra_list'))
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'flights/staff/extra/extra_list.html')
    #     self.assertEqual(len(response.context['object_list']), 3)
    #
    # def test_CreateExtraView(self):
    #     data = {
    #         'name': 'test_extra',
    #         'description': 'test_description',
    #         'available': True,
    #         'price': 100.0
    #     }
    #     response = self.client.post(reverse('staff_extra_create'), data=data)
    #     self.assertEqual(len(Extra.objects.all()), 4)
    #     self.assertRedirects(response, '/staff/extra/', status_code=302)
    #     self.assertTrue(Extra.objects.filter(name='test_extra', description='test_description').exists())
    #
    # def test_CreateExtraView_empty(self):
    #     data = {
    #         'name': '',
    #         'description': '',
    #         'available': True,
    #         'price': ''
    #     }
    #     response = self.client.post(reverse('staff_extra_create'), data=data)
    #     self.assertFormError(response, 'form', 'name', 'This field is required.')
    #     self.assertFormError(response, 'form', 'description', 'This field is required.')
    #     self.assertFormError(response, 'form', 'price', 'This field is required.')
    #     form = response.context['form']
    #     errors = form.errors
    #     self.assertEqual(len(errors), 3)
    #
    # def test_ExtraUpdateView(self):
    #     data = {
    #         'name': 'Updated Extra',
    #         'description': 'Updated description',
    #         'available': False,
    #         'price': 200
    #     }
    #     response = self.client.post(reverse('staff_extra_update', kwargs={'pk': self.extra.pk}), data=data)
    #
    #     self.assertEqual(response.status_code, 302)
    #     self.extra.refresh_from_db()
    #     self.assertEqual(self.extra.name, 'Updated Extra')
    #     self.assertEqual(self.extra.description, 'Updated description')
    #     self.assertEqual(self.extra.available, False)
    #     self.assertEqual(self.extra.price, 200)
    #
    # def test_ExtraUpdateView_invalid(self):
    #     data = {
    #         'name': '',  # имя не может быть пустым
    #         'description': '',
    #         'available': True,
    #         'price': -1  # цена не может быть отрицательной
    #     }
    #
    #     response = self.client.post(reverse('staff_extra_update', kwargs={'pk': self.extra.pk}), data=data)
    #
    #     self.assertEqual(response.status_code, 200)
    #     form = response.context['form']
    #     self.assertTrue(form.errors)
    #     self.extra.refresh_from_db()
    #     self.assertEqual(self.extra.name, 'EXTRA')
    #     self.assertEqual(self.extra.description, 'EXTRA_DESCRIPTION')
    #     self.assertEqual(self.extra.available, True)
    #     self.assertEqual(self.extra.price, 100.0)
    #
    # def test_DeleteExtraView_url_exists_at_desired_location(self):
    #     response = self.client.get(f'/staff/extra/delition/{self.extra.id}/')
    #     self.assertEqual(response.status_code, 200)
    #
    # def test_DeleteExtraView_url_accessible_by_name(self):
    #     response = self.client.get(reverse('staff_extra_delete', args=[self.extra.id]))
    #     self.assertEqual(response.status_code, 200)
    #
    # def test_DeleteExtraView_uses_correct_template(self):
    #     response = self.client.get(reverse('staff_extra_delete', args=[self.extra.id]))
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'flights/staff/extra/delete_extra.html')
    #
    # def test_DeleteExtraView_post_request_deletes_object(self):
    #     response = self.client.post(reverse('staff_extra_delete', args=[self.extra.id]))
    #     self.assertEqual(response.status_code, 302)
    #     with self.assertRaises(Extra.DoesNotExist):
    #         Extra.objects.get(id=self.extra.id)
    #
    # def test_DeleteExtraView_returns_404_for_nonexistent_object(self):
    #     response = self.client.get(reverse('staff_extra_delete', args=[9999]))
    #     self.assertEqual(response.status_code, 404)
    #
    # def test_FlightListView(self):
    #     response = self.client.get(reverse('staff_flight_list'))
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'flights/staff/flight/flight_list.html')
    #     self.assertEqual(len(response.context['object_list']), 1)
    #
    # @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    # @patch('flights.staff_forms.clean_or_errors')
    # @patch('flights.staff_forms.flight_expiration_task.apply_async', return_value=Mock(id='mock-task-id'))
    # def test_CreateFlightView(self, mock_data, task_data):
    #     task_data.return_value = None
    #     mock_data.return_value = None
    #     data = {
    #         'name': 'test_flight',
    #         'aircraft': self.aircraft.id,
    #         'origin_airport': self.airport.id,
    #         'destination_airport': self.airport.id,
    #         'economy_seats': 10,
    #         'business_seats': 10,
    #         'first_class_seats': 10,
    #         'departure_time': '2023-01-01T10:00',
    #         'arrival_time': '2023-01-01T12:00'
    #     }
    #     response = self.client.post(reverse('staff_flight_create'), data=data)
    #     form = FlightCreateForm(data=data)
    #     self.assertTrue(form.is_valid())
    #     self.assertEqual(len(Flight.objects.all()), 2)
    #     self.assertRedirects(response, '/staff/flight/', status_code=302)
    #     self.assertTrue(Flight.objects.filter(name='test_flight', economy_seats=10).exists())
    #
    # def test_CreateFlightView_empty(self):
    #     data = {
    #         'name': '',
    #         'aircraft': '',
    #         'origin_airport': '',
    #         'destination_airport': '',
    #         'economy_seats': '',
    #         'business_seats': '',
    #         'first_class_seats': '',
    #         'departure_time': '',
    #         'arrival_time': ''
    #     }
    #     response = self.client.post(reverse('staff_flight_create'), data=data)
    #     self.assertFormError(response, 'form', 'name', 'This field is required.')
    #     self.assertFormError(response, 'form', 'aircraft', 'This field is required.')
    #     self.assertFormError(response, 'form', 'origin_airport', 'This field is required.')
    #     self.assertFormError(response, 'form', 'destination_airport', 'This field is required.')
    #     self.assertFormError(response, 'form', 'economy_seats', 'This field is required.')
    #     self.assertFormError(response, 'form', 'business_seats', 'This field is required.')
    #     self.assertFormError(response, 'form', 'first_class_seats', 'This field is required.')
    #     self.assertFormError(response, 'form', 'departure_time', 'This field is required.')
    #     self.assertFormError(response, 'form', 'arrival_time', 'This field is required.')
    #     form = response.context['form']
    #     errors = form.errors
    #     self.assertEqual(len(errors), 9)

    # @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    # @patch('flights.staff_forms.flight_expiration_task.apply_async', return_value=Mock(id='mock-task-id'))
    # def test_CreateFlightView_false_data(self, task_data):
    #     task_data.return_value = None
    #     self.aircraft.total_seats = 10
    #     self.aircraft.save()
    #     data = {
    #         'name': 'TEST',
    #         'aircraft': self.aircraft.id,
    #         'origin_airport': self.airport.id,
    #         'destination_airport': self.airport.id,
    #         'economy_seats': 10,
    #         'business_seats': 10,
    #         'first_class_seats': 10,
    #         'departure_time': '2023-01-01T10:00',
    #         'arrival_time': '2023-01-01T10:00',
    #     }
    #     response = self.client.post(reverse('staff_flight_create'), data=data)
    #     form = FlightCreateForm(data=data)
    #     self.assertFalse(form.is_valid())
    #     self.assertFormError(response, 'form', 'arrival_time',
    #                          "The arrival time must not be earlier than"
    #               " the next day from the creation of the flight and not earlier then departure time.")
    #     self.assertFormError(response, 'form', 'departure_time',
    #                          "The departure time must not be earlier than"
    #               " the next day from the creation of the flight.")
    #     self.assertFormError(response, 'form', 'first_class_seats',
    #                          "The number of seats must not exceed"
    #               " the total number of seats on the aircraft.")
    #     self.assertFormError(response, 'form', 'business_seats',
    #                          "The number of seats must not exceed"
    #               " the total number of seats on the aircraft.")
    #     self.assertFormError(response, 'form', 'economy_seats',
    #                          "The number of seats must not exceed"
    #               " the total number of seats on the aircraft.")
    #     form = response.context['form']
    #     errors = form.errors
    #     self.assertEqual(len(errors), 5)

    # def test_FlightUpdateView(self):
    #     response = self.client.get(reverse('staff_flight_update', args=[self.flight.id]))
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'flights/staff/flight/flight_update.html')

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch('flights.staff_forms.clean_or_errors')
    @patch('flights.staff_forms.flight_expiration_task.apply_async', return_value=Mock(id='mock-task-id'))
    def test_FlightUpdateView(self, mock_data, task_data):
        task_data.return_value = None
        mock_data.return_value = None
        self.aircraft.total_seats = 30
        self.aircraft.save()
        self.client.login(username='test_username_1', password='test_password')
        data = {
            'name': 'test_flight',
            'aircraft': self.aircraft.id,
            'origin_airport': self.airport.id,
            'destination_airport': self.airport.id,
            'economy_seats': 10,
            'business_seats': 10,
            'first_class_seats': 10,
            'departure_time': '2023-05-14T10:00',
            'arrival_time': '2023-05-15T12:00'
        }
        response = self.client.post(reverse('staff_flight_update', args=[self.flight.id]), data=data)
        form = FlightCreateForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/staff/flight/', status_code=302)
        flight = Flight.objects.get(pk=1)
        self.assertEqual(flight.name, 'test_flight')

