import logging

from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect

from swautocheckin.forms import EmailForm, ReservationForm
from swautocheckin.models import Passenger, Reservation, create_reservation


LOGGER = logging.getLogger(__name__)


def email_view(request):
    if request.method == 'POST':
        email_form = EmailForm(request.POST)
        if email_form.is_valid():
            form_email = email_form.cleaned_data['email']
            passenger, created = Passenger.objects.get_or_create(email=form_email)
            return HttpResponseRedirect(reverse('reservation', args=[passenger.uuid]))

    else:
        email_form = EmailForm()

    return render(request, 'email.html', {
        'email_form': email_form,
    })


def reservation_view(request, passenger_uuid):
    passenger = get_object_or_404(Passenger, uuid=passenger_uuid)

    if request.method == 'POST':
        reservation_form = ReservationForm(request.POST)
        if reservation_form.is_valid():
            if passenger.first_name != reservation_form.cleaned_data['first_name'] \
                    or passenger.last_name != reservation_form.cleaned_data['last_name']:
                LOGGER.info("Updating passenger name...")
                passenger.first_name = reservation_form.cleaned_data['first_name']
                passenger.last_name = reservation_form.cleaned_data['last_name']
                passenger.save()

            confirmation_num = reservation_form.cleaned_data['confirmation_num']
            flight_date = reservation_form.cleaned_data['flight_date']
            flight_time = reservation_form.cleaned_data['flight_time']
            return_flight_date = reservation_form.cleaned_data['return_flight_date']
            return_flight_time = reservation_form.cleaned_data['return_flight_time']
            return_reservation = None
            if return_flight_time and return_flight_time:
                return_reservation = create_reservation(confirmation_num, return_flight_date, return_flight_time, passenger)
            reservation = create_reservation(confirmation_num, flight_date, flight_time, passenger, return_reservation=return_reservation)

            return HttpResponseRedirect(reverse('success', args=[reservation.uuid]))
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


def success_view(request, reservation_uuid):
    reservation = get_object_or_404(Reservation, uuid=reservation_uuid)
    return render(request, 'success.html', {
        'reservation': reservation
    })

