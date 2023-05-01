import random
import unittest
from io import StringIO
from unittest.mock import patch

from edge_logger.edge_logger import *


class BufferStream:
    def __init__(self, logger):
        self.logger = logger
        self._buf = StringIO()
        self.name = "buffer_handler"

    def __enter__(self):
        bh = logging.StreamHandler(self._buf)
        bh.set_name(self.name)
        self.logger.addHandler(bh)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.remove_handler(self.name)

    @property
    def buf(self):
        return self._buf

    def __str__(self):
        return self.buf.getvalue().strip()


class TestLogging(unittest.TestCase):

    def __init__(self, test_name):
        super().__init__(test_name)
        logging.setLoggerClass(EdgeLogger)
        self.logger = logging.getLogger(__name__)

    def test_levels(self):
        with BufferStream(self.logger) as b:
            self.logger.info("info")
            s = str(b)
            s = "".join(s.split())
            self.assertEqual(s, "info")

        with BufferStream(self.logger) as b:
            self.logger.set_handler_level(b.name, "warning")
            self.logger.info("info")
            s = str(b)
            s = "".join(s.split())
            self.assertEqual(s, "")

    def test_levels_info_not_logged(self):
        with BufferStream(self.logger) as b:
            self.logger.info("info")
            s = str(b)
            s = "".join(s.split())
            self.assertEqual(s, "info")

    def test_levels_change_only_handler_level(self):

        with BufferStream(self.logger) as b:
            self.logger.set_handler_level(b.name, "debug")
            self.logger.debug("debug")
            s = str(b)
            s = "".join(s.split())
            self.assertEqual(s, "debug")

    def test_levels_change_base_level(self):

        with BufferStream(self.logger) as b:
            self.logger.set_level("DEBUG")
            self.logger.propagate = False
            self.logger.debug("debug")
            s = str(b)
            s = "".join(s.split())
            self.assertEqual(s, "debug")

    def test_extra_fields(self):
        with BufferStream(self.logger) as b:
            self.logger.set_handler_level(b.name, "info")
            self.logger.set_handler_formatter(b.name, JsonFormatter())
            self.logger.info("info", extra={"city": "san francisco", "temp": 72})
            s = str(b)
            s = "".join(s.split())
            s = json.loads(s)
            self.assertEqual(72, s["temp"])

    def test_multiple_log_instances(self):
        l1 = logging.getLogger(__name__)
        l2 = logging.getLogger(__name__)
        self.assertEqual(id(l1), id(l2))

    def my_post_side_effect(self, *args, **kwargs):
        json_dict = json.loads(kwargs.get("data"))
        self.assertEqual("test_http_handler", json_dict.get("message"))
        self.assertEqual("tests.test_edge_logger", json_dict.get("name"))

    @patch("requests.Session.post")
    def test_http_handler(self, mock_post):
        mock_post.side_effect = self.my_post_side_effect
        hh = CustomHttpHandler(url="https://httpstat.us/200")
        hh.setFormatter(JsonFormatter())
        hh.setLevel("DEBUG")
        self.logger.addHandler(hh)
        self.logger.error(self._testMethodName)

    def test_http_handler_live(self):
        hh = CustomHttpHandler(url="https://httpstat.us/200")
        hh.setFormatter(JsonFormatter())
        hh.setLevel("DEBUG")
        self.logger.addHandler(hh)
        self.logger.info(self._testMethodName, extra={'sequence': random.randint(1, 100000)})


if __name__ == '__main__':
    unittest.main()
