#!/usr/bin/env python
# Copyright (C) 2012 Buttinsky Developers.
# See 'COPYING' for copying permission.

from stack import LayerPlugin, Message


class AddressCheck(LayerPlugin):

    def settings(self, setting):
        pass

    def receive(self, msgs):
        # TODO parse webpage content
        pass

    def transmit(self, msg):
        return msg
