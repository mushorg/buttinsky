#!/usr/bin/env python
# Copyright (C) 2012 Buttinsky Developers.
# See 'COPYING' for copying permission.

from stack import LayerPlugin

from modules import logging_handler


class SimpleLog(LayerPlugin):

    def receive(self, msg):
        print "Log recvd:\n" + msg.data
        return msg

    def transmit(self, msg):
        if len(msg.data) > 0:
            loggers = logging_handler.get_loggers()
            for logger in loggers:
                logger.insert(msg.data)
        return msg
