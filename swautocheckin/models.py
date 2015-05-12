from django.db import models
import uuid


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