# Embedded file name: ..\Resources\logging.py
from __future__ import absolute_import
import os
import sys
import logging
import traceback
import logging.handlers
__LOGGING_INITIALIZED = False
__LOGGER = None
__HANDLER = None

def initialize_logging():
    global __LOGGER
    global __LOGGING_INITIALIZED
    global __HANDLER
    if __LOGGING_INITIALIZED:
        return
    __LOGGING_INITIALIZED = True
    if sys.platform == 'darwin':
        fname = os.path.join(os.path.expanduser('~'), 'Library', 'Logs', 'Shotgun', 'tk-desktop.log')
    elif sys.platform == 'win32':
        fname = os.path.join(os.environ.get('APPDATA', 'APPDATA_NOT_SET'), 'Shotgun', 'tk-desktop.log')
    elif sys.platform.startswith('linux'):
        fname = os.path.join(os.path.expanduser('~'), '.shotgun', 'logs', 'tk-desktop.log')
    else:
        raise NotImplementedError('Unknown platform: %s' % sys.platform)
    log_dir = os.path.dirname(fname)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    __LOGGER = logging.getLogger('tk-desktop')
    __HANDLER = logging.handlers.RotatingFileHandler(fname, maxBytes=1048576, backupCount=5)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    __HANDLER.setFormatter(formatter)
    __LOGGER.addHandler(__HANDLER)
    if os.environ.get('TK_DESKTOP_DEBUG'):
        __LOGGER.setLevel(logging.DEBUG)
    else:
        __LOGGER.setLevel(logging.INFO)

    class _TopLevelExceptionHandler(object):

        def __init__(self):
            self._current_hook = sys.excepthook

        def _handle(self, etype, evalue, etb):
            if self._current_hook:
                self._current_hook(etype, evalue, etb)
            lines = traceback.format_exception(etype, evalue, etb)
            lines.insert(0, lines.pop())
            logging.getLogger('tk-desktop').error('\n'.join(lines))

    sys.excepthook = _TopLevelExceptionHandler()._handle


def tear_down_logging():
    global __HANDLER
    global __LOGGER
    global __LOGGING_INITIALIZED
    if not __LOGGING_INITIALIZED:
        return
    else:
        __LOGGING_INITIALIZED = False
        __LOGGER.removeHandler(__HANDLER)
        __HANDLER = None
        __LOGGER = None
        return