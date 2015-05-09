from datetime import datetime, timedelta
import logging
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from swautocheckin import tasks

from swautocheckin.forms import EmailForm, ReservationForm
from swautocheckin.models import Passenger, Reservation

LOGGER = logging.getLogger(__name__)


def email_view(request):
    LOGGER.info("test")
    if request.method == 'POST':
        email_form = EmailForm(request.POST)
        if email_form.is_valid():
            form_email = email_form.cleaned_data['email']
            passenger, created = Passenger.objects.get_or_create(email=form_email)
            return HttpResponseRedirect(reverse('reservation', args=[passenger.id]))

    else:
        email_form = EmailForm()

    return render(request, 'email.html', {
        'email_form': email_form,
    })


def _get_checkin_time(reservation):
    checkin_time = datetime.combine(
        (reservation.flight_date - timedelta(days=1)),  # Subtract 24 hours for checkin time
        reservation.flight_time
    )
    # todo is utc 7 hours during daylight savings?
    checkin_time += timedelta(hours=7)  # Add 7 hours for UTC
    # checkin_time -= timedelta(seconds=30)  # Start trying 30 seconds
    return checkin_time


def reservation_view(request, passenger_id):
    passenger = get_object_or_404(Passenger, id=passenger_id)

    if request.method == 'POST':
        reservation_form = ReservationForm(request.POST)
        if reservation_form.is_valid():
            passenger.first_name = reservation_form.cleaned_data['first_name']
            passenger.last_name = reservation_form.cleaned_data['last_name']
            passenger.save()
            confirmation_num = reservation_form.cleaned_data['confirmation_num']
            flight_date = reservation_form.cleaned_data['flight_date']
            flight_time = reservation_form.cleaned_data['flight_time']

            reservation = Reservation.objects.create(
                passenger=passenger,
                flight_date=flight_date,
                flight_time=flight_time,
                confirmation_num=confirmation_num
            )

            checkin_time = _get_checkin_time(reservation)

            tasks.checkin_job.apply_async(args=[reservation.id], eta=checkin_time)

            return HttpResponseRedirect(reverse('success', args=[reservation.id]))
    else:
        reservation_form = ReservationForm(
            initial={
                'email': passenger.email,
                'first_name': passenger.first_name,
                'last_name': passenger.last_name,
            })

    return render(request, 'create-reservation.html', {
        'reservation_form': reservation_form,
        'passenger': passenger,
    })


def success_view(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    return render(request, 'success.html', {
        'reservation': reservation
    })

