from django.contrib import admin

from swautocheckin.models import Reservation, Passenger
from celery.result import AsyncResult


def kill_tasks(model_admin, request, query_set):
    reservations = query_set.all()
    for reservation in reservations:
        reservation.revoke_task(update=True)


def create_tasks(model_admin, request, query_set):
    reservations = query_set.all()
    for reservation in reservations:
        reservation.create_task()


class ReservationAdmin(admin.ModelAdmin):
    # fields = ['passenger', 'success', 'boarding_position']
    list_display = (
        'passenger', 'confirmation_num', 'flight_date', 'flight_time', 'success', 'boarding_position', 'created_at')
    actions = [create_tasks, kill_tasks]


admin.site.register(Reservation, ReservationAdmin)
admin.site.register(Passenger)
