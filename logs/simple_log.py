#!/usr/bin/env python
# Copyright (C) 2012 Buttinsky Developers.
# See 'COPYING' for copying permission.

from stack import LayerPlugin

from modules import logging_handler


class SimpleLog(LayerPlugin):

    def receive(self, msg):
        self.log(msg.data)
        return msg

    def transmit(self, msg):
        if len(msg.data) > 0:
            self.log(msg.data)
        return msg

    def log(self, msg):
        loggers = logging_handler.get_loggers()
        print loggers
        for logger in loggers:
            print "found logger"
            logger.insert(msg)
