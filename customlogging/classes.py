import constants
import decorators


class LoggingWrapper(object):

    # Exclude __init__ by default...
    config = {
        'exclude': set('__init__'),
        'include': set()
    }

    @classmethod
    def setupWrapper(
        cls,
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
                config['exclude'].add(method)
            config['include'] = set()
        elif include_methods:
            for method in include_methods:
                config['include'].add(method)
            config['exclude'] = set()

        # NoSQL
        # CouchDB
        if couch_db_config:
            cls.config = {'output_type': constants.REMOTE_COUCH_DB}

        # JSON file
        elif output_json_file:
            cls.config = {'output_type': constants.LOCAL_JSON_FILE}

        # sqllite3 file
        elif output_sqllite3_location:
            cls.config = {'output_type': constants.LOCAL_SQLLITE3}

        # Amazon S3
        # Plain text file

        # JSON file

        # sqllite3 file

        # TOCONSIDER: Azure?

        # Default to local output text file
        else:
            cls.config = {'output_type': constants.LOCAL_PLAIN_TEXT_FILE}

    # TODO: expose methods with appropriate names
    # TODO: 
    def __init__(self, model_class, *args, **kwargs):
        decorated_class = decorators.classLoggingDecorator(model_class, type(self).config)
        self.model = decorated_class(*args, **kwargs)

    # decorate all methods with logging