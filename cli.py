#!/usr/bin/env python
# Copyright (C) 2012 Buttinsky Developers.
# See 'COPYING' for copying permission.

import cmd
import sys
import gevent 

from configobj import ConfigObj

from event_loops import gevent_client
from gevent import queue

import gevent.pool

from protocols import irc
from behaviors import simple_response
from modules import reporter_handler

from stack import Layer

group = gevent.pool.Group()

import select
from gevent.monkey import patch_all
patch_all(os=True, select=True)


def raw_input(message):
    """
    Non-blocking raw_input from stdin.
    """

    sys.stdout.write(message)
    select.select([sys.stdin], [], [])
    return sys.stdin.readline()

class MonitorSpawner(object):

    def __init__(self, queue):
        self.queue = queue

    def work(self):
        try:
            g = gevent.spawn(self.listen)
            g.join()
        finally:
            g.kill()

    def listen(self):
        while True:
            net_settings = self.queue.get()
            set_nick = "NICK %s\r\n" % net_settings["nick"]
            set_user = "USER %s %s bla :%s\r\n" % (net_settings["nick"],
                                                   net_settings["host"],
                                                   net_settings["nick"],
                                                   )
            net_settings["hello"] = set_nick + set_user

            print "Host: " + net_settings["host"]
            print "PORT: " + net_settings["port"]
            client = gevent_client.Client(net_settings["host"],
                                          net_settings["port"])

            # layer1 <-> log <-> protocol <-> behaviour
            protocol = Layer(irc.IRCProtocol())
            protocol.settings(net_settings)
            layer1 = Layer(gevent_client.Layer1(client))
            response = Layer(simple_response.SimpleResponse())
            log = Layer(reporter_handler.ReporterHander(), layer1, protocol)

            response.setLower(protocol)
            protocol.setLower(log)
            protocol.setUpper(response)
            layer1.setUpper(log)

            client.setLayer1(layer1)
            group.spawn(client.connect)

class CLI(object):

    def __init__(self):
        self.config = ConfigObj("settings/freenode.set", _inspec=True)

    def cmdloop(self):
        q = queue.Queue()
        _m = MonitorSpawner(q)
        gevent.spawn(_m.work)
        while True:
            line = raw_input("")
            print line
            args = line.split(' ')
            if args[0] == 'monitor':
                arg = args[1].strip()
                try:
                    net_settings = self.config[arg]
                except KeyError:
                    print "Error: Unknown section " + arg
                    continue
                if len(net_settings) > 0:
                    q.put(net_settings)

if __name__ == "__main__":
    cli = CLI()
    g = gevent.spawn(cli.cmdloop)
    g.join()
