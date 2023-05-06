from django.contrib import messages
from django.contrib.auth import logout, get_user_model, login, authenticate
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, CreateView, ListView, DetailView, FormView


from django.conf import settings
from flights.forms import RegisterUserForm, LoginUserForm, TicketConfirmForm, SeatForm, \
    StripeForm, ChangeProfileForm
from flights.models import *
from flights.utils import token_generator, get_one_flight, render_to_pdf, BaseDataMixin, send_ticket_to_email, \
    FlightMixin
from flights.utils import get_flights, send_email_verify
from django.utils.http import urlsafe_base64_decode
import stripe
from stripe.error import CardError

User = get_user_model()

stripe.api_key = settings.STRIPE_SECRET_KEY


def room(request, room_name):
    return render(request, "flights/room.html", {"room_name": room_name})


def landing_page(request):
    return render(request, 'flights/landing_page.html')


class PaymentView(LoginRequiredMixin, BaseDataMixin, View):
    template_name = 'flights/payment.html'
    form_class = StripeForm
    login_url = 'login'
    title = 'Payment'

    def get(self, request, ticket_id):
        context = self.get_user_context()
        ticket = Ticket.objects.get(pk=ticket_id)
        context['user'] = request.user
        context['ticket'] = ticket
        context['form'] = self.form_class(context=context)
        context['price'] = ticket.price
        context['flight'] = get_one_flight(ticket.flight.id)
        context['flight_id'] = ticket.flight.id
        context['seat'] = ticket.seat
        context['extras'] = self.request.session.get('extras')

        return render(request, self.template_name, context=context)

    def post(self, request, ticket_id):
        context = self.get_user_context()
        ticket = Ticket.objects.get(pk=ticket_id)
        context['ticket'] = ticket
        context['current_year'] = str(datetime.datetime.now().year)[2:]
        context['user'] = request.user
        form = self.form_class(request.POST, context=context)
        context['form'] = form
        context['flight'] = get_one_flight(ticket.flight.id)
        context['flight_id'] = ticket.flight.id
        context['extras'] = self.request.session.get('extras')
        context['seat'] = ticket.seat
        card_number = request.POST['card_number']
        exp_month = request.POST['exp_month']
        exp_year = request.POST['exp_year']
        cvc = request.POST['cvc']
        cardholder_name = request.POST['cardholder_name']
        price = int(ticket.price)
        context['price'] = price

        if form.is_valid(request):
            # Создайте токен Stripe
            try:
                token = stripe.Token.create(
                    card={
                        "number": card_number,
                        "exp_month": exp_month,
                        "exp_year": exp_year,
                        "cvc": cvc,
                        "name": cardholder_name,
                    },
                )
            except stripe.error.InvalidRequestError as e:
                user_message = e.user_message if e.user_message else "Invalid request error"
                messages.error(request, user_message)
                return render(request, self.template_name, context=context)
            except stripe.error.CardError as e:
                user_message = e.user_message if e.user_message else "Card error"
                messages.error(request, user_message)
                return render(request, self.template_name, context=context)
            except Exception as e:
                messages.error(request, "Unknown error: {}".format(e))
                return render(request, self.template_name, context=context)

            # Создайте платеж
            try:
                charge = stripe.Charge.create(
                    amount=price,  # Сумма в центах
                    currency='usd',
                    source=token['id'],
                    description='Описание оплаты',
                )
                ticket = form.save()

                # сохранить информацию о платеже в базу данных
                Payment.objects.create(user=request.user,
                                       ticket=ticket,
                                       price=price,
                                       cardholder_name=cardholder_name)

                # соответствующее уведомление об успешной оплате
                data = {
                    'ticket': ticket,
                    'current_year': datetime.datetime.now().year,
                    'flight': get_one_flight(ticket.flight.id)
                }
                subject = 'Payment successful!'
                send_ticket_to_email('flights/pdf_template/pdf_template.html', request.user.email, subject, data)

                # Перенаправь пользователя на страницу успешной оплаты или предоставь
                return redirect('profile_tickets')

            except stripe.error.InvalidRequestError as e:
                user_message = e.user_message if e.user_message else "Invalid request error"
                messages.error(request, user_message)
                return render(request, self.template_name, context=context)
            except stripe.error.CardError as e:
                user_message = e.user_message if e.user_message else "Card error"
                messages.error(request, user_message)
                return render(request, self.template_name, context=context)
            except Exception as e:
                messages.error(request, "Unknown error: {}".format(e))
                return render(request, self.template_name, context=context)
        print('not valid')
        return render(request, self.template_name, context=context)


class ProfileView(LoginRequiredMixin, BaseDataMixin, DetailView):
    model = User
    login_url = 'login'
    template_name = 'flights/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_user_context())
        context['user'] = get_object_or_404(User, pk=self.request.user.pk)
        context['title'] = f"Profile {self.request.user}"
        context['tickets'] = Ticket.objects.filter(user=self.request.user)
        return context


