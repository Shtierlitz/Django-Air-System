from django.contrib import admin
from django_celery_results.admin import TaskResultAdmin as OriginalTaskResultAdmin
from django_celery_results.models import TaskResult

# Register your models here.
from flights.models import *


class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username')


class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'user', 'flight', 'price', 'seat')


class ExtraAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'available', 'price')


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'ticket', 'price', 'date', 'cardholder_name')


class SeatAdmin(admin.ModelAdmin):
    list_display = ('id', 'row_letter', 'seat_number', 'seat_type')
    ordering = ('id', )


class FlightAdmin(admin.ModelAdmin):
    list_display = ('id', 'departure_time', 'arrival_time', 'aircraft', 'origin_airport', 'destination_airport',
                    'economy_seats', 'business_seats', 'first_class_seats', 'seats_list', 'users_list')
    ordering = ('id',)

    def seats_list(self, obj):
        return ", ".join([str(seat) for seat in obj.seats.all()])

    seats_list.short_description = 'Seats'

    def users_list(self, obj):
        return ", ".join([str(seat) for seat in obj.users.all()])

    users_list.short_description = 'Users'


class AircraftAdmin(admin.ModelAdmin):
    list_display = ('id', 'model', 'aircraft_type', 'total_seats')


class AirportAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'city', 'country')


class CustomTaskResultAdmin(admin.ModelAdmin):
    list_display = ('task_id', 'task_name', 'status', 'date_done', 'result')
    list_filter = ('status', 'task_name', 'date_done')
    search_fields = ('task_id', 'task_name',)

admin.site.unregister(TaskResult)  # Удаляем стандартный ModelAdmin
admin.site.register(TaskResult, CustomTaskResultAdmin)

admin.site.register(User, UserAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(Extra, ExtraAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Seat, SeatAdmin)
admin.site.register(Flight, FlightAdmin)
admin.site.register(Aircraft, AircraftAdmin)
admin.site.register(Airport, AirportAdmin)
