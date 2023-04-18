import unittest
from io import StringIO
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

    def test_extra_fields(self):

        with BufferStream(self.logger) as b:
            self.logger.set_handler_level(b.name, "info")
            self.logger.set_handler_formatter(b.name, JsonFormatter())
            self.logger.info("info", extra={"city": "san francisco", "temp": 72})
            s = str(b)
            s = "".join(s.split())
            s = json.loads(s)
            self.assertEqual(72, s["temp"])


if __name__ == '__main__':
    unittest.main()
