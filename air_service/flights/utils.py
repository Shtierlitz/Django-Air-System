import os

from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied

from flights.models import *
from django.contrib.auth.tokens import default_token_generator as token_generator
from django.utils.http import urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import get_template
from django.db.models import Case, When, IntegerField, Value, Q, F

from io import BytesIO
from django.http import HttpResponse
from xhtml2pdf import pisa

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from django.utils import timezone
import channels.layers
from asgiref.sync import async_to_sync


def send_status_update(user_id, content):
    channel_layer = channels.layers.get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"status_updates_user_{user_id}",
        {
            "type": "send_status_update",
            "content": content
        }
    )


def send_email_with_pdf_attachment(subject, body, to_email, pdf_data):
    # Введите свои данные для отправки письма
    from_email = os.environ.get('EMAIL_HOST_USER')
    password = os.environ.get('EMAIL_HOST_PASSWORD')

    # Создание сообщения
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Добавление текста в письмо
    msg.attach(MIMEText(body, 'plain'))

    # Создание вложения PDF
    attachment = MIMEBase('application', 'octet-stream')
    attachment.set_payload(pdf_data)
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', 'attachment', filename='Ticket.pdf')
    msg.attach(attachment)

    # Отправка письма
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(from_email, password)
        server.send_message(msg)

    print(f'Email sent to {to_email}')


def send_ticket_to_email(template_src, to_email, subject, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        pdf_data = result.getvalue()
        body = 'Please print or download your ticket and don`t forget to present it' \
               ' to the Check-in manager before boarding..'
        send_email_with_pdf_attachment(subject, body, to_email, pdf_data)
        return None


def render_to_pdf(template_src, context_dict={}, to_email=None):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        pdf_data = result.getvalue()
        if to_email:
            # Настройте subject и body письма
            subject = 'Your Django Air Ticket'
            body = 'Please print or download your ticket and don`t forget to present it to the Check-in manager before boarding..'
            send_email_with_pdf_attachment(subject, body, to_email, pdf_data)
        return HttpResponse(pdf_data, content_type='application/pdf')
    return None


def send_email_verify(request, user):
    current_site = get_current_site(request)
    context = {
        'user': user,
        'domain': current_site.domain,
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "token": token_generator.make_token(user),
    }
    message = render_to_string(
        'registration/verify_email.html',
        context=context
    )
    email = EmailMessage(
        'Verify email',
        message,
        to=[user.email],
    )
    email.send()


def send_message(name, email, content, subject: str):
    text = get_template("registration/message.html")
    html = get_template("registration/message.html")
    context = {
        'name': name,
        'email': email,
        'content': content
    }
    subject = subject
    from_email = os.environ.get('EMAIL_HOST_USER')
    text_content = text.render(context)
    html_content = html.render(context)

    msg = EmailMultiAlternatives(subject, text_content, from_email, [os.environ.get('EMAIL_HOST_USER')])
    msg.attach_alternative(html_content, 'text/html')
    msg.send()


def get_one_flight(flight_id):
    flight = Flight.objects.get(pk=flight_id)
    return {
        'name': flight.name,
        'departure_time': flight.departure_time,
        'arrival_time': flight.arrival_time,
        'aircraft': flight.aircraft.aircraft_type,
        'origin_airport': [flight.origin_airport.name, flight.origin_airport.code, flight.origin_airport.city,
                           flight.origin_airport.country],
        'destination_airport': [flight.destination_airport.name, flight.destination_airport.code,
                                flight.destination_airport.city, flight.destination_airport.country],
        'total_seats': flight.economy_seats + flight.business_seats + flight.first_class_seats,
        'expire': flight.expire
    }


def get_flights(search_query=None) -> dict:
    flights = Flight.objects.all()
    res_dict = {}
    for flight in flights:
        # if search_query:
        if search_query and search_query.strip().lower() not in (
                flight.origin_airport.city.lower(), flight.destination_airport.city.lower()):
            continue  # пропускаем рейсы, не соответствующие условию поиска
        res_dict[flight.id] = get_one_flight(flight.id)
    # else:
    #     res_dict[flight.id] = get_one_flight(flight.id)
    sorted_dict = dict(sorted(res_dict.items(), key=lambda x: x[1]['departure_time']))
    return sorted_dict


def check_in_confirm_or_errors(form, check_in, ticket, form_invalid, request):
    if check_in == ticket.check_in:
        pass
    elif ticket.check_in == 'APPROVED' and check_in != ticket.check_in:
        form.add_error(None, "You cant change check in status after it was approved.")
        return form_invalid(form)
    else:
        ticket.check_in = check_in
        ticket.save()
        send_status_update(ticket.user.id, {"ticket_id": ticket.id, "check_in": ticket.check_in})
        check_in_message(request, ticket)


def check_in_message(request, ticket):
    subject = f'Ticket {ticket.code} - check in.'
    content = f"<p>Greetings our dear customer!</p>" \
              f"<p>Congratulations! You have been successfully checked in on board.</p>" \
              f"<p>You can now await for boarding permission in airports awaiting hall.</p>" \
              f"<p>Please do not miss yours boarding time.</p>" \
              f"<p>With best regards Check In Manger - {request.user.first_name} {request.user.last_name}."
    send_message(ticket.user.username, ticket.user.email, content, subject)


def onboard_message(request, ticket):
    subject = f'Ticket {ticket.code} - onboard.'
    content = f"<p>Greetings our dear customer!</p>" \
              f"<p>You have successfully completed your boarding check.</p>" \
              f"<p>Please go to the plane and follow the instructions of the flight attendants.</p>" \
              f"<p>From the whole crew we wish you - Fly to your dreams!</p>" \
              f"With Best Regards Boarding Manager - {request.user.first_name} {request.user.last_name}."
    send_message(ticket.user.username, ticket.user.email, content, subject)


def onboard_confirm_or_errors(form, onboard, check_in, ticket, form_invalid, request):
    if onboard == ticket.onboard:
        pass
    elif ticket.onboard == 'APPROVED' and onboard != ticket.onboard:
        form.add_error(None, "You cant change onboard status after it was approved.")
        return form_invalid(form)
    elif onboard == 'APPROVED' and ticket.check_in == 'NOT APPROVED' and check_in == 'NOT APPROVED':
        form.add_error(None, "You cant change onboard status before it was approved by checkin manager.")
        return form_invalid(form)
    else:
        ticket.onboard = onboard
        ticket.save()
        send_status_update(ticket.user.id, {"ticket_id": ticket.id, "onboard": ticket.onboard})
        onboard_message(request, ticket)


def clean_or_errors(cleaned_data, aircraft, add_error):
    economy_seats = cleaned_data['economy_seats']
    business_seats = cleaned_data['business_seats']
    first_class_seats = cleaned_data['first_class_seats']
    departure_time = cleaned_data['departure_time']
    arrival_time = cleaned_data['arrival_time']

    today = timezone.make_aware(datetime.datetime.today())
    today = today.replace(microsecond=0)
    if departure_time <= today:
        add_error('departure_time',
                  "The departure time must not be earlier than"
                  " the next day from the creation of the flight.")

    if arrival_time < departure_time or arrival_time <= timezone.make_aware(datetime.datetime.today()):
        add_error('arrival_time',
                  "The arrival time must not be earlier than"
                  " the next day from the creation of the flight and not earlier then departure time.")

    total = economy_seats + business_seats + first_class_seats
    if total > aircraft.total_seats:
        add_error('first_class_seats',
                  "The number of seats must not exceed"
                  " the total number of seats on the aircraft.")
        add_error('business_seats',
                  "The number of seats must not exceed"
                  " the total number of seats on the aircraft.")
        add_error('economy_seats',
                  "The number of seats must not exceed"
                  " the total number of seats on the aircraft.")


class BaseDataMixin:
    title = ''
    permission = None

    def get_user_context(self, **kwargs):
        context = kwargs
        group = self.request.user.groups.all().first()
        context['group'] = group
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_user_context())
        context['title'] = self.title
        return context

    def dispatch(self,  request, *args, **kwargs):
        if self.permission is not None:
            if not request.user.has_perm(self.permission):
                raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)


