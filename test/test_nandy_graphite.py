import unittest
import unittest.mock

import os
import json

import graphyte

import nandy_graphite

class MockGraphyteSender(object):

    def __init__(self, host, port, prefix):

        self.host = host
        self.port = port
        self.prefix = prefix

        self.messages = []

    def send(self, name, value, timestamp):

        self.messages.append({
            "name": name,
            "value": value,
            "timestamp": timestamp
        })

class TestNandyGraphite(unittest.TestCase):

    maxDiff = None

    @unittest.mock.patch("graphyte.Sender", MockGraphyteSender)
    def setUp(self):

        self.nandy_graphite = nandy_graphite.Graphite()

    @unittest.mock.patch("graphyte.Sender", MockGraphyteSender) 
    def test___init___(self):

        self.assertEqual(self.nandy_graphite.sender.host, "graphite")
        self.assertEqual(self.nandy_graphite.sender.port, 2003)
        self.assertEqual(self.nandy_graphite.sender.prefix, "nandy")

        init = nandy_graphite.Graphite("unit", 7, "test")

        self.assertEqual(init.sender.host, "unit")
        self.assertEqual(init.sender.port, 7)
        self.assertEqual(init.sender.prefix, "test")

    def test_send(self):

        self.nandy_graphite.send("this   is", "totally $^&*& cray", 1, 7)
        self.assertEqual(self.nandy_graphite.sender.messages, [{
            "name": "this_is.totally_cray",
            "value": 1,
            "timestamp": 7
        }])
