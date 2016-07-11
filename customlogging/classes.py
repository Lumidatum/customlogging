import multiprocessing
import os

import requests

import constants
import decorators
import helpers


class LoggingWrapper(object):

    # Exclude __init__ by default...
    # Local plain text file by default...
    config = {
        'exclude': set(['__init__']),
        'include': set(),
        'output_type': constants.LOCAL_PLAIN_TEXT_FILE,
    }

    @classmethod
    def setup(
        cls,
        lumidatum_user_id,
        lumidatum_model_id,
        couch_db_config=None,
        output_text_file=None,
        output_json_file=None,
        output_sqlite3_location=None,
        include_methods=None,
        exclude_methods=None,
        s3=False
    ):
        """
        Change static class configuration for all subsequent instantiations.
        """
        # Method exclusion takes priority if both are provided.
        if exclude_methods:
            for method in exclude_methods:
                cls.config['exclude'].add(method)
            cls.config['include'] = set()
        elif include_methods:
            for method in include_methods:
                cls.config['include'].add(method)
            cls.config['exclude'] = set()

        # Set user Id and model Id and log for all types
        cls.config['lumidatum_user_id'] = lumidatum_user_id
        cls.config['lumidatum_model_id'] = lumidatum_model_id

        # NoSQL
        # CouchDB
        if couch_db_config:
            cls.config['output_type'] = constants.REMOTE_COUCH_DB
            cls.config['remote_host'] = couch_db_config['remote_host']
            cls.config['database'] = 'user_{}_model{}'.format(lumidatum_user_id, lumidatum_model_id)

            # Ensure the database is created in CouchDB
            db_init_proc = multiprocessing.Process(
                target=helpers.sendLoggingMessage,
                args=(requests.put, os.path.join(cls.config['remote_host'], cls.config['database']), None)
            )
            db_init_proc.start()

        # JSON file
        elif output_json_file:
            cls.config['output_type'] = constants.LOCAL_JSON_FILE
            cls.config['output_file'] = output_json_file

        # sqllite3 file
        elif output_sqllite3_location:
            cls.config['output_type'] = constants.LOCAL_SQLLITE3
            cls.config['output_file'] = output_sqlite3_location

        # Amazon S3
        # Plain text file

        # JSON file

        # sqllite3 file

        # TOCONSIDER: Azure?

        # Default to local output text file
        else:
            cls.config['output_type'] = constants.LOCAL_PLAIN_TEXT_FILE
            cls.config['output_file'] = output_text_file if output_text_file else 'customlogging.out'

    def __init__(self, model_class, selected_decorator, *args, **kwargs):
        undecorated_model = model_class(*args, **kwargs)
        # decorated_class = decorators.classLoggingDecorator(model_class, type(self).config)
        self.model = undecorated_model
        # self.model = decorated_class(*args, **kwargs)

        for attr in model_class.__dict__:
            if callable(getattr(model_class, attr)) and attr not in self.config.get('exclude', set()):
                print repr(undecorated_model)
                print repr(attr)
                setattr(self, attr, selected_decorator(getattr(undecorated_model, attr), self.config))
