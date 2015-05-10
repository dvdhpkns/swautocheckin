from django.db import models


class Passenger(models.Model):
    """Passenger to be checked in."""
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()

    def __unicode__(self):
        return u'%s %s' % (self.first_name, self.last_name)


class Reservation(models.Model):
    """Flight reservation information."""
    passenger = models.ForeignKey(Passenger)
    confirmation_num = models.CharField(max_length=13)
    flight_time = models.TimeField()
    flight_date = models.DateField()
    task_id = models.CharField(max_length=64)
    boarding_group = models.CharField(max_length=3)
    success = models.BooleanField(default=False)

    def __unicode__(self):
        return u'%s. %s: %s' % (self.id, self.passenger, self.flight_date)