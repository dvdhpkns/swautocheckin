import json
import logging
from django.core.mail import send_mail
from django.conf import settings

import requests

SOUTHWEST_HOST = 'https://www.southwest.com'
BOARDING_PASS_PATH = "/api/air-checkin/v1/air-checkin/feature/mobile-boarding-pass"
CONFIRMATION_PATH = "/api/air-checkin/v1/air-checkin/page/air/check-in/confirmation"
CHECKIN_REVIEW_PATH = "/api/air-checkin/v1/air-checkin/page/air/check-in/review"

LOGGER = logging.getLogger(__name__)

# setting to allow easy toggle of printing content in logs
LOG_CONTENT = False


class ResponseStatus:
    def __init__(self, code, search_string):
        self.code = code
        self.search_string = search_string


RESPONSE_STATUS_SUCCESS = ResponseStatus(1, "")
RESPONSE_STATUS_TOO_EARLY = ResponseStatus(0, "DEPARTURE_DATE_IS_TOO_SOON")
RESPONSE_STATUS_INVALID = ResponseStatus(-1, "CONFIRMATION_NUMBER__DOES_NOT_MATCH")
RESPONSE_STATUS_RES_NOT_FOUND = ResponseStatus(-2, "RESERVATION_NOT_FOUND")
RESPONSE_STATUS_INVALID_PASSENGER_NAME = ResponseStatus(-3, "PASSENGER_IS_NOT_IN_RESERVATION")
RESPONSE_STATUS_RESERVATION_CANCELLED = ResponseStatus(-4, "Your reservation has been cancelled")  # todo
RESPONSE_STATUS_FLIGHT_FINALIZED = ResponseStatus(-5, "FLIGHT_FINALIZED")
RESPONSE_STATUS_UNKNOWN_FAILURE = ResponseStatus(-100, None)

POST_HEADERS = requests.utils.default_headers()
POST_HEADERS.update({
    "origin": "https://www.southwest.com",
    "pragma": "no-cache",
    "referer": "https://www.southwest.com/air/check-in/index.html?redirectToVision=true&leapfrogRequest=true",
    "x-channel-id": "southwest",
    "x-api-key": "l7xx944d175ea25f4b9c903a583ea82a1c4c",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US,en;q=0.9",
    "authorization": "null null",
    "cache-control": "no-cache",
    "content-type": "application/json"
})


def _post_to_southwest_checkin(confirmation_num, first_name, last_name):
    """
    :param confirmation_num:
    :param first_name:
    :param last_name:
    :return:
    """
    session = requests.Session()
    session.get(SOUTHWEST_HOST)

    data = {
        "redirectToVision": "true",
        "passengerFirstName": first_name,
        "passengerLastName": last_name,
        "leapfrogRequest": "true",
        # "hash": "0e4094b8-9047-477f-bf1d-820ed3fe419b",
        "confirmationNumber": confirmation_num,
        "application": "air-check-in",
        "site": "southwest"
    }

    response = session.post(SOUTHWEST_HOST + CHECKIN_REVIEW_PATH, data=json.dumps(data), headers=POST_HEADERS)

    return response, session


def attempt_checkin(confirmation_num, first_name, last_name, email, do_checkin=True):
    response, session = _post_to_southwest_checkin(confirmation_num, first_name, last_name)
    if response.status_code is 200 or response.status_code is 304:
        # must initialize for the case when flight on res is already less than 24 hrs away
        boarding_position = None
        if do_checkin:
            response_json = json.loads(response.content)
            try:
                token = response_json["data"]["searchResults"]["token"]
            except KeyError:
                LOGGER.exception("Failed to complete checkin, missing token.")
                _send_failure_email(confirmation_num, response,
                                    subject="Failed to complete checkin, missing token.")
                return RESPONSE_STATUS_UNKNOWN_FAILURE.code, None
            boarding_position = _complete_checkin(session, email, confirmation_num, token)
        return RESPONSE_STATUS_SUCCESS.code, boarding_position
    else:
        # early and finalized return 400. the rest 404 (I think!)
        # for now lets just use strings and not worry about status
        if response.content.find(RESPONSE_STATUS_TOO_EARLY.search_string) is not -1:
            # more than 24 hours before
            LOGGER.info('Checking in too early for reservation ' + confirmation_num)
            return RESPONSE_STATUS_TOO_EARLY.code, None
        elif response.content.find(RESPONSE_STATUS_FLIGHT_FINALIZED.search_string) is not -1:
            return RESPONSE_STATUS_FLIGHT_FINALIZED.code, None
        elif response.content.find(RESPONSE_STATUS_INVALID.search_string) is not -1:
            # invalid format
            LOGGER.info('Invalid confirmation number ' + confirmation_num)
            return RESPONSE_STATUS_INVALID.code, None
        elif response.content.find(RESPONSE_STATUS_RES_NOT_FOUND.search_string) is not -1:
            # incorrect name or confirmation number
            LOGGER.info("Can't find reservation in data base " + confirmation_num)
            return RESPONSE_STATUS_RES_NOT_FOUND.code, None
        elif response.content.find(RESPONSE_STATUS_INVALID_PASSENGER_NAME.search_string) is not -1:
            LOGGER.info("Invalid passenger name " + confirmation_num)
            return RESPONSE_STATUS_INVALID_PASSENGER_NAME.code, None
        elif response.content.find(RESPONSE_STATUS_RESERVATION_CANCELLED.search_string) is not -1:
            LOGGER.info("Reservation canceled " + confirmation_num)
            return RESPONSE_STATUS_RESERVATION_CANCELLED.code, None
        else:
            LOGGER.info('WTF received unknown status ' + str(response.status_code) + " for " + confirmation_num)

    # send email with response body if we get here.
    _send_failure_email(confirmation_num, response,
                        subject="Unknown response from checkin attempt, status " + str(response.status_code) + ": ")
    if LOG_CONTENT:
        LOGGER.error(response.content)

    return RESPONSE_STATUS_UNKNOWN_FAILURE.code, None


