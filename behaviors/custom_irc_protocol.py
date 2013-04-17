#!/usr/bin/env python
# Copyright (C) 2013 Buttinsky Developers.
# See 'COPYING' for copying permission.

from stack import LayerPlugin, Message
from netzobparse import NetzobModelParser


class CustomIRCProtocol(LayerPlugin):

    def settings(self, settings):
        self.settings = settings["protocol"]
        self.stateMachine = NetzobModelParser('behaviors/models/customNetzobIRCModel.xml')

    def receive(self, msgs):
        messages = []
        for m in msgs.data:
            if "command" in m:
                reply_msg = None
                if m["command"] == "JOIN":
                    reply_msg = self.stateMachine.handleInput(None, self.settings, True)
                    if len(reply_msg) == 0:
                        break
                    reply = dict()
                    reply["command"] = "PRIVMSG"
                    reply["args"]= self.settings["channel"].encode("ascii") + " :" + reply_msg
                    messages.append(reply)
                if m["command"] == "PRIVMSG":
                    reply_msg = self.stateMachine.handleInput(m["args"][1], self.settings)
                    if len(reply_msg) == 0:
                        break
                    reply = dict()
                    reply["command"] = "PRIVMSG"
                    reply["args"] = self.settings["channel"].encode("ascii") + " :" + reply_msg
                    messages.append(reply)
                else:
                    messages.append(m)
        return Message(messages, msgs.left)

    def transmit(self, msg):
        return msg

