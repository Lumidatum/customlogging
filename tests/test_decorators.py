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


# Test function
def foo(some_arg, some_kwarg=None):

    return str(some_arg) + str(some_kwarg)

# Helper function for testing running logging call
def makeFunctionCall(decorated_function, message_queue, couch_db_config, expected_return_value, some_arg, some_kwarg=None, ):
    logging.warn('Making individual call...')

    test_doc_id = str(uuid.uuid4())

    message_queue.put((test_doct_id, some_arg, some_kwarg))
    actual_return_value = decorated_function(test_doc_id, some_arg, some_kwarg=some_kwarg)

    assert(expected_return_value == actual_return_value)

def cleanUpFunctionCall(couch_db_config, test_doc_id, test_arg_value, test_kwarg_value):
    logging.warn('Cleaning up individual call...')

    # Get value from test couchDB
    # TODO: find a better way to wait for write to CouchDB...
    # time.sleep(.2)
    write_result_response = requests.get(
        os.path.join(couch_db_config['remote_host'], couch_db_config['database'], test_doc_id)
    )
    write_result_response_object = json.loads(write_result_response.text)

    logging.info(write_result_response.text)

    assert(ast.literal_eval(write_result_response_object['args'])[0] == test_arg_value)
    assert(ast.literal_eval(write_result_response_object['kwargs'])['some_kwarg'] == test_kwarg_value)
    assert(write_result_response_object['start_time'] is not None)
    assert(write_result_response_object['end_time'] is not None)

    logging.info( os.path.join(couch_db_config['remote_host'], couch_db_config['database'], test_doc_id + '?rev={}'.format(write_result_response_object['_rev'])) )

    # Clean up
    delete_response = requests.delete(
        os.path.join(couch_db_config['remote_host'], couch_db_config['database'], test_doc_id + '?rev={}'.format(write_result_response_object['_rev']))
    )


def test_couchDB_decorated_function_call_success():
    logging.warn('test_couchDB_decorated_function_call_success')

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
    time.sleep(.2)
    write_result_response = requests.get(
        os.path.join(remote_host, test_db, test_doc_id)
    )
    write_result_response_object = json.loads(write_result_response.text)

    logging.info(write_result_response.text)

    assert(ast.literal_eval(write_result_response_object['args'])[0] == 1)
    assert(ast.literal_eval(write_result_response_object['kwargs'])['some_kwarg'] == 2)
    assert(write_result_response_object['start_time'] is not None)
    assert(write_result_response_object['end_time'] is not None)

    logging.info( os.path.join(remote_host, test_db, test_doc_id + '?rev={}'.format(write_result_response_object['_rev'])) )

    # Clean up
    delete_response = requests.delete(
        os.path.join(remote_host, test_db, test_doc_id + '?rev={}'.format(write_result_response_object['_rev']))
    )

    logging.info(write_result_response_object['_rev'])

    assert(delete_response.status_code == 200)

def test_couchDB_decorated_function_call_multi_concurrent_success():
    logging.warn('test_couchDB_decorated_function_call_multi_concurrent_success')

    remote_host = 'http://52.41.176.213:5984'
    test_db = 'test_decorator'

    couch_db_config = {
        'remote_host': remote_host,
        'database': test_db,
    }

    decorated_foo = decorators.couchDBLogging(foo, couch_db_config)
    message_queue = multiprocessing.Queue()

    subprocs = [
        multiprocessing.Process(
            target=makeFunctionCall,
            args=(decorated_foo, message_queue, couch_db_config, '02', 0, 2),
        ),
        multiprocessing.Process(
            target=makeFunctionCall,
            args=(decorated_foo, message_queue, couch_db_config, '12', 1, 2),
        ),
        multiprocessing.Process(
            target=makeFunctionCall,
            args=(decorated_foo, message_queue, couch_db_config, '22', 2, 2),
        ),
        multiprocessing.Process(
            target=makeFunctionCall,
            args=(decorated_foo, message_queue, couch_db_config, '32', 3, 2),
        ),
        multiprocessing.Process(
            target=makeFunctionCall,
            args=(decorated_foo, message_queue, couch_db_config, '42', 4, 2),
        ),
    ]

    map(lambda proc: proc.start(), subprocs)
    map(lambda proc: proc.join(), subprocs)

    # TODO: get cleanup working: currently queue doesn't get back results ... ?
    logging.error('start cleaning...')
    logging.error(message_queue.empty())
    while not message_queue.empty():
        cleanUpFunctionCall(couch_db_config, *(message_queue.get()))

