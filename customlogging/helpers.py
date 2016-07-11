import datetime
import json


def generateUtcNowTimeStampString():
    """
    Get the current UTC time as an ISO formatted string.

    Precision is only up to milliseconds for deserialization to
    other programming languages.
    """

    timestamp = datetime.datetime.utcnow().isoformat()

    return timestamp
    # return timestamp[:23] + timestamp[26:]

def sendLoggingMessage(method_call, url, message_dict):
    method_call(url, json.dumps(message_dict))
