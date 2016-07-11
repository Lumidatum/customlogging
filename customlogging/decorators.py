from functools import wraps
import datetime
import json
import logging
import os
import uuid

import requests

import constants
import helpers


def couchLoggingDecorator(func, config):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # TODO: wrap first logging action in try/except
        args_string = repr(args)
        kwargs_string = repr(kwargs)

        # pull necessary info from config
        remote_host = 'http://ec2-52-41-176-213.us-west-2.compute.amazonaws.com:5984'
        database = 'user_{}_model_{}'.format(config['lumidatum_user_id'], config['lumidatum_model_id'])

        url_for_model_call_start = os.path.join(remote_host, database)

        # log to couch start, time, args, kwargs
        logging_message_id_string = str(uuid.uuid4())
        logging_message = {
            '_id': logging_message_id_string,
            'args': args_string,
            'kwargs': kwargs_string,
            'start': helpers.generateUtcNowTimeStampString(),
        }
        response = requests.post(url_for_model_call_start, data=json.dumps(logging_message))

        results = func(*args, **kwargs)

        url_for_model_call_end = os.path.join(url_for_model_call_start, logging_message_id_string)

        # TODO: wrap second logging action in try/except
        # log to couch end, time
        logging_end_id_string = str(uuid.uuid4())
        logging_message['end'] = helpers.generateUtcNowTimeStampString()

        response = requests.put(url_for_model_call_end, data=json.dumps(logging_message))

        return results

    return wrapper

def functionLoggingDecorator(func, config):
    @wraps(func)
    def wrapper(*args, **kwargs):
        string_args = repr(args)
        string_kwargs = repr(kwargs)
        logging.info('[{}] before func: {} args: {} kwargs: {}'.format(datetime.datetime.utcnow().isoformat(), func.__name__, args, kwargs))
        # logging.info('[{}] before func: {} args: {} kwargs: {}'.format(datetime.datetime.utcnow().isoformat(), func.__name__, args, kwargs))
        # logging.info(datetime.datetime.utcnow().isoformat(), string_args, string_kwargs)
        results = func(*args, **kwargs)
        logging.info('[{}] after'.format(datetime.datetime.utcnow().isoformat()))
        # logging.info(datetime.datetime.utcnow().isoformat(), repr(results), string_args, string_kwargs)
        # logging.info('[{}] after'.format(datetime.datetime.utcnow().isoformat()))

        return results

    return wrapper

# TODO, this modifies the class itself, -> on next call it will wrap the wrapped class...
def classLoggingDecorator(cls, config):
    # TODO: switch function decorators based on config
    if config['output_type'] == constants.LOCAL_PAIN_TEXT_FILE:
        selected_decorator = functionLoggingDecorator

    # Setup logger as needed...

    for attr in cls.__dict__:
        if callable(getattr(cls, attr)) and attr not in config.get('exclude', set()):
            print repr(cls)
            print repr(attr)
            setattr(cls, attr, selected_decorator(getattr(cls, attr), config))

    return cls

# import logging
# logging.basicConfig(filename='wrappertest.log', level=logging.INFO)

# class thing(object):
#     def __init__(self, a):
#         self.a = a
#     def yo(self, b):
#         print "yoarr", self.a, b

# import customlogging.classes
# import customlogging.decorators

# config = {
#     'remote_host': 'ec2-52-41-176-213.us-west-2.compute.amazonaws.com:5984'
# }
# customlogging.classes.LoggingWrapper.setup('85', '125', couch_db_config=config)
# testobj = customlogging.classes.LoggingWrapper(thing, customlogging.decorators.couchLoggingDecorator, '123')
