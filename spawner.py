#!/usr/bin/env python
# Copyright (C) 2012 Buttinsky Developers.
# See 'COPYING' for copying permission.

import json
import os

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
        self.__settingList = {}
        self.__fileList = {}

    def addStack(self, identifier, stack):
        self.__stackList[identifier] = stack

    def addSetting(self, identifier, setting):
        self.__settingList[identifier] = setting

    def addFile(self, identifier, filename):
        self.__fileList[identifier] = filename

    def getStack(self, identifier=None):
        if identifier == None:
            return self.__stackList
        stack = None
        try:
            stack = self.__stackList[identifier]
        except:
            pass
        return stack

    def getSetting(self, identifier=None):
        if identifier == None:
            return self.__settingList
        setting = None
        try:
            setting = self.__settingList[identifier]
        except:
            pass
        return setting

    def getFile(self, identifier=None):
        if identifier == None:
            return self.__fileList
        filename = None
        try:
            filename = self.__fileList[identifier]
        except:
            pass
        return filename

    def removeStack(self, identifier):
        stack = self.getStack(identifier)
        if stack != None:
            del self.__stackList[identifier]
        return stack

    def removeSetting(self, identifier):
        setting = self.getSetting(identifier)
        if setting != None:
            del self.__settingList[identifier]
        return setting

    def removeFile(self, identifier):
        filename = self.getFile(identifier)
        if filename != None:
            del self.__fileList[identifier]
        return filename


CONFIG_MONITOR = 0
STOP_MONITOR = 1
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

            if msg_type == STOP_MONITOR or msg_type == RESTART_MONITOR:
                stack = self.ml.removeStack(identifier)
                setting = self.ml.removeSetting(identifier)
                filename = self.ml.removeFile(identifier)
                if stack != None:
                    stack.disconnect()
                    group.killone(stack.connect)
                    if msg_type == RESTART_MONITOR:
                        self.spawnMonitor(identifier, setting, filename)
                continue

            if msg_type == CONFIG_MONITOR:
                self.spawnMonitor(identifier, data[2], data[3])

    def spawnMonitor(self, identifier, net_settings, filename):
            client = gevent_client.Client(net_settings["host"],
                                          net_settings["port"])
            # layer_network <-> layer_log <-> layer_protocol <-> layer_behavior
            layer_network = Layer(gevent_client.Layer1(client))

            log_plugins = [p.strip() for p in net_settings["log_plugins"].split(",")]
            layer_log = Layer(reporter_handler.ReporterHandler(log_plugins),
                              layer_network)

            if net_settings["protocol_plugin"] == "irc":
                proto = irc.IRCProtocol()
            
            layer_protocol = Layer(proto, layer_log)
            layer_behavior = Layer(simple_response.SimpleResponse(),
                                   layer_protocol)
            layer_protocol.settings(net_settings)

            layer_log.setUpper(layer_protocol)
            layer_network.setUpper(layer_log)
            layer_protocol.setUpper(layer_behavior)
    
            client.setLayer1(layer_network)
            group.spawn(client.connect)
            self.ml.addStack(identifier, client)
            self.ml.addSetting(identifier, net_settings)
            self.ml.addFile(identifier, filename)


from SimpleXMLRPCServer import SimpleXMLRPCServer
from gevent.monkey import patch_all
patch_all()


class ButtinskyXMLRPCServer(object):

    def __init__(self, messageQueue):
        self.ml = MonitorList()
        self.queue = messageQueue

    def load(self, identifier, filename):
        if self.ml.getStack(identifier):
            raise Exception("Identifier " + identifier + " already exist")
        json_data = open('settings/' + filename)
        data = json.load(json_data)
        config = data["config"]
        self.queue.put([CONFIG_MONITOR, identifier, config, filename])
        json_data.close()
        return ""

    def create(self, filename, config):
        path = "settings/" + filename
        if os.path.isfile(path):
            raise Exception("File " + path + " already exist")
        f = open(path, 'w')
        f.write(json.loads(config))
        f.close()
        return ""

    def status(self):
        status = self.ml.getFile()
        root = "settings/"
        status[""] = list()
        for path, subdirs, files in os.walk(root):
            for name in files:
                filename = os.path.join(path, name).split(root)[1]
                if filename not in status.values():
                    status[""].append(filename)
        return status

    def stop(self, identifier):
        if not self.ml.getStack(identifier):
            raise Exception("Identifier " + identifier + " does not exist")
        self.queue.put([STOP_MONITOR, identifier, None])
        return ""

    def restart(self, identifier):
        if not self.ml.getStack(identifier):
            raise Exception("Identifier " + identifier + " does not exist")
        self.queue.put([RESTART_MONITOR, identifier, None])
        return ""

    def list(self, filename):
        f = open("settings/" + filename, "r")
        content = f.read()
        return content

    def delete(self, filename):
        os.remove("settings/" + filename)
        return ""

    def echo(self, msg):
        return "Msg recvd: " + msg

if __name__ == '__main__':
    messageQueue = queue.Queue()
    gevent.spawn(MonitorSpawner(messageQueue).work)
    buttinsky_config = ConfigObj("conf/buttinsky.cfg")
    hostname = buttinsky_config["xmlrpc"]["server"]
    port = int(buttinsky_config["xmlrpc"]["port"])
    server = SimpleXMLRPCServer((hostname, port))
    print "Listening on port 8000..."
    server.register_instance(ButtinskyXMLRPCServer(messageQueue))
    server.serve_forever()
