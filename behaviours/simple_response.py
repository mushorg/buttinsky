#!/usr/bin/env python
# Copyright (C) 2012 Buttinsky Developers.
# See 'COPYING' for copying permission.

from stack import LayerPlugin, Message


class SimpleResponse(LayerPlugin):

    def receive(self, msgs):
        messages = []
        for m in msgs.data:
            if "command" in m:
                if m["command"] == "PRIVMSG":
                    if m["args"][1] == "hello":
                        reply = {"command": "",
                                 "args": [],
                                 }
                        reply["command"] = "PRIVMSG"
                        reply["args"] = m["prefix"].split('!~')[0] + " hey!"
                        messages.append(reply)
                else:
                    messages.append(m)
        return Message(messages, msgs.left)

    def transmit(self, msg):
        return msg