class FlightMixin:
    title = ''
    permission = None

    def get_user_context(self, **kwargs):
        context = kwargs
        group = self.request.user.groups.all().first()
        context['group'] = group
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_user_context())
        context['search'] = True
        search_query = self.request.GET.get('search')  # получаем значение search из GET-запроса
        flights = context['object_list']
        flight_list = []
        if search_query:
            search_query = search_query.strip()
            for flight in flights:
                if search_query.upper() == flight.name.upper() \
                        or search_query.lower() == flight.origin_airport.city.lower() \
                        or search_query.lower() == flight.destination_airport.city.lower() \
                        or search_query.lower() == flight.aircraft.aircraft_type.lower():
                    flight_list.append(flight)
            if len(flight_list) == 0:
                context['not_found'] = True
            else:
                context['object_list'] = flight_list
        return context

    def dispatch(self,  request, *args, **kwargs):
        if self.permission is not None:
            if not request.user.has_perm(self.permission):
                raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Flight.objects.annotate(
            is_active=Case(
                When(expire=Expiring.ACTIVE, then=1),
                default=0,
                output_field=IntegerField(),
            ),
            total_seats=F('economy_seats') + F('business_seats') + F('first_class_seats'),
            has_seats_left=Case(
                When(total_seats__gt=0, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).annotate(
            priority=Case(
                When(Q(is_active=1) & Q(has_seats_left=1), then=Value(2)),
                When(Q(is_active=1) & Q(has_seats_left=0), then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by('-priority', 'departure_time', '-aircraft__total_seats')
        return queryset


    # def search_flights(self, search_query):
    #     query = Flight.objects.all()
    #     flights = {}
    #     for i in query:
    #         if i.code == search_query.strip().upper():
    #             flights.append(i)
    #         elif i.


# def get_extra_all():
#     extras = Extra.objects.filter(available=True)
#     extra_tuple = () #('', '---------'),
#     for i, e in enumerate(extras):
#         inner_tuple = (e.price, e)
#         extra_tuple += (inner_tuple,)
#     return extra_tuple
