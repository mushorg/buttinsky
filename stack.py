#!/usr/bin/env python
# Copyright (C) 2012 Buttinsky Developers.
# See 'COPYING' for copying permission.


class Message(object):

    def __init__(self, data="", left=""):
        self.data = data
        if not left:
            self.left = ""
        else:
            self.left = left


class Layer(object):

    def __init__(self, plugin, lower=None, upper=None):
        self.plugin = plugin
        self.upper = upper
        self.lower = lower

    def setLower(self, lower):
        self.lower = lower

    def setUpper(self, upper):
        self.upper = upper

    def transmit(self, msg):
        msg = self.plugin.transmit(msg)
        if not self.lower:
            self.lower.transmit(msg)

    def receive(self, msg):
        msg = self.plugin.receive(msg)
        if not self.upper:
            self.upper.receive(msg)
        else:
            self.transmit(msg)

    def settings(self, settings):
        self.plugin.settings(settings)


class LayerPlugin(object):

    def __init__(self):
        pass

    def transmit(self, msg):
        raise NotImplementedError

    def receive(self, msg):
        raise NotImplementedError

    def settings(self, settings):
        raise NotImplementedError
