"""
Main module for interacting with Nandy in Redis
"""

import os
import json

import redis


class Channel(object):

    def __init__(self, channel, host=None, port=None):

        self.channel = channel
        self.redis = redis.StrictRedis(host=host or os.environ["REDIS_HOST"], port=port or int(os.environ["REDIS_PORT"]))
        self.pubsub = None

    def publish(self, data):
        """
        Sends a message to the channel
        """

        self.redis.publish(self.channel, json.dumps(data))

    def subscribe(self):
        """
        Subscribes to the channel on Redis
        """

        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(self.channel) 

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
