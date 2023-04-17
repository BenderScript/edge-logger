import logging
import json
import sys
from typing import Mapping, Any


# https://github.com/tomoum/logzilla/blob/main/src/logzilla/logzilla.py#L145
class ColorFormatter(logging.Formatter):
    """Custom formatter for logging module"""

    white = "\x1b[37;20m"
    green = "\x1b[32;20m"
    blue = "\x1b[34;20m"
    cyan = "\x1b[36;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    def __init__(self) -> None:
        super().__init__()
        self.formats = {
            logging.DEBUG: self.cyan + "%(message)s" + self.reset,
            logging.INFO: self.green + "%(message)s" + self.reset,
            logging.WARNING: self.yellow + "%(message)s" + self.reset,
            logging.ERROR: self.red + "%(message)s" + self.reset,
            logging.CRITICAL: self.bold_red + "%(message)s" + self.reset,
        }

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
        log_fmt = self.formats.get(record.levelno)
        record.msg = json.dumps(log_data)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class JsonFormatter(logging.Formatter):
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
        return json.dumps(log_data, indent=4)


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
