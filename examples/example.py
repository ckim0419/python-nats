# coding: utf-8
import tornado.ioloop
import tornado.gen
import time
from datetime import datetime
from nats.io.client import Client as NATS

@tornado.gen.coroutine
def main():
    nc = NATS()

    # Establish connection to the server.
    yield nc.connect({ "verbose": True, "servers": ["nats://127.0.0.1:4222"] })

    def discover(msg=None):
        print("[Received]: %s" % msg.data)

    sid = yield nc.subscribe("discover", "", discover)
    # Only interested in 2 messages.
    yield nc.auto_unsubscribe(sid, 2)

    loop = tornado.ioloop.IOLoop.instance()
    yield nc.publish("discover", "A")
    yield nc.publish("discover", "B")

    # Following two messages won't be received.
    yield nc.publish("discover", "C")
    yield nc.publish("discover", "D")

    # Request/Response
    def help_request_handler(msg):
        print("[Received]: %s" % msg.data)
        nc.publish(msg.reply, "OK, I can help!")

    # Susbcription using distributed queue
    yield nc.subscribe("help", "workers", help_request_handler)

    try:
        # Expect a single request and timeout after 500 ms
        response = yield nc.timed_request("help", "Hi, need help!", 500)
        print("[Response]: %s" % response.data)
    except tornado.gen.TimeoutError, e:
        print("Timeout! Need to retry...")

    try:
        start = datetime.now()
        # Make roundtrip to the server and timeout after 1000 ms
        yield nc.flush(1)
        end = datetime.now()
        print("Latency: %d µs" % (end.microsecond - start.microsecond))
    except tornado.gen.TimeoutError, e:
        print("Timeout! Flush too slow...")

    yield tornado.gen.Task(loop.add_timeout, time.time() + 1)

if __name__ == '__main__':
    tornado.ioloop.IOLoop.instance().run_sync(main)
