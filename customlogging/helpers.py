import datetime


def generateUtcNowTimeStampString():
    """
    Get the current UTC time as an ISO formatted string.

    Precision is only up to milliseconds for deserialization to
    other programming languages.
    """

    timestamp = datetime.datetime.utcnow().isoformat()

    return timestamp[:23] + timestamp[26:]