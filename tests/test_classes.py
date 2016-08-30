import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), 'test_classes.log'),
    level=logging.INFO
)

import ast
import json
import time
import uuid

import requests

from customlogging import classes
from customlogging import constants


def FooClass(object):
    def __init__(self):
        pass

    def AnIncludedMethod(self, first_arg, first_kwarg=None):

        return str(first_arg) + str(first_kwarg)

    def AnExcludedMethod(self, first_arg, first_kwarg=None):

        return str(first_arg) + str(first_kwarg)


REMOTE_HOST = 'http://52.41.176.213:5984'


def test_class_wrapper_couch_db_setup_dict():
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
    assert(classes.LoggingWrapper.config.get('database') == 'user_5_model_441')
    assert(classes.LoggingWrapper.config.get('output_type') == constants.REMOTE_COUCH_DB)

def test_class_wrapper_success():
    pass

def test_class_wrapper_excluded():
    pass
