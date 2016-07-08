from functools import wraps
import datetime
import logging


def functionLoggingDecorator(func, selected_logger):
    @wraps(func)
    def wrapper(*args, **kwargs):
        string_args = repr(args)
        string_kwargs = repr(kwargs)
        selected_logger.info('[{}] before func: {} args: {} kwargs: {}'.format(datetime.datetime.utcnow().isoformat(), func.__name__, args, kwargs))
        # logging.info('[{}] before func: {} args: {} kwargs: {}'.format(datetime.datetime.utcnow().isoformat(), func.__name__, args, kwargs))
        # logging.info(datetime.datetime.utcnow().isoformat(), string_args, string_kwargs)
        results = func(*args, **kwargs)
        selected_logger.info('[{}] after'.format(datetime.datetime.utcnow().isoformat()))
        # logging.info(datetime.datetime.utcnow().isoformat(), repr(results), string_args, string_kwargs)
        # logging.info('[{}] after'.format(datetime.datetime.utcnow().isoformat()))

        return results

    return wrapper

# TODO, this modifies the class itself, -> on next call it will wrap the wrapped class...
def classLoggingDecorator(cls, config):
    # TODO: switch function decorators based on config
    selected_decorator = functionLoggingDecorator
    selected_logger = logging
    # Setup logger as needed...

    for attr in cls.__dict__:
        if callable(getattr(cls, attr)) and attr not in config.get('exclude', set()):
            print repr(cls)
            print repr(attr)
            setattr(cls, attr, selected_decorator(getattr(cls, attr), selected_logger))

    return cls

# import logging
# logging.basicConfig(filename='wrappertest.log', level=logging.INFO)

# class thing(object):
#     def __init__(self, a):
#         self.a = a
#     def yo(self, b):
#         print "yoarr", self.a, b

# import loggingwrapper.classes
# testobj = loggingwrapper.classes.LoggingWrapper(thing, '123')
