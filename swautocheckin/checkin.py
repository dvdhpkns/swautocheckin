import logging
from django.core.mail import send_mail
from django.conf import settings

import requests
from lxml import html

DOC_DELIVERY_URL = "https://www.southwest.com/flight/selectCheckinDocDelivery.html"
PRINT_DOCUMENT_URL = "https://www.southwest.com/flight/selectPrintDocument.html"
SOUTHWEST_CHECKIN_URL = 'https://www.southwest.com/flight/retrieveCheckinDoc.html'

PRINT_PAYLOAD = {
    'checkinPassengers[0].selected': True,
    'printDocuments': 'Check In'
}

LOGGER = logging.getLogger(__name__)

# setting to allow easy toggle of printing content in logs
LOG_CONTENT = False


class ResponseStatus:
    def __init__(self, code, search_string):
        self.code = code
        self.search_string = search_string


RESPONSE_STATUS_SUCCESS = ResponseStatus(1, "Continue to Create Boarding Pass/Security Document? ")
RESPONSE_STATUS_TOO_EARLY = ResponseStatus(0, "Boarding Pass is more than 24 hours")
RESPONSE_STATUS_INVALID = ResponseStatus(-1, "The confirmation number entered is invalid.")
RESPONSE_STATUS_RES_NOT_FOUND = ResponseStatus(-2, "unable to retrieve your reservation from our database")
RESPONSE_STATUS_INVALID_PASSENGER_NAME = ResponseStatus(-3, "The passenger name entered does not match one of the "
                                                            "passenger names listed under the confirmation number")
RESPONSE_STATUS_RESERVATION_CANCELLED = ResponseStatus(-4, "Your reservation has been cancelled")
RESPONSE_STATUS_UNKNOWN_FAILURE = ResponseStatus(-100, None)

POST_HEADERS = requests.utils.default_headers().update({
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Content-Type": "application/x-www-form-urlencoded",
    "Host": "www.southwest.com",
    "Origin": "https://www.southwest.com",
    "Referer": "https://www.southwest.com",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36"
})

def _post_to_southwest_checkin(confirmation_num, first_name, last_name):
    """
    :param confirmation_num:
    :param first_name:
    :param last_name:
    :return:
    """
    session = requests.Session()
    session.get(SOUTHWEST_CHECKIN_URL)

    payload = {
        'confirmationNumber': confirmation_num,
        'firstName': first_name,
        'lastName': last_name
    }

    response = session.post(SOUTHWEST_CHECKIN_URL, data=payload, headers=POST_HEADERS)

    return response, session


def attempt_checkin(confirmation_num, first_name, last_name, email, do_checkin=True):
    response, session = _post_to_southwest_checkin(confirmation_num, first_name, last_name)

    if response.status_code is 200 or response.status_code is 304:
        if response.content.find(RESPONSE_STATUS_SUCCESS.search_string) is not -1:
            # must initialize for the case when flight on res is already less than 24 hrs away
            boarding_position = None
            if do_checkin:
                boarding_position = _complete_checkin(session, email, confirmation_num)
            return RESPONSE_STATUS_SUCCESS.code, boarding_position
        elif response.content.find(RESPONSE_STATUS_TOO_EARLY.search_string) is not -1:
            # more than 24 hours before
            LOGGER.info('Checking in too early for reservation ' + confirmation_num)
            return RESPONSE_STATUS_TOO_EARLY.code, None
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
            LOGGER.error('WTF: unhandled response.')

    else:
        LOGGER.info('WTF received status other then 200 for ' + confirmation_num)

    # send email with response body if we get here.
    _send_failure_email(confirmation_num, response,
                        subject="Unknown response from checkin attempt, status " + str(response.status_code) + ": ")
    if LOG_CONTENT:
        LOGGER.error(response.content)

    return RESPONSE_STATUS_UNKNOWN_FAILURE.code, None


def _complete_checkin(session, email, confirmation_num):
    print_response = session.post(PRINT_DOCUMENT_URL, data=PRINT_PAYLOAD, headers=POST_HEADERS)

    if print_response.status_code is 200:
        if print_response.content.find("You are Checked In") is not -1:
            tree = html.fromstring(print_response.content)

            # returns an array with el[0] = boarding group, el[1] = boarding number. Example ['A', '34']
            boarding_info = tree.xpath('//span[@class="boardingInfo"]/text()')
            boarding_position = boarding_info[0] + boarding_info[1]

            doc_payload = {
                'emailAddress': email,
                'selectedOption': 'optionEmail',
                # 'book_now':
            }

            doc_response = session.post(DOC_DELIVERY_URL, data=doc_payload, headers=POST_HEADERS)

            if doc_response.status_code is 200:
                if doc_response.content.find("Boarding Pass Confirmation") is not -1:
                    LOGGER.info("Success checking in confirmation number: " + confirmation_num)
                    return boarding_position
                else:
                    _send_failure_email(confirmation_num, doc_response, subject="Failure with doc response: ")
                    LOGGER.error('Success message not found while posting to ' + DOC_DELIVERY_URL +
                                 (('\ncontent: ' + doc_response.content) if LOG_CONTENT else ""))
            else:
                _send_failure_email(confirmation_num, doc_response,
                                    subject="Invalid status from doc response (" + str(
                                        doc_response.status_code) + "): ")
                LOGGER.error('Non-200 posting to ' + DOC_DELIVERY_URL +
                             '\nstatus_code: ' + str(doc_response.status_code) +
                             (('\ncontent: ' + doc_response.content) if LOG_CONTENT else ""))

        else:
            if print_response.request.url == 'https://www.southwest.com/flight/viewCheckinDocument.html?int=':
                send_mail("Boarding pass from Southwest auto-checkin for confirmation number: " + confirmation_num,
                          "Successful auto-checkin for southwest flight " + confirmation_num,
                          settings.EMAIL_HOST_USER,
                          [email, 'swautocheckin@dvdhpkns.com'], fail_silently=False,
                          html_message=print_response.content.replace("/assets", "http://southwest.com/assets"))
                return None
            else:
                _send_failure_email(confirmation_num, print_response, subject="Failure printing boarding pass: ")
                LOGGER.error('Success message not found while posting to ' + PRINT_DOCUMENT_URL +
                             (('\ncontent: ' + print_response.content) if LOG_CONTENT else ""))
    else:
        _send_failure_email(confirmation_num, print_response,
                            subject="Invalid status from print response (" + str(print_response.status_code) + "): ")
        LOGGER.error('Non-200 posting to ' + PRINT_DOCUMENT_URL +
                     '\nstatus_code: ' + str(print_response.status_code) +
                     (('\ncontent: ' + print_response.content) if LOG_CONTENT else ""))

    raise Exception('Error checking in')


def _send_failure_email(confirmation_num, response, subject="Failure checking in: ", to_emails=['holler@dvdhpkns.com']):
    email_subject = subject + confirmation_num
    non_html_email_body = subject + confirmation_num
    send_mail(email_subject, non_html_email_body,
              settings.EMAIL_HOST_USER,
              to_emails, fail_silently=False,
              html_message=response.content.replace("/assets", "http://southwest.com/assets"))
