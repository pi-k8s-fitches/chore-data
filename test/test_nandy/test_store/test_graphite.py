import unittest
import unittest.mock

import os
import json

import graphyte

import nandy.store.graphite

class TestNandyGraphite(unittest.TestCase):

    maxDiff = None

    @unittest.mock.patch("graphyte.Sender", nandy.store.graphite.MockGraphyteSender)
    def setUp(self):

        self.graphite = nandy.store.graphite.Graphite()

    @unittest.mock.patch("graphyte.Sender", nandy.store.graphite.MockGraphyteSender) 
    def test___init___(self):

        self.assertEqual(self.graphite.sender.host, "graphite")
        self.assertEqual(self.graphite.sender.port, 2003)
        self.assertEqual(self.graphite.sender.prefix, "nandy")

        init = nandy.store.graphite.Graphite("unit", 7, "test")

        self.assertEqual(init.sender.host, "unit")
        self.assertEqual(init.sender.port, 7)
        self.assertEqual(init.sender.prefix, "test")

    def test_send(self):

        self.graphite.send("this   is", "totally $^&*& cray", 1, 7)
        self.assertEqual(self.graphite.sender.messages, [{
            "name": "this_is.totally_cray",
            "value": 1,
            "timestamp": 7
        }])
