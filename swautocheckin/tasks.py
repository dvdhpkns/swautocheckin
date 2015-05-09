from datetime import datetime
import os
from celery import Celery
from celery.exceptions import MaxRetriesExceededError
from celery.task import task
from swautocheckin import checkin
from swautocheckin.checkin import *
from celery.utils.log import get_task_logger
from django.conf import settings


logger = get_task_logger(__name__)

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'swautocheckin.settings')

app = Celery('swautocheckin')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


def _checkin_fail(reservation):
    logger.error("Checkin task failed.")
    reservation.success = False
    reservation.save()


def _retry_checkin(reservation):
    logger.info("Attempting checkin retry...")
    try:
        checkin_job.retry(args=[reservation.id])
    except MaxRetriesExceededError:
        _checkin_fail(reservation)


@task(ignore_result=False, default_retry_delay=10, max_retries=10)
def checkin_job(reservation_id):
    from swautocheckin.models import Reservation
    reservation = Reservation.objects.get(id=reservation_id)
    logger.info("Attempting checkin for " + reservation.__str__())
    logger.info('Attempt: ' + str(checkin_job.request.retries + 1))

    response_code, content = checkin.attempt_checkin(reservation.confirmation_num, reservation.passenger.first_name,
                                                     reservation.passenger.last_name, reservation.passenger.email)

    if response_code == RESPONSE_STATUS_SUCCESS.code:
        logger.info("Successfully checked in for reservation: " + reservation.__str__())
        logger.info('Time: ' + str(datetime.now().time()))
        logger.info('Reservation time: ' + str(reservation.flight_time))
        reservation.success = True
        reservation.save()
        return True
    elif response_code == RESPONSE_STATUS_TOO_EARLY.code:
        logger.info('Time: ' + str(datetime.now().time()))
        logger.info('Reservation time: ' + str(reservation.flight_time))
        _retry_checkin(reservation)
    elif response_code == RESPONSE_STATUS_INVALID.code:
        logger.error("Invalid reservation, id: " + str(reservation.id))
        _checkin_fail(reservation)
        return False
    elif response_code == RESPONSE_STATUS_RES_NOT_FOUND.code:
        logger.error("Reservation not found, id: " + str(reservation.id))
        _checkin_fail(reservation)
        return False
    else:
        logger.error("Unknown error, retrying...")
        _retry_checkin(reservation)
