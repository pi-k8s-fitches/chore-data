import unittest
import unittest.mock

import os
import time
import json

import nandy_redis

class MockRedis(object):

    def __init__(self, host, port):

        self.host = host
        self.port = port
        self.channel = None

        self.data = {}
        self.messages = []

    def publish(self, channel, message):

        self.channel = channel
        self.messages.append({"data": message.encode("utf-8")})

    def pubsub(self):

        return self

    def subscribe(self, channel):

        self.channel = channel

    def get_message(self):

        if self.messages:
            return self.messages.pop(0)  

class TestNandyRedis(unittest.TestCase):

    maxDiff = None

    @unittest.mock.patch("redis.StrictRedis", MockRedis) 
    def setUp(self):

        self.nandy_redis = nandy_redis.Channel("test")

    @unittest.mock.patch("redis.StrictRedis", MockRedis) 
    def test___init___(self):

        self.assertEqual(self.nandy_redis.channel, "test")
        self.assertEqual(self.nandy_redis.redis.host, "redis")
        self.assertEqual(self.nandy_redis.redis.port, 6379)

        init = nandy_redis.Channel("unit", "floop", 7)

        self.assertEqual(init.channel, "unit")
        self.assertEqual(init.redis.host, "floop")
        self.assertEqual(init.redis.port, 7)

    def test_publish(self):

        self.nandy_redis.publish({"a": 1})

        self.assertEqual(self.nandy_redis.redis.channel, "test")
        self.assertEqual(self.nandy_redis.redis.messages[0], {"data": json.dumps({"a": 1}).encode("utf-8")})

    def test_subscribe(self):

        self.nandy_redis.subscribe()

        self.assertEqual(self.nandy_redis.redis.channel, "test")

    def test_next(self):

        self.assertIsNone(self.nandy_redis.next())

        self.nandy_redis.redis.messages.append({"data": json.dumps({"a": 1}).encode("utf-8")})
        self.assertEqual(self.nandy_redis.next(), {"a": 1})
        self.assertEqual(self.nandy_redis.redis.channel, "test")
