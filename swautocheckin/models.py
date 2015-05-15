from datetime import datetime, timedelta
import logging
from django.db import models
import uuid
from swautocheckin import tasks


LOGGER = logging.getLogger(__name__)


class Passenger(models.Model):
    """Passenger to be checked in."""
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()

    def __unicode__(self):
        return u'%s %s' % (self.first_name, self.last_name)


class Reservation(models.Model):
    """Flight reservation information."""
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    passenger = models.ForeignKey(Passenger)
    confirmation_num = models.CharField(max_length=13)
    flight_time = models.TimeField()
    flight_date = models.DateField()
    task_id = models.CharField(max_length=64, blank=True, null=True)
    boarding_position = models.CharField(max_length=3, blank=True, null=True)
    success = models.NullBooleanField(blank=True, null=True, default=None)
    child_reservations = models.ManyToManyField("self", symmetrical=False, blank=True, default=None,)
                                                # limit_choices_to={"confirmation_num": confirmation_num})

    def __unicode__(self):
        return u'%s. %s: %s' % (self.id, self.passenger, self.flight_date)


def create_reservation(confirmation_num, flight_date, flight_time, passenger, return_reservation=None):
    LOGGER.info("Creating reservation and scheduling checkin task...")

    reservation = Reservation.objects.create(
        passenger=passenger,
        flight_date=flight_date,
        flight_time=flight_time,
        confirmation_num=confirmation_num,
    )
    if return_reservation:
        reservation.child_reservations.add(return_reservation)
    # schedule checkin for 24 hours before reservation
    checkin_time = _get_checkin_time(reservation)
    result = tasks.checkin_job.apply_async(args=[reservation.id], eta=checkin_time)
    reservation.task_id = result.id
    reservation.save()
    return reservation


def _get_checkin_time(reservation):
    checkin_time = datetime.combine(
        (reservation.flight_date - timedelta(days=1)),  # Subtract 24 hours for checkin time
        reservation.flight_time
    )
    # todo is utc 7 hours during daylight savings?
    checkin_time += timedelta(hours=7)  # Add 7 hours for UTC
    # checkin_time -= timedelta(seconds=30)  # Start trying 30 seconds
    return checkin_time