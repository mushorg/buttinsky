#!/usr/bin/env python
# Copyright (C) 2012 Buttinsky Developers.
# See 'COPYING' for copying permission.

import gevent
import json

from gevent.server import StreamServer
from gevent import queue

from event_loops import gevent_client
from configobj import ConfigObj

from protocols import irc
from behaviors import simple_response
from modules import reporter_handler
from stack import Layer

import gevent.pool
group = gevent.pool.Group()


def singleton(cls):
    instances = {}
    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getinstance

@singleton
class MonitorList(object):

    def __init__(self):
        self.__list = {}

    def add(self, identifier, stack):
        self.__list[identifier] = stack

    def get(self, identifier=None):
        if identifier == None:
            return self.__list
        stack = None
        try:
            stack = self.__list[identifier]
        except:
            pass
        return stack

    def remove(self, identifier):
        stack = self.get(identifier)
        if stack != None:
            del self.__list[identifier]
        return stack

class MonitorSpawner(object):

    def __init__(self, queue):
        self.messageQueue = queue
        self.ml = MonitorList()

    def work(self):
        try:
            g = gevent.spawn(self.listen)
            g.join()
        finally:
            g.kill()

    def listen(self):
        while True:
            data = self.messageQueue.get()
            print "MonitorSpawner: received config"
            self.ml.add(data[0], data[1])
            #group.spawn()


from SimpleXMLRPCServer import SimpleXMLRPCServer
from gevent.monkey import patch_all
patch_all()

class ButtinskyXMLRPCServer(object):
    
    def __init__(self, messageQueue):
        self.ml = MonitorList()
        self.queue = messageQueue

    def load(self, identifier, filename):
        json_data = open('settings/' + filename)
        data = json.load(json_data)
        config = data["config"]
        self.queue.put([identifier, config])
        json_data.close()
        return "Load command, recv id: " + identifier

    def create(self, identifier, config):
        data = json.loads(config)
        config = data["config"]
        self.queue.put([identifier, config])
        return "Create command, recvd id: " + identifier

    def status(self):
        return self.ml.get()

    def stop(self, identifier):
        return "Stop command, recvd id: " + identifier

    def restart(self, identifier):
        return "Restart command, recvd id: " + identifier

    def delete(self, identifier):
        return "Delete command, recvd id: " + identifier

    def echo(self, msg):
        return "Msg recvd: " + msg

if __name__ == '__main__':
    messageQueue = queue.Queue()
    gevent.spawn(MonitorSpawner(messageQueue).work)
    server = SimpleXMLRPCServer(("localhost", 8000))
    print "Listening on port 8000..."
    server.register_instance(ButtinskyXMLRPCServer(messageQueue))
    server.serve_forever()

