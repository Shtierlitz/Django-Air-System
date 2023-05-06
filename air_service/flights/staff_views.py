import datetime

from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.views.generic import ListView, FormView, DeleteView, UpdateView, CreateView

from air_service.celery import app
from flights.models import Ticket, Status, Extra, Flight, Aircraft, Airport, User, Expiring
from flights.staff_forms import StaffCheckInForm, StaffExtraForm, FlightUpdateForm, FlightCreateForm, \
    AircraftCreateForm, AirportForm, AssignRoleForm
from flights.tasks import logger
from flights.utils import check_in_confirm_or_errors, \
    onboard_confirm_or_errors, BaseDataMixin, check_in_message, onboard_message, FlightMixin

from django.db.models import Case, When, IntegerField, Value, Q, F
from django.contrib import messages


class StaffMainPageView(BaseDataMixin, ListView):
    model = Ticket
    template_name = 'flights/staff/index.html'
    title = "Staff tickets list"
    paginate_by = 15

    def get_queryset(self):
        queryset = Ticket.objects.annotate(
            is_paid=Case(
                When(status=Status.PAID, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            is_not_approved_check_in=Case(
                When(check_in=Ticket.Checking.NOT_APPROVED, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            is_paid_and_approved=Case(
                When(status=Status.PAID, check_in=Ticket.Checking.APPROVED, onboard=Ticket.Checking.APPROVED,
                     then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            has_one_approved=Case(
                When(Q(check_in=Ticket.Checking.APPROVED) | Q(onboard=Ticket.Checking.APPROVED), then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            both_not_approved=Case(
                When(check_in=Ticket.Checking.NOT_APPROVED, onboard=Ticket.Checking.NOT_APPROVED, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
        ).order_by('is_paid_and_approved', '-is_paid', 'both_not_approved', '-has_one_approved', 'check_in', 'onboard')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_user_context())
        context['search'] = True
        search_query = self.request.GET.get('search')  # получаем значение search из GET-запроса
        tickets = context['object_list']
        tickets_list = []
        if search_query:
            search_query = search_query.strip()
            for ticket in tickets:
                if search_query == str(
                        ticket.id) or search_query.upper() == ticket.status.upper() \
                        or search_query.upper() == ticket.check_in.upper() \
                        or search_query.upper() == ticket.onboard.upper()\
                        or search_query.upper() == ticket.code.upper():
                    tickets_list.append(ticket)
            if len(tickets_list) == 0:
                context['not_found'] = True
            else:
                context['object_list'] = tickets_list
        return context


class TicketStaffView(BaseDataMixin, FormView):
    model = Ticket
    template_name = 'flights/staff/ticket.html'
    context_object_name = 'ticket'
    form_class = StaffCheckInForm
    title = 'Staff ticket confirm'

    def get_context_data(self, form=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_user_context())
        ticket_id = self.kwargs['ticket_id']
        ticket = Ticket.objects.get(pk=ticket_id)
        context['form'] = form if form else self.form_class(instance=ticket)
        context['ticket'] = ticket
        return context

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.has_perm('flights.can_approve_check_in') or request.user.has_perm(
                'flights.can_approve_onboard')):
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        check_in = form.cleaned_data['check_in']
        onboard = form.cleaned_data['onboard']

        ticket_id = self.kwargs['ticket_id']
        ticket = Ticket.objects.get(pk=ticket_id)

        if ticket.status == 'UNPAID' and (check_in == 'APPROVED' or onboard == 'APPROVED'):
            form.add_error(None, 'You cant approve an unpaid ticket.')
            return self.form_invalid(form)

        user = self.request.user
        if check_in != ticket.check_in and not user.has_perm('flights.can_approve_check_in'):
            form.add_error(None, 'You do not have permission to change the check-in status.')
            return self.form_invalid(form)

        if onboard != ticket.onboard and not user.has_perm('flights.can_approve_onboard'):
            form.add_error(None, 'You do not have permission to change the onboard status.')
            return self.form_invalid(form)

        check_in_confirm_or_errors(form, check_in, ticket, self.form_invalid, self.request)
        onboard_confirm_or_errors(form, onboard, check_in, ticket, self.form_invalid, self.request)

        if len(form.non_field_errors()) != 0:
            return self.form_invalid(form)

        self.success_url = reverse_lazy('staff_ticket_list')
        return super().form_valid(form)

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        return self.render_to_response(context)


class ExtraListView(BaseDataMixin, ListView):
    model = Extra
    template_name = 'flights/staff/extra/extra_list.html'
    context_object_name = 'extra'
    title = 'Extra list'


class CreateExtraView(BaseDataMixin,  CreateView):
    model = Extra
    template_name = 'flights/staff/extra/extra_create.html'
    form_class = StaffExtraForm
    success_url = reverse_lazy('staff_extra_list')
    title = 'Extra creation'
    permission = 'flights.can_manage_extras'


class ExtraUpdateView(BaseDataMixin, UpdateView):
    model = Extra
    form_class = StaffExtraForm
    template_name = 'flights/staff/extra/extra_update.html'
    success_url = reverse_lazy('staff_extra_list')
    title = 'Extra update'
    permission = 'flights.can_manage_extras'


class DeleteExtraView(BaseDataMixin, DeleteView):
    model = Extra
    template_name = 'flights/staff/extra/delete_extra.html'
    success_url = reverse_lazy('staff_extra_list')
    title = 'Delete extra'
    permission = 'flights.can_manage_extras'


class FlightListView(FlightMixin, ListView):
    model = Flight
    template_name = 'flights/staff/flight/flight_list.html'
    context_object_name = 'flight'
    title = 'Flight list'
    paginate_by = 15


class CreateFlightView(BaseDataMixin, CreateView):
    model = Flight
    template_name = 'flights/staff/flight/flight_create.html'
    form_class = FlightCreateForm
    success_url = reverse_lazy('staff_flight_list')
    title = 'Flight creation'
    permission = 'flights.can_manage_flights'


class FlightUpdateView(BaseDataMixin, UpdateView):
    model = Flight
    form_class = FlightUpdateForm
    template_name = 'flights/staff/flight/flight_update.html'
    success_url = reverse_lazy('staff_flight_list')
    title = 'Flight update'
    permission = 'flights.can_manage_flights'


class FlightDeleteView(BaseDataMixin, DeleteView):
    model = Flight
    template_name = 'flights/staff/flight/flight_delete.html'
    success_url = reverse_lazy('staff_flight_list')
    title = 'Delete flight'
    permission = 'flights.can_manage_flights'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Отменить текущую задачу
        if self.object.task_id:
            try:
                app.control.revoke(self.object.task_id)
                logger.info(f"Задача рейса с номером {self.object.name} успешно уделена")
            except Exception as e:
                logger.error(f"Ошибка при отмене задачи с ID {self.object.task_id}: {e}")
                messages.error(request, f"Ошибка при отмене задачи с ID {self.object.task_id}: {e}")

        # Найти все билеты, связанные с данным полетом
        related_tickets = self.object.tickets.all()

        # Отменить задачи для всех связанных билетов
        for ticket in related_tickets:
            if ticket.task_id:
                try:
                    app.control.revoke(ticket.task_id)
                    logger.info(f"Задача билета с номером {ticket.code} успешно уделена")
                except Exception as e:
                    logger.error(f"Ошибка при отмене задачи билета с номером {ticket.code}: {e}")
                    messages.error(request, f"Ошибка при отмене задачи билета с номером {ticket.code}: {e}")

        response = super().delete(request, *args, **kwargs)
        return response


class AircraftListView(BaseDataMixin, ListView):
    model = Aircraft
    template_name = 'flights/staff/aircraft/aircraft_list.html'
    title = 'Aircraft list'


class AircraftCreateView(BaseDataMixin, CreateView):
    model = Aircraft
    template_name = 'flights/staff/aircraft/aircraft_create.html'
    form_class = AircraftCreateForm
    success_url = reverse_lazy('staff_aircraft_list')
    title = 'Aircraft creation'
    permission = 'flights.can_manage_aircraft'


class AircraftUpdateView(BaseDataMixin, UpdateView):
    model = Aircraft
    form_class = AircraftCreateForm
    template_name = 'flights/staff/aircraft/aircraft_update.html'
    success_url = reverse_lazy('staff_aircraft_list')
    title = 'Aircraft update'
    permission = 'flights.can_manage_aircraft'


class AircraftDeleteView(BaseDataMixin, DeleteView):
    model = Aircraft
    template_name = 'flights/staff/aircraft/aircraft_delete.html'
    success_url = reverse_lazy('staff_airport_list')
    title = 'Delete aircraft'
    permission = 'flights.can_manage_aircraft'


class AirportListView(BaseDataMixin, ListView):
    model = Airport
    template_name = 'flights/staff/airport/airport_list.html'
    title = 'Airport list'
    paginate_by = 15


class AirportCreateView(BaseDataMixin, CreateView):
    model = Airport
    template_name = 'flights/staff/airport/airport_create.html'
    form_class = AirportForm
    success_url = reverse_lazy('staff_airport_list')
    title = 'Airport creation'
    permission = 'flights.can_manage_airports'


class AirportUpdateView(BaseDataMixin, UpdateView):
    model = Airport
    form_class = AirportForm
    template_name = 'flights/staff/airport/airport_update.html'
    success_url = reverse_lazy('staff_airport_list')
    title = 'Airport update'
    permission = 'flights.can_manage_airports'


class AirportDeleteView(BaseDataMixin, DeleteView):
    model = Airport
    template_name = 'flights/staff/airport/airport_delete.html'
    success_url = reverse_lazy('staff_airport_list')
    title = 'Delete airport'
    permission = 'flights.can_manage_airports'


class UserListView(BaseDataMixin, ListView):
    model = User
    template_name = 'flights/staff/user_list.html'
    title = 'Airport list'


class AssignRoleView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = AssignRoleForm
    template_name = 'flights/staff/assign_role.html'
    success_url = reverse_lazy('user_list')

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name='Supervisor').exists()

    def handle_no_permission(self):
        raise PermissionDenied
