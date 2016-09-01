import datetime
import json
import logging


def generateUtcNowTimeStampString():
    """
    Get the current UTC time as an ISO formatted string.

    Precision is only up to milliseconds for deserialization to
    other programming languages.
    """

    timestamp = datetime.datetime.utcnow().isoformat()

    return timestamp[:23] + timestamp[26:]

def sendLoggingMessage(method_call, url, message_dict):
    try:
        method_call(url, json.dumps(message_dict))
    except Exception as e:
        logging.exception(e.message)