class ProfileTicketListView(LoginRequiredMixin, BaseDataMixin, ListView):
    model = Ticket
    login_url = 'login'
    template_name = 'flights/profile_ticket_list.html'
    context_object_name = 'tickets'
    title = 'My tickets'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user=self.request.user)


class ChangeProfileView(LoginRequiredMixin, BaseDataMixin, FormView):
    model = User
    login_url = 'login'
    template_name = 'flights/change_profile.html'
    form_class = ChangeProfileForm
    success_url = None

    def get_context_data(self, form=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_user_context())
        context['user'] = get_object_or_404(User, pk=self.request.user.pk)
        context['title'] = f"Change profile {self.request.user}"
        context['form'] = form if form else self.form_class()
        return context

    def form_valid(self, form):
        user = self.request.user
        username = form.cleaned_data['username'] or user.username
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        email = form.cleaned_data['email']
        phone = form.cleaned_data['phone']
        gender = form.cleaned_data['gender']

        if User.objects.filter(username=username).exclude(pk=user.pk).exists():
            form.add_error('username', "User with this User name already exists.")
            return self.form_invalid(form)

        user.username = username
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if email:
            user.email = email
        if phone:
            user.phone = phone
        if gender:
            user.gender = gender

        user.save()
        self.success_url = reverse_lazy('profile', kwargs={'pk': self.request.user.id })
        return super().form_valid(form)

    def form_invalid(self, form):
        print('invalid')
        context = self.get_context_data(form=form)
        return self.render_to_response(context)


class BookingConfirmView(LoginRequiredMixin, BaseDataMixin, FormView):
    model = Ticket
    form_class = TicketConfirmForm
    template_name = 'flights/booking_confirmation.html'
    login_url = 'login'
    title = "Confirm a ticket"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_user_context())
        data = self.request.session.get('data')
        context['flight'] = get_one_flight(self.kwargs['flight_id'])
        context['flight_id'] = self.kwargs['flight_id']
        context['user'] = self.request.user
        price = int(float(self.request.session.get('price')))
        context['price'] = price
        extras = data.get('extras')
        context['extras'] = [Extra.objects.get(pk=i) for i in extras]
        context['row_letter'] = data.get('row_letter')
        context['seat_number'] = data.get('seat_number')
        context['seat_type'] = data.get('seat_type')
        return context

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def form_valid(self, form):
        seat = form.cleaned_data.get('seat')
        self.request.session['data'] = {'seat': seat}
        form.save_ticket()
        self.success_url = reverse_lazy('profile_tickets')
        return super().form_valid(form)


class OrderSeatView(LoginRequiredMixin, BaseDataMixin, FormView):
    model = Seat
    form_class = SeatForm
    template_name = 'flights/seat.html'
    login_url = 'login'
    success_url = None
    title = "Choose a seat"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_user_context())
        context['flight'] = get_one_flight(self.kwargs['flight_id'])
        context['flight_id'] = self.kwargs['flight_id']
        context['user'] = self.request.user
        context['price'] = 100
        form = self.form_class()
        context['seat'] = form
        context['zipped_extras'] = zip(form['extra'].field.queryset, form['extra'])
        return context

    def form_invalid(self, form):
        context = self.get_context_data()
        context['seat'] = form
        return render(self.request, self.template_name, context)

    def form_valid(self, form):
        cleaned_data = form.cleaned_data
        extras = cleaned_data['extra']
        extras_serializable = [extra.pk for extra in extras]

        self.request.session['data'] = {
            'row_letter': cleaned_data['row_letter'],
            'extras': extras_serializable,
            'seat_number': cleaned_data['seat_number'],
            'seat_type': cleaned_data['seat_type'],
        }

        self.success_url = reverse_lazy('confirm', kwargs={'flight_id': self.kwargs['flight_id']})
        return super().form_valid(form)


def save_price(request):
    if request.method == 'POST':
        price = request.POST.get('price', None)
        if price is not None:
            request.session['price'] = price
            return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})


class TicketView(LoginRequiredMixin, BaseDataMixin, DetailView):
    model = Ticket
    template_name = 'flights/ticket.html'
    context_object_name = 'ticket'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_user_context())
        ticket = self.get_object()
        context['flight'] = get_one_flight(ticket.flight.id)
        context['flight_id'] = ticket.flight.id
        context['title'] = f'Ticket {ticket.code}'
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(pk=self.kwargs['pk'])

    def post(self, request, *args, **kwargs):
        if 'delete_ticket' in request.POST:
            ticket = self.get_object()
            ticket.flight.seats.remove(ticket.seat)
            ticket.flight.save()
            if ticket.seat.seat_type == TextClassType.ECONOMY:
                ticket.flight.economy_seats += 1

            elif ticket.seat.seat_type == TextClassType.BUSINESS:
                ticket.flight.business_seats += 1

            else:
                ticket.flight.first_class_seats += 1
            ticket.flight.users.remove(request.user.id)
            ticket.flight.save()
            ticket.delete()
            return redirect(reverse('profile'))


