from functools import wraps
import datetime
import json
import logging
import multiprocessing
import os
import uuid

# import grequests
import requests

import constants
import helpers


def couchLoggingDecorator(func, config):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            args_string = repr(args)
            kwargs_string = repr(kwargs)

            # pull necessary info from config
            remote_host = config['remote_host']
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

            logging_start_proc = multiprocessing.Process(
                target=helpers.sendLoggingMessage,
                args=(requests.post, url_for_model_call_start, logging_message)
            )
            logging_start_proc.start()
            # print logging_message
        except Exception as e:
            logging.exception('Pre function call logging failure: {}'.format(e))

        results = func(*args, **kwargs)

        try:
            url_for_model_call_end = os.path.join(url_for_model_call_start, logging_message_id_string)

            # log to couch end, time
            logging_end_id_string = str(uuid.uuid4())
            logging_message['end'] = helpers.generateUtcNowTimeStampString()

            logging_end_proc = multiprocessing.Process(
                target=helpers.sendLoggingMessage,
                args=(requests.put, url_for_model_call_end, logging_message)
            )
            logging_end_proc.start()
            # print logging_message['end']
        except Exception as e:
            logging.exception('Post function call logging failure: {}'.format(e))

        return results

    return wrapper

def functionLoggingDecorator(func, config):
    @wraps(func)
    def wrapper(*args, **kwargs):
        string_args = repr(args)
        string_kwargs = repr(kwargs)
        logging.info('[{}] before func: {} args: {} kwargs: {}'.format(datetime.datetime.utcnow().isoformat(), func.__name__, args, kwargs))

        results = func(*args, **kwargs)

        logging.info('[{}] after'.format(datetime.datetime.utcnow().isoformat()))

        return results

    return wrapper

# import logging
# logging.basicConfig(filename='wrappertest.log', level=logging.INFO)

# class thing(object):
#     def __init__(self, a):
#         self.a = a
#     def somefunc(self, b):
#         print "yoarr", self.a, b

# import customlogging.classes
# import customlogging.decorators

# config = {
#     'remote_host': 'http://ec2-52-41-176-213.us-west-2.compute.amazonaws.com:5984'
# }
# customlogging.classes.LoggingWrapper.setup('85', '125', couch_db_config=config)
# testobj = customlogging.classes.LoggingWrapper(thing, customlogging.decorators.couchLoggingDecorator, '123')
# testobj.somefunc('some message')