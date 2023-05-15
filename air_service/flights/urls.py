from django.urls import path

from flights.staff_views import StaffMainPageView, TicketStaffView, DeleteExtraView, CreateExtraView, ExtraListView, \
    FlightListView, FlightUpdateView, ExtraUpdateView, CreateFlightView, AircraftListView, \
    AircraftCreateView, FlightDeleteView, AircraftUpdateView, AircraftDeleteView, AirportListView, AirportCreateView, \
    AirportUpdateView, AirportDeleteView, AssignRoleView, UserListView
from flights.views import *

urlpatterns = [
    path("chat/<str:room_name>/", room, name="room"),
    path('', landing_page, name='landing_page'),
    path('flights/', MainPage.as_view(), name='home'),
    path('about/', AboutView.as_view(), name='about'),
    path('seat/flight/<int:flight_id>/', OrderSeatView.as_view(), name='seat'),
    path('save_price/', save_price, name='save_price'),
    path('seat/confirm/<int:flight_id>/', BookingConfirmView.as_view(), name='confirm'),
    path('payment/<int:ticket_id>/', PaymentView.as_view(), name='payment'),
    path('profile/<int:pk>/', ProfileView.as_view(), name='profile'),
    path('profile/tickets/', ProfileTicketListView.as_view(), name='profile_tickets'),
    path('profile/cnange_profile/<int:pk>/', ChangeProfileView.as_view(), name='change_profile'),
    path('profile/ticket/<int:pk>/', TicketView.as_view(), name='ticket'),

    # pdf views
    path('pdf_view/<int:ticket_id>/', ViewPDF.as_view(), name="pdf_view"),
    path('pdf_download/<int:ticket_id>/', DownloadPDF.as_view(), name="pdf_download"),
    path('send_ticket/<int:ticket_id>/', SendTicket.as_view(), name="send_ticket"),

    # staff views
    path('staff/', StaffMainPageView.as_view(), name='staff_ticket_list'),
    path('staff/ticket/<int:ticket_id>/', TicketStaffView.as_view(), name='staff_ticket'),

    path('staff/extra/', ExtraListView.as_view(), name='staff_extra_list'),
    path('staff/extra/creation/', CreateExtraView.as_view(), name='staff_extra_create'),
    path('staff/extra/update/<int:pk>/', ExtraUpdateView.as_view(), name='staff_extra_update'),
    path('staff/extra/delition/<int:pk>/', DeleteExtraView.as_view(), name='staff_extra_delete'),

    path('staff/flight/', FlightListView.as_view(), name='staff_flight_list'),
    path('staff/flight/creation/', CreateFlightView.as_view(), name='staff_flight_create'),
    path('staff/flight/update/<int:pk>/', FlightUpdateView.as_view(), name='staff_flight_update'),
    path('staff/flight/delition/<int:pk>/', FlightDeleteView.as_view(), name='staff_flight_delete'),

    path('staff/aircraft/', AircraftListView.as_view(), name='staff_aircraft_list'),
    path('staff/aircraft/creation', AircraftCreateView.as_view(), name='staff_aircraft_create'),
    path('staff/aircraft/update/<int:pk>/', AircraftUpdateView.as_view(), name='staff_aircraft_update'),
    path('staff/aircraft/delition/<int:pk>/', AircraftDeleteView.as_view(), name='staff_aircraft_delete'),

    path('staff/airport/', AirportListView.as_view(), name='staff_airport_list'),
    path('staff/airport/creation', AirportCreateView.as_view(), name='staff_airport_create'),
    path('staff/airport/update/<int:pk>/', AirportUpdateView.as_view(), name='staff_airport_update'),
    path('staff/airport/delition/<int:pk>/', AirportDeleteView.as_view(), name='staff_airport_delete'),

    path('assign-role/users/', UserListView.as_view(), name='user_list'),
    path('assign-role/users/user/<int:pk>/', AssignRoleView.as_view(), name='assign_role'),

    # registration urls
    path('register/', RegisterUser.as_view(), name='register'),
    path('registration/login/', LoginUser.as_view(), name='login'),
    path('registration/logout/', logout_user, name='logout'),
    path('verify_email/<uidb64>/<token>/', EmailVerify.as_view(), name='verify_email'),
    path('confirm_email/', ConfirmEmailView.as_view(template_name='registration/confirm_email.html'), name='confirm_email'),
    path('invalid_verify/', InvalidVerifyView.as_view(template_name='registration/invalid_verify.html'), name='invalid_verify'),

    ]

