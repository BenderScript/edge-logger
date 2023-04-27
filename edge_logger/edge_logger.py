import logging
import json
import sys
import concurrent.futures
from typing import Mapping, Any

import requests
from requests.adapters import HTTPAdapter, Retry


# https://stackoverflow.com/questions/51525237/how-to-set-up-httphandler-for-python-logging
class CustomHttpHandler(logging.Handler):
    def __init__(self, url: str):
        """
        Initializes the custom http handler
        Parameters:
            url (str): The URL that the logs will be sent to
        """
        self.url = url
        #self.token = token

        # sets up a session with the server
        self.MAX_POOLSIZE = 100
        self.session = session = requests.Session()
        session.headers.update({
            'Content-Type': 'application/json'
        })

        self.session.mount('https://', HTTPAdapter(
            max_retries=Retry(
                total=5,
                backoff_factor=0.5,
                status_forcelist=[403, 500]
            ),
            pool_connections=self.MAX_POOLSIZE,
            pool_maxsize=self.MAX_POOLSIZE
        ))

        super().__init__()

    def emit_process_entry(self, record):
        json_log = self.format(record)
        response = self.session.post(self.url, data=json_log)
        return response

    def emit(self, record):
        """
        This function gets called when a log event gets emitted. It receives a
        record, formats it and sends it to the url
        Parameters:
            record: a log record
        """
        # self.emit_process_entry(record)
        with concurrent.futures.ProcessPoolExecutor() as executor:
            future = executor.submit(self.emit_process_entry, record)


class JsonFormatter(logging.Formatter):

    def __init__(self, indent=False):
        super().__init__()
        self._indent = indent

    def format(self, record):
        log_data = {
            'time': self.formatTime(record),
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage(),
            # 'line': record.lineno,
        }
        # If we added extra information, update log record
        if record.__getattribute__("_extra"):
            log_data.update(record.__getattribute__("_extra"))
        if self._indent:
            return json.dumps(log_data, indent=4)
        else:
            return json.dumps(log_data)


class EdgeLogger(logging.Logger):
    """
    Subclass logging.Logger so we can extend makeRecord to add dynamic information on a per-log basis
    https://docs.python.org/3/library/logging.html#logging.Logger
    """

    def __init__(self, name: str, stream=sys.stdout):
        super().__init__(name)

        # Base logger level. Messages will be further filtered by each handler.
        self.setLevel(logging.DEBUG)

        # create console handler and set level to info
        ch = logging.StreamHandler(stream=stream)
        ch.set_name("console_handler")

        # Console handler log level will filter the messages that are actually sent to stdout.
        ch.setLevel(logging.INFO)
        ch.setFormatter(JsonFormatter())

        # add ch to logger
        self.addHandler(ch)

    def makeRecord(
            self,
            name: str,
            level: int,
            fn: str,
            lno: int,
            msg: object,
            args: Any,
            exc_info: Any | None,
            func: str | None = ...,
            extra: Mapping[str, object] | None = ...,
            sinfo: str | None = ...,
    ) -> logging.LogRecord:
        """
        # Patch makeRecord so that we can add information dynamically to each log
        # https://stackoverflow.com/questions/59176101/extract-the-extra-fields-in-logging-call-in-log-formatter
        # https://github.com/symbolix/xlog_example/blob/master/xlog.py
        """
        record = logging.Logger.makeRecord(self, name, level, fn, lno, msg, args, exc_info, func, extra, sinfo)
        record._extra = extra
        return record

    def set_level(self, level):
        # Set up logger with desired log level
        log_level = getattr(logging, level.upper(), None)
        if not isinstance(log_level, int):
            raise ValueError('Invalid log level: %s' % level)
        self.setLevel(log_level)

    def remove_handler(self, handler_name: str):
        for handler in self.handlers:
            if handler.get_name() == handler_name:
                self.removeHandler(handler)
                break
        else:
            return False
        return True

    def set_handler_level(self, handler_name: str, level: str):
        log_level = getattr(logging, level.upper(), None)
        if not isinstance(log_level, int):
            raise ValueError('Invalid log level: %s' % level)
        for handler in self.handlers:
            if handler.get_name() == handler_name:
                handler.setLevel(log_level)
                break
        else:
            return False
        return True

    def set_handler_formatter(self, handler_name: str, formatter: logging.Formatter):
        for handler in self.handlers:
            if handler.get_name() == handler_name:
                handler.setFormatter(formatter)
                break
        else:
            return False
        return True

    def get_handlers(self):
        return self.handlers
