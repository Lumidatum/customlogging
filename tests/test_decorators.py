import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import ast
import json
import time
import uuid

import requests

from customlogging import decorators

# Test function
def foo(some_arg, some_kwarg=None):

    return str(some_arg) + str(some_kwarg)


def test_couchDB_decorated_function_call():
    remote_host = 'http://52.41.176.213:5984'
    test_db = 'test_decorator'

    couch_db_config = {
        'remote_host': remote_host,
        'database': test_db,
    }

    decorated_foo = decorators.couchDBLogging(foo, couch_db_config)

    expected_return_value = '12'

    test_doc_id = str(uuid.uuid4())

    actual_return_value = decorated_foo(test_doc_id, 1, some_kwarg=2)

    assert(expected_return_value == actual_return_value)
    # Get value from test couchDB
    # TODO: find a better way to wait for write to CouchDB...
    time.sleep(.1)
    couchDB_response = requests.get(
        os.path.join(remote_host, test_db, test_doc_id)
    )
    couch_response_object = json.loads(couchDB_response.text)

    assert(ast.literal_eval(couch_response_object['args'])[0] == 1)
    assert(ast.literal_eval(couch_response_object['kwargs'])['some_kwarg'] == 2)
    assert(couch_response_object['start_time'] is not None)
    assert(couch_response_object['end_time'] is not None)
