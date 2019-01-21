import os 
import re

import graphyte

SANITIZE = re.compile(r'\W+')

class Graphite(object):

    def __init__(self, host=None, port=None, prefix=None):

        self.sender = graphyte.Sender(host or os.environ["GRAPHITE_HOST"], port=port or int(os.environ["GRAPHITE_PORT"]), prefix=prefix or "nandy")

    def send(self, *args):

        self.sender.send(".".join([SANITIZE.sub('_', arg) for arg in args[:-2]]), args[-2], args[-1])