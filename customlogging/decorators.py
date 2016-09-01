from functools import wraps
import datetime
import json
import logging
import multiprocessing
import os
import uuid

import requests

import constants
import helpers


def couchDBLogging(func, config):
    @wraps(func)
    def wrapper(logging_message_id_string=None, *args, **kwargs):
        # Pull necessary info from config
        remote_host = config['remote_host']
        database = config['database']

        url_for_model_call_start = os.path.join(remote_host, database)

        if logging_message_id_string == None:
            logging_message_id_string = str(uuid.uuid4())

        try:
            # Set status doc to hold up value
            url_for_model_status = os.path.join(url_for_model_call_start, 'api_status')
            logging_model_up_proc = multiprocessing.Process(
                target=helpers.sendLoggingMessage,
                args=(
                    requests.put,
                    url_for_model_status,
                    {
                        'status': constants.MODEL_API_STATUS_UP,
                        'status_update_time': helpers.generateUtcNowTimeStampString(),
                    }
                )
            )
            logging_model_up_proc.start()
        except Exception as e:
            logging.exception('Pre function call logging failure, unable to set API UP status: {}'.format(e))

        try:
            args_string = repr(args)
            kwargs_string = repr(kwargs)

            # Log to CouchDB start: time, args, kwargs

            logging_message = {
                '_id': logging_message_id_string,
                'args': args_string,
                'kwargs': kwargs_string,
                'start_time': helpers.generateUtcNowTimeStampString(),
            }

            logging_start_proc = multiprocessing.Process(
                target=helpers.sendLoggingMessage,
                args=(requests.post, url_for_model_call_start, logging_message)
            )
            logging_start_proc.start()
        except Exception as e:
            logging.exception('Pre function call logging failure: {}'.format(e))

        url_for_model_call_endpoint = os.path.join(url_for_model_call_start, logging_message_id_string)

        results = None

        try:
            results = func(*args, **kwargs)
        except Exception as e:
            logging.exception('Inner function call failure: {}'.format(e))

            logging_message['exception'] = e.message
            logging_message['end_time'] = helpers.generateUtcNowTimeStampString()
            logging_message['model_satus'] = constants.MODEL_API_STATUS_DOWN

            logging_exception_proc = multiprocessing.Process(
                target=helpers.sendLoggingMessage,
                args=(requests.put, url_for_model_call_endpoint, logging_message)
            )
            logging_exception_proc.start()

            # Set status doc to hold down value
            url_for_model_status = os.path.join(url_for_model_call_start, 'api_status')
            logging_model_down_proc = multiprocessing.Process(
                target=helpers.sendLoggingMessage,
                args=(
                    requests.put,
                    url_for_model_status,
                    {
                        'status': constants.MODEL_API_STATUS_DOWN,
                        'status_update_time': helpers.generateUtcNowTimeStampString(),
                    }
                )
            )
            logging_model_down_proc.start()

            raise e

        try:
            #Log to CouchDB end: time
            logging_message['end_time'] = helpers.generateUtcNowTimeStampString()
            logging_message['model_satus'] = constants.MODEL_API_STATUS_UP

            logging_end_proc = multiprocessing.Process(
                target=helpers.sendLoggingMessage,
                args=(requests.put, url_for_model_call_endpoint, logging_message)
            )
            logging_end_proc.start()
        except Exception as e:
            logging.exception('Post function call logging failure: {}'.format(e))

        return results

    return wrapper

def pythonLogging(func, config):
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
# testobj = customlogging.classes.LoggingWrapper(thing, customlogging.decorators.couchDBLogging, '123')
# testobj.somefunc('some message')
