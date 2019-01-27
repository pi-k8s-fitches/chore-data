"""
Main module for interacting with Nandy in Redis
"""

import os
import json

import redis


class Channel(object):

    def __init__(self, channel, host=None, port=None, prefix=None):

        self.channel = channel
        self.redis = redis.StrictRedis(host=host or os.environ["REDIS_HOST"], port=port or int(os.environ["REDIS_PORT"]))
        self.prefix = prefix or "nandy"
        self.pubsub = None

    def publish(self, data):
        """
        Sends a message to the channel
        """

        self.redis.publish(f"{self.prefix}/{self.channel}", json.dumps(data))

    def subscribe(self):
        """
        Subscribes to the channel on Redis
        """

        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(f"{self.prefix}/{self.channel}") 

    def next(self):
        """
        Gets the next message from the speech channel
        """

        if not self.pubsub:
            self.subscribe()

        message = self.pubsub.get_message()

        if not message or "data" not in message or not isinstance(message["data"], bytes):
            return None

        return json.loads(message['data'])


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
