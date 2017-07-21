from datetime import datetime
import os
from celery import Celery
from celery.exceptions import MaxRetriesExceededError
from celery.task import task
from swautocheckin import checkin
from swautocheckin.checkin import *
from celery.utils.log import get_task_logger
from django.conf import settings

LOGGER = get_task_logger(__name__)

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'swautocheckin.settings.dev')

app = Celery('swautocheckin')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


def _checkin_fail(reservation):
    LOGGER.error("Checkin task failed.")
    reservation.success = False
    reservation.save()


def _retry_checkin(reservation):
    LOGGER.info("Attempting checkin retry...")
    try:
        checkin_job.retry(args=[reservation.id])
    except MaxRetriesExceededError:
        _checkin_fail(reservation)
        return False


@task(ignore_result=False, default_retry_delay=3, max_retries=5)
def checkin_job(reservation_id):
    from swautocheckin.models import Reservation

    reservation = Reservation.objects.get(id=reservation_id)
    LOGGER.info("Attempting checkin for " + reservation.__str__())
    LOGGER.info('Attempt: ' + str(checkin_job.request.retries + 1))

    response_code, boarding_position = checkin.attempt_checkin(reservation.confirmation_num,
                                                               reservation.passenger.first_name,
                                                               reservation.passenger.last_name,
                                                               reservation.passenger.email)

    try:
        if response_code == RESPONSE_STATUS_SUCCESS.code:
            LOGGER.info("Successfully checked in for reservation: " + reservation.__str__())
            LOGGER.info('Time: ' + str(datetime.now().time()))
            LOGGER.info('Reservation time: ' + str(reservation.flight_time))
            reservation.success = True
            reservation.boarding_position = boarding_position
            reservation.save()
            return True
        elif response_code == RESPONSE_STATUS_TOO_EARLY.code:
            LOGGER.info('Time: ' + str(datetime.now().time()))
            LOGGER.info('Reservation time: ' + str(reservation.flight_time))
            _retry_checkin(reservation)
        elif response_code == RESPONSE_STATUS_INVALID.code:
            LOGGER.error("Invalid reservation, id: " + str(reservation.id))
            _checkin_fail(reservation)
            return False
        elif response_code == RESPONSE_STATUS_RES_NOT_FOUND.code:
            LOGGER.error("Reservation not found, id: " + str(reservation.id))
            _checkin_fail(reservation)
            return False
        elif response_code == RESPONSE_STATUS_RESERVATION_CANCELLED.code:
            LOGGER.error("Reservation canceled, id: " + str(reservation.id))
            _checkin_fail(reservation)
            return False
        else:
            LOGGER.error("Unknown error, retrying...")
            _retry_checkin(reservation)
    except Exception as e:
        email_subject = "Exception while checking in..."
        non_html_email_body = "Exception occurred while checking in for " + reservation.id + ": " + e.message
        send_mail(email_subject, non_html_email_body,
                  settings.EMAIL_HOST_USER,
                  ['holler@dvdhpkns.com'], fail_silently=False,
                  html_message=non_html_email_body)


@task(ignore_result=False, default_retry_delay=3, max_retries=0)
def error_task():
    LOGGER.error("Entered error task. Will intentionally throw exception.")
    raise Exception("You've intentionally thrown a task exception.")