class AboutView(BaseDataMixin, TemplateView):
    template_name = 'flights/about.html'
    title = 'About Us'


class MainPage(FlightMixin, ListView):
    model = Flight
    template_name = 'flights/index.html'
    title = "Django Air System"
    paginate_by = 15


class RegisterUser(BaseDataMixin, CreateView):
    form_class = RegisterUserForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')
    title = "Registration"

    def form_valid(self, form):
        # Дополнительные действия перед сохранением формы
        user = form.save(commit=False)
        user.email = form.cleaned_data['email']
        user.set_password(form.cleaned_data['password1'])
        user.save()
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        # Отправить пользователю электронное письмо для подтверждения адреса электронной почты
        send_email_verify(self.request, user)
        # Перейти на страницу подтверждения адреса электронной почты
        return redirect('confirm_email')


class LoginUser(BaseDataMixin, LoginView):
    form_class = LoginUserForm
    template_name = 'registration/login.html'
    title = 'Sign in'


class ConfirmEmailView(BaseDataMixin, TemplateView):
    template_name = 'registration/confirm_email.html'
    title = "Confirm email"


class InvalidVerifyView(BaseDataMixin, TemplateView):
    template_name = 'registration/invalid_verify.html'
    title = "Invalid verify"


class EmailVerify(View):
    def get(self, request, uidb64, token):
        user = self.get_user(uidb64)

        if user is not None and token_generator.check_token(user, token):
            user.email_verify = True
            user.save()

            # Указание аутентификационного бэкенда перед вызовом login()
            backend = ModelBackend()
            user.backend = f'{backend.__module__}.{backend.__class__.__name__}'
            login(request, user)
            return redirect('home')
        return redirect('invalid_verify')

    @staticmethod
    def get_user(uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (
                TypeError,
                ValueError,
                OverflowError,
                User.DoesNotExist,
                ValidationError,
        ):
            user = None
        return user


class ViewPDF(View):
    """Opens up page as PDF"""

    def get(self, request, ticket_id, *args, **kwargs):
        ticket = Ticket.objects.get(pk=ticket_id)
        data = {
            'ticket': ticket,
            'current_year': datetime.datetime.now().year,
            'flight': get_one_flight(ticket.flight.id)
        }
        pdf = render_to_pdf('flights/pdf_template/pdf_template.html', data)
        return HttpResponse(pdf, content_type='application/pdf')


class DownloadPDF(View):
    """Automatically downloads to PDF file"""

    def get(self, request, ticket_id, *args, **kwargs):
        ticket = Ticket.objects.get(pk=ticket_id)
        data = {
            'ticket': ticket,
            'current_year': datetime.datetime.now().year,
            'flight': get_one_flight(ticket.flight.id)
        }
        pdf = render_to_pdf('flights/pdf_template/pdf_template.html', data)

        response = HttpResponse(pdf, content_type='application/pdf')
        filename = "Invoice_%s.pdf" % ("12341231")
        content = "attachment; filename='%s'" % (filename)
        response['Content-Disposition'] = content
        return response


class SendTicket(View):
    """Sends ticket to email"""

    def get(self, request, ticket_id, *args, **kwargs):
        ticket = Ticket.objects.get(pk=ticket_id)
        data = {
            'ticket': ticket,
            'current_year': datetime.datetime.now().year,
            'flight': get_one_flight(ticket.flight.id)
        }
        subject = f'Ticket: {ticket.code}'

        send_ticket_to_email('flights/pdf_template/pdf_template.html', request.user.email, subject, data)
        return redirect('ticket', pk=ticket_id)


def logout_user(request):
    logout(request)
    return redirect('/')


def permissionDenied(request, exception=None):
    return render(request, 'flights/errors/403.html', status=403)


def pageNotFound(request, exception=None):
    return render(request, 'flights/errors/404.html', status=404)


def serverError(request, exception=None):
    return render(request, 'flights/errors/500.html', status=500)

# def pageNotFound(request, exception):
#     return render(request, "flights/errors/404.html", {'title': "Page not found"}, status=404)

# def serverError(request):
#     return HttpResponseServerError("<h1>Server error!</h1>")

# def payment(request):
#     if request.method == 'POST':
#         token = request.POST['stripeToken']
#         print('post')
#
#         # Создайте платеж
#         try:
#             print('123')
#             charge = stripe.Charge.create(
#                 amount=1000,  # Сумма в центах
#                 currency='usd',
#                 source=token,
#                 description='Описание оплаты',
#             )
#
#             # Здесь можно сохранить информацию о платеже в базу данных
#             # Перенаправьте пользователя на страницу успешной оплаты или предоставьте
#             # соответствующее уведомление об успешной оплате
#             print('124')
#             return redirect('home')
#
#         except CardError as e:
#             print(e, '125')
#             # Ошибка платежа с карты, такая как недостаточный баланс или просроченная карта
#             messages.error(request, "Ошибка платежа: {}".format(e))
#             return redirect('payment')
#
#     return render(request, 'flights/payment.html')
