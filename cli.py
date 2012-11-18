#!/usr/bin/env python
# Copyright (C) 2012 Buttinsky Developers.
# See 'COPYING' for copying permission.

import cmd
import sys
import gevent 
import ast

from configobj import ConfigObj
from event_loops import gevent_client
from gevent import queue

from protocols import irc
from behaviors import simple_response
from modules import reporter_handler
from stack import Layer

import gevent.pool
group = gevent.pool.Group()

import select
from gevent.monkey import patch_all
patch_all(os=True, select=True)


def raw_input(message):
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

            stackstr = net_settings['stack']
            brack1 = stackstr.split('[')[1]
            brack2 = brack1.split(']')[0]
            li = brack2.split(',')
          
            stack = None
            for i in li:
                plugins = self._getPlugin(i.strip(), net_settings)
                if stack == None:
                    stack = list()
                if isinstance(plugins, list):
                    for plug in plugins:
                        stack.append(plug)
                else:
                    stack.append(plugins)

            previous = None
            for i in stack[1:]:
                if previous != None:
                    previous.setUpper(i)
                i.setLower(previous)
                previous = i

            group.spawn(stack[0].connect)


    def _getPlugin(self, str, settings):

        if str == "TCP":
            client = gevent_client.Client(settings["host"],
                                          settings["port"])
            layer1 = Layer(gevent_client.Layer1(client))
            client.setLayer1(layer1)
            return [client, layer1]

        if str == "LOG":
            log = Layer(reporter_handler.ReporterHandler())
            log.settings(settings)
            return log

        if str == "DEFAULT_IRC":
            protocol = Layer(irc.IRCProtocol())
            protocol.settings(settings)
            return protocol

        if str == "SIMPLE_RESPONSE":
            response = Layer(simple_response.SimpleResponse())
            response.settings(settings)
            return response


class CLI(object):

    def __init__(self):
        self.stack = None

    def cmdloop(self):
        q = queue.Queue()
        _m = MonitorSpawner(q)
        gevent.spawn(_m.work)

        while True:
            line = raw_input("")
            args = line.split(' ')

            if args[0] == 'monitor':
                arg = 'settings/' + args[1].strip() + '.set' 
                try:
                    net_settings = ConfigObj(arg, list_values=True, _inspec=True)
                except KeyError:
                    print "Error: Unknown setting " + arg
                    continue
                if len(net_settings) > 0:
                    q.put(net_settings)

            if args[0] == 'add':
                config = ConfigObj(list_values=True, _inspec=True)
                config.filename =  'settings/' + args[1] + '.set'
                setting = {}

                try:
                    setting = ast.literal_eval(' '.join(args[2:]))
                except SyntaxError:
                    print "Error in settings"
                    continue
                for key, value in setting.iteritems():
                    config[key] = value
                config.write()
                

if __name__ == "__main__":
    g = gevent.spawn(CLI().cmdloop)
    g.join()

