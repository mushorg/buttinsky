#!/usr/bin/env python
# Copyright (C) 2012 Buttinsky Developers.
# See 'COPYING' for copying permission.

from stack import LayerPlugin


class SimpleLog(LayerPlugin):

    def receive(self, msg):
        print "Log recvd:\n" + msg.data
        return msg

    def transmit(self, msg):
        if len(msg.data) > 0:
            print "Log transmit:\n" + msg.data
        return msg
