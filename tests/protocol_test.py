import sys

if sys.version_info >= (2, 7):
     import unittest
else:
    import unittest2 as unittest

import tornado.testing
from nats.io.client import Subscription
from nats.protocol.parser import *

class MockNatsClient:

    def __init__(self):
        self._subs = {}
        self._pongs = []
        self._pings_outstanding = 0
        self._pongs_received = 0
        self._server_info = {"max_payload": 1048576, "auth_required": False }

    def send_command(self, cmd):
        pass

    def _process_pong(self):
        pass

    def _process_ping(self):
        pass

    def _process_msg(self, msg):
        pass

    def _process_err(self, err=None):
        pass

class ProtocolParserTest(unittest.TestCase):

    def test_parse_ping(self):
        ps = Parser(MockNatsClient())
        data = b'PING\r\n'
        ps.parse(data)
        self.assertEqual(len(ps.scratch), 0)
        self.assertEqual(ps.state, AWAITING_CONTROL_LINE)

    def test_parse_pong(self):
        ps = Parser(MockNatsClient())
        data = b'PONG\r\n'
        ps.parse(data)
        self.assertEqual(len(ps.scratch), 0)
        self.assertEqual(ps.state, AWAITING_CONTROL_LINE)

    def test_parse_ok(self):
        ps = Parser()
        data = b'+OK\r\n'
        ps.parse(data)
        self.assertEqual(len(ps.scratch), 0)
        self.assertEqual(ps.state, AWAITING_CONTROL_LINE)

    def test_parse_msg(self):
        nc = MockNatsClient()
        expected = b'hello world!'

        def payload_test(msg):
          self.assertEqual(msg["data"], expected)

        sub = Subscription(subject="hello", queue=None, callback=payload_test, future=None)
        nc._subs[1] = sub
        ps = Parser(nc)
        data = b'MSG hello 1 world 12\r\n'
        ps.parse(data)
        self.assertEqual(len(ps.scratch), 0)
        self.assertEqual(len(ps.msg_arg.keys()), 3)
        self.assertEqual(ps.msg_arg["subject"], "hello")
        self.assertEqual(ps.msg_arg["reply"], "world")
        self.assertEqual(ps.msg_arg["sid"], 1)
        self.assertEqual(ps.needed, 12)
        self.assertEqual(ps.state, AWAITING_MSG_PAYLOAD)

        ps.parse(expected)
        self.assertEqual(len(ps.scratch), 0)
        self.assertEqual(ps.state, AWAITING_MSG_END)

        data = b'\r\n'
        ps.parse(data)
        self.assertEqual(len(ps.scratch), 0)
        self.assertEqual(ps.state, AWAITING_CONTROL_LINE)

    def test_parse_msg_op(self):
        ps = Parser()
        data = b'MSG hello'
        ps.parse(data)
        self.assertEqual(len(ps.scratch), 9)
        self.assertEqual(ps.state, AWAITING_MSG_ARG)

    def test_parse_err_op(self):
        ps = Parser()
        data = b"-ERR 'Slow..."
        ps.parse(data)
        self.assertEqual(len(ps.scratch), 13)
        self.assertEqual(ps.state, AWAITING_MINUS_ERR_ARG)

    def test_parse_err(self):
        ps = Parser(MockNatsClient())
        data = b"-ERR 'Slow consumer'\r\n"
        ps.parse(data)
        self.assertEqual(len(ps.scratch), 0)
        self.assertEqual(ps.state, AWAITING_CONTROL_LINE)

    @unittest.skip("INFO parsing only done on connect by the Client before CONNECT")
    def test_parse_info(self):
        ps = Parser()
        data = b'INFO {"server_id":"eec6c3","version":"0.6.6","go":"go1.4.2","host":"0.0.0.0","port":4222,"auth_required":false,"ssl_required":false,"max_payload":1048576}\r\n'
        ps.parse(data)
        self.assertEqual(ps.state, None)

if __name__ == '__main__':
    runner = unittest.TextTestRunner(stream=sys.stdout)
    unittest.main(verbosity=1, exit=False, testRunner=runner)