def _complete_checkin(session, email, confirmation_num, token):
    data = {
        "airportCheckInRequiredReservation": "false",
        "confirmationNumber": confirmation_num,
        "drinkCouponSelected": "false",
        "electronicSystemTravelAuthorizationRequiredReservation": "false",
        "international": "false",
        "reprint": "false",
        "token": token,
        "travelAuthorizationCheckNotPerformed": "false",
        "travelerIdentifiers": [],
        "application": "air-check-in",
        "site": "southwest"
    }

    checkin_response = session.post(SOUTHWEST_HOST + CONFIRMATION_PATH, data=json.dumps(data), headers=POST_HEADERS)

    if checkin_response.status_code is 200:
        # if print_response.content.find("You are Checked In") is not -1:
        boarding_position = ""
        checkin_json = json.loads(checkin_response.content)
        try:
            b = checkin_json['data']['searchResults']['travelers'][0]['boardingBounds'][0]['boardingSegments'][0]
            boarding_position = b['boardingGroup'] + b['boardingGroupPosition']
        except:
            LOGGER.exception("Error getting boarding position.")

        doc_payload = {
            "deliveryMethod": "EMAIL",
            "destination": email,
            "confirmationNumber": confirmation_num,
            "drinkCouponSelected": "false",
            "token": token,
            "application": "air-check-in",
            "site": "southwest"
        }

        doc_response = session.post(SOUTHWEST_HOST + BOARDING_PASS_PATH, data=json.dumps(doc_payload),
                                    headers=POST_HEADERS)

        if doc_response.status_code is 200:
            if doc_response.content.find("Boarding Pass Confirmation") is not -1:
                LOGGER.info("Success checking in confirmation number: " + confirmation_num)
                return boarding_position
            else:
                _send_failure_email(confirmation_num, doc_response, subject="Failure with doc response: ")
                LOGGER.error('Success message not found while posting to ' + BOARDING_PASS_PATH +
                             (('\ncontent: ' + doc_response.content) if LOG_CONTENT else ""))
        else:
            _send_failure_email(confirmation_num, doc_response,
                                subject="Invalid status from doc response (" + str(
                                    doc_response.status_code) + "): ")
            LOGGER.error('Non-200 posting to ' + BOARDING_PASS_PATH +
                         '\nstatus_code: ' + str(doc_response.status_code) +
                         (('\ncontent: ' + doc_response.content) if LOG_CONTENT else ""))

            # else:
            #     if print_response.request.url == 'https://www.southwest.com/flight/viewCheckinDocument.html?int=':
            #         send_mail("Boarding pass from Southwest auto-checkin for confirmation number: " + confirmation_num,
            #                   "Successful auto-checkin for southwest flight " + confirmation_num,
            #                   settings.EMAIL_HOST_USER,
            #                   [email, 'swautocheckin@dvdhpkns.com'], fail_silently=False,
            #                   html_message=print_response.content.replace("/assets", "http://southwest.com/assets"))
            #         return None
            #     else:
            #         _send_failure_email(confirmation_num, print_response, subject="Failure printing boarding pass: ")
            #         LOGGER.error('Success message not found while posting to ' + CONFIRMATION_PATH +
            #                      (('\ncontent: ' + print_response.content) if LOG_CONTENT else ""))
    else:
        _send_failure_email(confirmation_num, checkin_response,
                            subject="Invalid status from print response (" + str(checkin_response.status_code) + "): ")
        LOGGER.error('Non-200 posting to ' + CONFIRMATION_PATH +
                     '\nstatus_code: ' + str(checkin_response.status_code) +
                     (('\ncontent: ' + checkin_response.content) if LOG_CONTENT else ""))

    raise Exception('Error checking in')


def _send_failure_email(confirmation_num, response, subject="Failure checking in: ", to_emails=['holler@dvdhpkns.com']):
    email_subject = subject + confirmation_num
    non_html_email_body = subject + confirmation_num
    send_mail(email_subject, non_html_email_body,
              settings.EMAIL_HOST_USER,
              to_emails, fail_silently=False,
              html_message=response.content.replace("/assets", "http://southwest.com/assets"))
