from datetime import datetime, timedelta
import logging

import pytz
from celery.result import AsyncResult
from django.db import models
import uuid
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from swautocheckin import tasks

LOGGER = logging.getLogger(__name__)


class Passenger(models.Model):
    """Passenger to be checked in."""
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()

    def __unicode__(self):
        return u'%s %s - %s' % (self.first_name, self.last_name, self.email)


class Reservation(models.Model):
    """Flight reservation information."""
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    passenger = models.ForeignKey(Passenger)
    confirmation_num = models.CharField(max_length=13)
    flight_time = models.TimeField()
    flight_date = models.DateField()
    task_id = models.CharField(max_length=64, blank=True, null=True)
    boarding_position = models.CharField(max_length=3, blank=True, null=True)
    success = models.NullBooleanField(blank=True, null=True, default=None)
    child_reservations = models.ManyToManyField("self", symmetrical=False, blank=True, default=None, )
    # limit_choices_to={"confirmation_num": confirmation_num})

    def __unicode__(self):
        return u'%s. %s: %s' % (self.id, self.passenger, self.flight_date)

    def revoke_task(self, update=False):
        if self.task_id:
            LOGGER.info("Deleting task " + self.task_id)
            result = AsyncResult(self.task_id)
            result.revoke()
            if update:
                self.task_id = None
                self.success = False
                self.save()

    def create_task(self):
        # revoke task if one already exists
        try:
            self.revoke_task()
        except:
            LOGGER.error("Error revoking task. Will continue to create new task.")
        LOGGER.info("Creating task for " + self.__str__())
        # schedule checkin for 24 hours before reservation
        checkin_time = self._get_checkin_time()
        LOGGER.info("Checkin time is " + checkin_time.__str__())
        result = tasks.checkin_job.apply_async(args=[self.id], eta=checkin_time)
        self.task_id = result.id
        self.success = None
        self.save()

    def _get_checkin_time(self):

        checkin_time = datetime.combine(
            (self.flight_date - timedelta(days=1)),  # Subtract 24 hours for checkin time
            self.flight_time
        )
        checkin_time -= timedelta(seconds=10)  # Start trying a few seconds early

        # convert to utc
        pst_timezone = pytz.timezone("America/Los_Angeles")
        checkin_time_pst = pst_timezone.localize(checkin_time, is_dst=None)
        checkin_time_utc = checkin_time_pst.astimezone(pytz.utc)
        return checkin_time_utc


@receiver(pre_delete, sender=Reservation)
def pre_delete_revoke_task(sender, instance, using, **kwargs):
    instance.revoke_task()


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
    reservation.create_task()
    return reservation



