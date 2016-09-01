import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), 'test.log'),
    level=logging.INFO
)

import ast
import json
import multiprocessing
import time
import uuid

import requests

from customlogging import decorators


REMOTE_HOST = 'http://ec2-52-41-176-213.us-west-2.compute.amazonaws.com:5984'
TEST_DB = 'test_decorator'

COUCH_DB_CONFIG = {
    'remote_host': REMOTE_HOST,
    'database': TEST_DB,
}

# Test function
def foo(some_arg, some_kwarg=None):

    return str(some_arg) + str(some_kwarg)

def errorRaisingFunc(some_arg, some_kwarg=None):

    raise ValueError('Test exception')

# Helper function for testing running logging call
def makeFunctionCall(decorated_function, message_queue, couch_db_config, expected_return_value, some_arg, some_kwarg=None, ):
    logging.warn('Making individual call...')

    test_doc_id = str(uuid.uuid4())

    if message_queue: message_queue.put((test_doct_id, some_arg, some_kwarg))
    actual_return_value = decorated_function(test_doc_id, some_arg, some_kwarg=some_kwarg)

    assert(expected_return_value == actual_return_value)

def cleanUpFunctionCall(couch_db_config, test_doc_id, test_arg_value, test_kwarg_value):
    logging.warn('Cleaning up individual call...')

    # Get value from test couchDB
    # TODO: find a better way to wait for write to CouchDB...
    # time.sleep(.2)
    write_result_response = requests.get(
        os.path.join(COUCH_DB_CONFIG['remote_host'], COUCH_DB_CONFIG['database'], test_doc_id)
    )
    write_result_response_object = json.loads(write_result_response.text)

    logging.info(write_result_response.text)

    assert(ast.literal_eval(write_result_response_object['args'])[0] == test_arg_value)
    assert(ast.literal_eval(write_result_response_object['kwargs'])['some_kwarg'] == test_kwarg_value)
    assert(write_result_response_object['start_time'] is not None)
    assert(write_result_response_object['end_time'] is not None)

    logging.info( os.path.join(COUCH_DB_CONFIG['remote_host'], COUCH_DB_CONFIG['database'], test_doc_id + '?rev={}'.format(write_result_response_object['_rev'])) )

    # Clean up
    delete_response = requests.delete(
        os.path.join(COUCH_DB_CONFIG['remote_host'], COUCH_DB_CONFIG['database'], test_doc_id + '?rev={}'.format(write_result_response_object['_rev']))
    )


def test_couchDB_decorated_function_call_success():
    logging.warn('test_couchDB_decorated_function_call_success')


    COUCH_DB_CONFIG = {
        'remote_host': REMOTE_HOST,
        'database': TEST_DB,
    }

    decorated_foo = decorators.couchDBLogging(foo, COUCH_DB_CONFIG)
    expected_return_value = '12'
    test_doc_id = str(uuid.uuid4())

    actual_return_value = decorated_foo(test_doc_id, 1, some_kwarg=2)

    assert(expected_return_value == actual_return_value)
    # Get value from test couchDB
    # TODO: find a better way to wait for write to CouchDB...
    time.sleep(.2)
    write_result_response = requests.get(
        os.path.join(REMOTE_HOST, TEST_DB, test_doc_id)
    )
    write_result_response_object = json.loads(write_result_response.text)

    logging.info(write_result_response.text)

    assert(ast.literal_eval(write_result_response_object['args'])[0] == 1)
    assert(ast.literal_eval(write_result_response_object['kwargs'])['some_kwarg'] == 2)
    assert(write_result_response_object['start_time'] is not None)
    assert(write_result_response_object['end_time'] is not None)

    logging.info( os.path.join(REMOTE_HOST, TEST_DB, test_doc_id + '?rev={}'.format(write_result_response_object['_rev'])) )

    # Clean up
    delete_response = requests.delete(
        os.path.join(REMOTE_HOST, TEST_DB, test_doc_id + '?rev={}'.format(write_result_response_object['_rev']))
    )

    logging.info(write_result_response_object['_rev'])

    assert(delete_response.status_code == 200)

def test_couchDB_decorated_function_call_multi_concurrent_success():
    logging.warn('test_couchDB_decorated_function_call_multi_concurrent_success')

    decorated_foo = decorators.couchDBLogging(foo, COUCH_DB_CONFIG)
    message_queue = multiprocessing.Queue()

    subprocs = [
        multiprocessing.Process(
            target=makeFunctionCall,
            args=(decorated_foo, message_queue, COUCH_DB_CONFIG, '02', 0, 2),
        ),
        multiprocessing.Process(
            target=makeFunctionCall,
            args=(decorated_foo, message_queue, COUCH_DB_CONFIG, '12', 1, 2),
        ),
        multiprocessing.Process(
            target=makeFunctionCall,
            args=(decorated_foo, message_queue, COUCH_DB_CONFIG, '22', 2, 2),
        ),
        multiprocessing.Process(
            target=makeFunctionCall,
            args=(decorated_foo, message_queue, COUCH_DB_CONFIG, '32', 3, 2),
        ),
        multiprocessing.Process(
            target=makeFunctionCall,
            args=(decorated_foo, message_queue, COUCH_DB_CONFIG, '42', 4, 2),
        ),
    ]

    map(lambda proc: proc.start(), subprocs)
    map(lambda proc: proc.join(), subprocs)

    # TODO: get cleanup working: currently queue doesn't get back results ... ?
    logging.error('start cleaning...')
    logging.error(message_queue.empty())
    while not message_queue.empty():
        cleanUpFunctionCall(COUCH_DB_CONFIG, *(message_queue.get()))

def test_couchDB_decorated_fuction_call_exception_logged():
    logging.warn('test_couchDB_decorated_function_call_multi_concurrent_success')

    decorated_function = decorators.couchDBLogging(errorRaisingFunc, COUCH_DB_CONFIG)

    exception_raising_proc = multiprocessing.Process(
            target=makeFunctionCall,
            args=(decorated_function, None, COUCH_DB_CONFIG, '02', 0, 2),
    )
    exception_raising_proc.start()

    assert(exception_raising_proc.exitcode != 0)

    # Check for Exception logs...
