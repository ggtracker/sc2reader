import logging

LEVEL_MAP = dict(
    DEBUG=logging.DEBUG,
    INFO=logging.INFO,
    WARN=logging.WARN,
    ERROR=logging.ERROR,
    CRITICAL=logging.CRITICAL
)

def setup():
    logging.getLogger('sc2reader').addHandler(logging.NullHandler())

def log_to_file(filename, level='WARN', format=None, datefmt=None, **options):
    add_log_handler(logging.FileHandler(filename, **options),level, format, datefmt)

def log_to_console(level='WARN', format=None, datefmt=None, **options):
    add_log_handler(logging.StreamHandler(**options),level, format, datefmt)

def add_log_handler(handler, level='WARN', format=None, datefmt=None):
    handler.setFormatter(logging.Formatter(format, datefmt))

    if isinstance(level, basestring):
        level = LEVEL_MAP[level]

    logger = logging.getLogger('sc2reader')
    logger.setLevel(level)
    logger.addHandler(handler)

def get_logger(entity):
    """
        Retrieves loggers from the enties fully scoped name. Accepts strings,
        classes, and functions.

            get_logger(Replay)     -> sc2reader.replay.Replay
            get_logger(__name__)   -> sc2reader.utils
            get_logger(get_logger) -> sc2reader.utils.get_logger

        :param entity: The entity for which we want a logger.
    """
    try:
        if isinstance(entity, basestring):
            return logging.getLogger(entity)
        else:
            return logging.getLogger(entity.__module__+'.'+entity.__name__)

    except AttributeError as e:
        msg = "Cannot retrieve logger for {0}. Only strings, classes, and functions supported."
        raise TypeError(msg.format(entity))