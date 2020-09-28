# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division

import logging

try:
    unicode
except NameError:
    basestring = unicode = str

try:
    from logging import NullHandler
except ImportError:
    # Copied from the Python 2.7 source code.
    class NullHandler(logging.Handler):
        """
        This handler does nothing. It's intended to be used to avoid the
        "No handlers could be found for logger XXX" one-off warning. This is
        important for library code, which may contain code to log events. If a user
        of the library does not configure logging, the one-off warning might be
        produced; to avoid this, the library developer simply needs to instantiate
        a NullHandler and add it to the top-level logger of the library module or
        package.
        """

        def handle(self, record):
            pass

        def emit(self, record):
            pass

        def createLock(self):
            self.lock = None


LEVEL_MAP = dict(
    DEBUG=logging.DEBUG,
    INFO=logging.INFO,
    WARN=logging.WARN,
    ERROR=logging.ERROR,
    CRITICAL=logging.CRITICAL,
)


def setup():
    logging.getLogger("sc2reader").addHandler(NullHandler())


def log_to_file(filename, level="WARN", format=None, datefmt=None, **options):
    add_log_handler(logging.FileHandler(filename, **options), level, format, datefmt)


def log_to_console(level="WARN", format=None, datefmt=None, **options):
    add_log_handler(logging.StreamHandler(**options), level, format, datefmt)


def add_log_handler(handler, level="WARN", format=None, datefmt=None):
    handler.setFormatter(logging.Formatter(format, datefmt))

    if isinstance(level, basestring):
        level = LEVEL_MAP[level]

    logger = logging.getLogger("sc2reader")
    logger.setLevel(level)
    logger.addHandler(handler)


def get_logger(entity):
    """
    Retrieves loggers from the enties fully scoped name.

        get_logger(Replay)     -> sc2reader.replay.Replay
        get_logger(get_logger) -> sc2reader.utils.get_logger

    :param entity: The entity for which we want a logger.
    """
    try:
        return logging.getLogger(entity.__module__ + "." + entity.__name__)

    except AttributeError:
        raise TypeError("Cannot retrieve logger for {0}.".format(entity))


def loggable(cls):
    cls.logger = get_logger(cls)
    return cls
