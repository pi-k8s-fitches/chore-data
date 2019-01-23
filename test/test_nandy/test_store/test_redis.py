import unittest
import unittest.mock

import os
import time
import json

import nandy.store.redis

class TestNandyRedis(unittest.TestCase):

    maxDiff = None

    @unittest.mock.patch("redis.StrictRedis", nandy.store.redis.MockRedis) 
    def setUp(self):

        self.redis = nandy.store.redis.Channel("test")

    @unittest.mock.patch("redis.StrictRedis", nandy.store.redis.MockRedis) 
    def test___init___(self):

        self.assertEqual(self.redis.channel, "test")
        self.assertEqual(self.redis.redis.host, "redis")
        self.assertEqual(self.redis.redis.port, 6379)

        init = nandy.store.redis.Channel("unit", "floop", 7)

        self.assertEqual(init.channel, "unit")
        self.assertEqual(init.redis.host, "floop")
        self.assertEqual(init.redis.port, 7)

    def test_publish(self):

        self.redis.publish({"a": 1})

        self.assertEqual(self.redis.redis.channel, "test")
        self.assertEqual(self.redis.redis.messages[0], {"data": json.dumps({"a": 1}).encode("utf-8")})

    def test_subscribe(self):

        self.redis.subscribe()

        self.assertEqual(self.redis.redis.channel, "test")

    def test_next(self):

        self.assertIsNone(self.redis.next())

        self.redis.redis.messages.append({"data": json.dumps({"a": 1}).encode("utf-8")})
        self.assertEqual(self.redis.next(), {"a": 1})
        self.assertEqual(self.redis.redis.channel, "test")
