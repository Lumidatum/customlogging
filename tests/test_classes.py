import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), 'test.log'),
    level=logging.INFO
)

import ast
import getpass
import json
import time
import uuid

import requests

from customlogging import classes
from customlogging import constants
from customlogging import decorators


class FooClass(object):
    def __init__(self, some_val, some_key_val=2):
        self.some_val = some_val
        self.some_key_val = some_key_val

    def AnIncludedMethod(self, first_arg, first_kwarg=None):

        return str(first_arg) + str(first_kwarg) + str(self.some_val) + str(self.some_key_val)

    def AnExcludedMethod(self, first_arg, first_kwarg=None):

        return str(first_arg) + str(first_kwarg)


REMOTE_HOST = 'http://52.41.176.213:5984'


def test_class_wrapper_couch_db_setup_dict():
    logging.warn('test_class_wrapper_couch_db_setup_dict')

    couch_db_config = {
        'remote_host': REMOTE_HOST,
    }

    assert(classes.LoggingWrapper.config.get('remote_host') is None)
    assert(classes.LoggingWrapper.config.get('database') is None)
    assert(classes.LoggingWrapper.config.get('output_type') == constants.LOCAL_PLAIN_TEXT_FILE)

    test_user_id = 5
    test_model_id = 441

    classes.LoggingWrapper.setup(
        test_user_id,
        test_model_id,
        couch_db_config=couch_db_config
    )

    assert(classes.LoggingWrapper.config.get('remote_host') == REMOTE_HOST)
    # Default behavior is to set user_{user_id}_model_{model_id} given at setup()
    assert(classes.LoggingWrapper.config.get('database') == '{}_user_5_model_441'.format(getpass.getuser()))
    assert(classes.LoggingWrapper.config.get('output_type') == constants.REMOTE_COUCH_DB)

def test_class_wrapper_success():
    logging.warn('test_class_wrapper_success')

    couch_db_config = {
        'remote_host': REMOTE_HOST,
    }

    test_user_id = 5
    test_model_id = 441

    classes.LoggingWrapper.setup(
        test_user_id,
        test_model_id,
        couch_db_config=couch_db_config
    )

    wrapped_class_instance = classes.LoggingWrapper(
        FooClass,
        decorators.couchDBLogging,
        3,
        4
    )
    test_doc_id = str(uuid.uuid4())
    expected_return_value = '1234'

    regular_arg = 1
    keyword_arg = 2

    actual_return_value = wrapped_class_instance.AnIncludedMethod(
        test_doc_id,
        regular_arg,
        first_kwarg=keyword_arg
    )

    assert(expected_return_value == actual_return_value)

    time.sleep(.2)
    write_result_response = requests.get(
        os.path.join(REMOTE_HOST, '{}_user_{}_model_{}'.format(getpass.getuser(), test_user_id, test_model_id), test_doc_id)
    )
    write_result_response_object = json.loads(write_result_response.text)

    logging.info(write_result_response.text)

    assert(ast.literal_eval(write_result_response_object['args'])[0] == 1)
    assert(ast.literal_eval(write_result_response_object['kwargs'])['first_kwarg'] == 2)
    assert(write_result_response_object['start_time'] is not None)
    assert(write_result_response_object['end_time'] is not None)

    # Clean up
    delete_response = requests.delete(
        os.path.join(REMOTE_HOST, '{}_user_{}_model_{}'.format(getpass.getuser(), test_user_id, test_model_id), test_doc_id + '?rev={}'.format(write_result_response_object['_rev']))
    )

    logging.info(write_result_response_object['_rev'])

    assert(delete_response.status_code == 200)

def test_class_wrapper_excluded():
    logging.warn('test_class_wrapper_excluded')

    couch_db_config = {
        'remote_host': REMOTE_HOST,
    }
    excluded_methods = [
        'AnExcludedMethod',
    ]

    test_user_id = 5
    test_model_id = 441

    classes.LoggingWrapper.setup(
        test_user_id,
        test_model_id,
        couch_db_config=couch_db_config,
        exclude_methods=excluded_methods
    )

    wrapped_class_instance = classes.LoggingWrapper(
        FooClass,
        decorators.couchDBLogging,
        3
    )
    expected_return_value = '12'

    regular_arg = 1
    keyword_arg = 2

    actual_return_value = wrapped_class_instance.AnExcludedMethod(
        # test_doc_id,
        regular_arg,
        first_kwarg=keyword_arg
    )

    assert(expected_return_value == actual_return_value)

    database_response = requests.get(
        os.path.join(REMOTE_HOST, '{}_user_{}_model_{}'.format(getpass.getuser(), test_user_id, test_model_id))
    )
    database_response_object = json.loads(database_response.text)

    logging.info(database_response.text)

    # Assuming all docs are cleaned up after test, except the one for model API status.
    assert(database_response_object['doc_count'] == 1)
