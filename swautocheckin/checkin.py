import logging

import requests
from lxml import html

DOC_DELIVERY_URL = "https://www.southwest.com/flight/selectCheckinDocDelivery.html"

PRINT_DOCUMENT_URL = "https://www.southwest.com/flight/selectPrintDocument.html"

logger = logging.getLogger(__name__)

SOUTHWEST_CHECKIN_URL = 'https://www.southwest.com/flight/retrieveCheckinDoc.html'


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
RESPONSE_STATUS_UNKNOWN_FAILURE = ResponseStatus(-100, None)


def _post_to_southwest_checkin(confirmation_num, first_name, last_name):
    """

    :param confirmation_num:
    :param first_name:
    :param last_name:
    :return:
    """
    session = requests.Session()
    get_response = session.get(SOUTHWEST_CHECKIN_URL)

    payload = {
        'confirmationNumber': confirmation_num,
        'firstName': first_name,
        'lastName': last_name,
        'submitButton': 'Check In'
    }
    response = session.post(SOUTHWEST_CHECKIN_URL, data=payload)

    return response, session


def attempt_checkin(confirmation_num, first_name, last_name, email, do_checkin=True):
    response, session = _post_to_southwest_checkin(confirmation_num, first_name, last_name)

    if response.status_code is 200 or response.status_code is 304:
        if response.content.find(RESPONSE_STATUS_SUCCESS.search_string) is not -1:
            if do_checkin:
                boarding_position = _complete_checkin(session, email, confirmation_num)
            return RESPONSE_STATUS_SUCCESS.code, boarding_position
        elif response.content.find(RESPONSE_STATUS_TOO_EARLY.search_string) is not -1:
            # more than 24 hours before
            logger.info('Checking in too early for reservation ' + confirmation_num)
            return RESPONSE_STATUS_TOO_EARLY.code, None
        elif response.content.find(RESPONSE_STATUS_INVALID.search_string) is not -1:
            # invalid format
            logger.info('Invalid confirmation number ' + confirmation_num)
            return RESPONSE_STATUS_INVALID.code, None
        elif response.content.find(RESPONSE_STATUS_RES_NOT_FOUND.search_string) is not -1:
            # incorrect name or confirmation number
            logger.info("Can't find reservation in data base " + confirmation_num)
            return RESPONSE_STATUS_RES_NOT_FOUND.code, None
        elif response.content.find(RESPONSE_STATUS_INVALID_PASSENGER_NAME.search_string) is not -1:
            logger.info("Invalid passenger name " + confirmation_num)
            return RESPONSE_STATUS_INVALID_PASSENGER_NAME.code, None
        else:
            logger.error('WTF: unhandled response.')

    else:
        logger.info('WTF received status other then 200 for ' + confirmation_num)

    filename = './res_WTF_' + str(confirmation_num) + '_content.html'
    print >> open(filename, 'w+'), response.content.replace("/assets", "http://southwest.com/assets")
    logger.error(response.content)
    return RESPONSE_STATUS_UNKNOWN_FAILURE.code, None


def _complete_checkin(session, email, confirmation_num):
    print_payload = {
        'checkinPassengers[0].selected': True,
        'printDocuments': 'Check In'
    }

    print_response = session.post(PRINT_DOCUMENT_URL, data=print_payload)

    if print_response.status_code is 200:
        if print_response.content.find("You are Checked In") is not -1:
            tree = html.fromstring(print_response.content)

            # returns an array with el[0] = boarding group, el[1] = boarding number. Example ['A', '34']
            boarding_info = tree.xpath('//span[@class="boardingInfo"]/text()')
            boarding_position = boarding_info[0] + boarding_info[1]

            doc_payload = {
                '_optionPrint': 'on',
                'optionEmail': True,
                '_optionEmail': 'on',
                'emailAddress': email,
                '_optionText': 'on',
                # 'book_now':
            }

            doc_response = session.post(DOC_DELIVERY_URL, data=doc_payload)

            if doc_response.status_code is 200:
                if doc_response.content.find("Boarding Pass Confirmation") is not -1:
                    logger.info("Success checking in confirmation number: " + confirmation_num)
                    return boarding_position
                else:
                    filename = './print_WTF_' + str(confirmation_num) + '_content.html'
                    print >> open(filename, 'w+'), doc_response.content.replace("/assets",
                                                                                "http://southwest.com/assets")
                    logger.error('Success message not found while posting to ' + DOC_DELIVERY_URL +
                                 '\ncontent: ' + doc_response.content)
            else:
                logger.error('Non-200 posting to ' + DOC_DELIVERY_URL +
                             '\nstatus_code: ' + str(doc_response.status_code) +
                             '\ncontent: ' + doc_response.content)

        else:
            logger.error('Success message not found while posting to ' + PRINT_DOCUMENT_URL +
                         '\ncontent: ' + print_response.content)
    else:
        logger.error('Non-200 posting to ' + PRINT_DOCUMENT_URL +
                     '\nstatus_code: ' + str(print_response.status_code) +
                     '\ncontent: ' + print_response.content)

    raise Exception('Error checking in')