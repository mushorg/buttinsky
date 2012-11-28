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
        self.__stackList = {}

    def addStack(self, identifier, stack):
        self.__stackList[identifier] = stack

    def getStack(self, identifier=None):
        if identifier == None:
            return self.__stackList
        stack = None
        try:
            stack = self.__stackList[identifier]
        except:
            pass
        return stack

    def removeStack(self, identifier):
        stack = self.getStack(identifier)
        if stack != None:
            del self.__stackList[identifier]
        return stack

CONFIG_MONITOR  = 0
STOP_MONITOR    = 1
RESTART_MONITOR = 2

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
            msg_type = data[0]
            identifier = data[1]

            if msg_type == STOP_MONITOR:
                print "MonitorSpawner: received stop"
                stack = self.ml.removeStack(identifier)
                if stack != None:
                    stack.disconnect()
                continue

            if msg_type == RESTART_MONITOR:
                print "MonitorSpawner: received restart"
                stack = self.ml.getStack(identifier)
                if stack != None:
                    stack.disconnect()
                    group.spawn(stack.connect)
                continue

            
            print "MonitorSpawner: received config"
            net_settings = data[2]
            client = gevent_client.Client(net_settings["host"],
                                          net_settings["port"])

            # layer_network <-> layer_log <-> layer_protocol <-> layer_behavior
            layer_network = Layer(gevent_client.Layer1(client))
            layer_log = Layer(reporter_handler.ReporterHandler(), layer_network)
            layer_protocol = Layer(irc.IRCProtocol(), layer_log)
            layer_behavior = Layer(simple_response.SimpleResponse(), layer_protocol)

            layer_protocol.settings(net_settings)

            layer_log.setUpper(layer_protocol)
            layer_network.setUpper(layer_log)
            layer_protocol.setUpper(layer_behavior)

            client.setLayer1(layer_network)
            group.spawn(client.connect)
            self.ml.addStack(identifier, client)


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
        self.queue.put([CONFIG_MONITOR, identifier, config])
        json_data.close()
        return "Load command, recv id: " + identifier

    def create(self, identifier, config):
        data = json.loads(config)
        config = data["config"]
        self.queue.put([identifier, config])
        return "Create command, recvd id: " + identifier

    def status(self):
        return "Status command recvd"
        #return self.ml.get()

    def stop(self, identifier):
        self.queue.put([STOP_MONITOR, identifier, None])
        return "Stop command, recvd id: " + identifier

    def restart(self, identifier):
        self.queue.put([RESTART_MONITOR, identifier, None])
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

