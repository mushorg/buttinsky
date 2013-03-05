#!/usr/bin/env python
# Copyright (C) 2012 Buttinsky Developers.
# See 'COPYING' for copying permission.

from stack import LayerPlugin, Message


class IRCProtocol(LayerPlugin):

    def settings(self, net_settings):
        self.settings = {
                  "host": net_settings["host"],
                  "port": int(net_settings["port"]),
                  "channel": net_settings["channel"],
                  "nick": net_settings["nick"],
                  "hello": False,
        }

    def receive(self, msg):
        left = ""
        data = msg.data
        if not data or "\r\n" not in data:
            return Message()
        if not data.endswith("\r\n"):
            data, left = data.rsplit("\r\n", 1)
        messages = []
        for msg in data.split("\r\n"):
            if msg != "":
                message = {
                           "prefix": "",
                           "command": "",
                           "args": [],
                           }
                trailing = []
                if msg[0] == ":":
                    message["prefix"], msg = msg[1:].split(" ", 1)
                if msg.find(" :") != -1:
                    msg, trailing = msg.split(" :", 1)
                    message["args"] = msg.split()
                    message["args"].append(trailing)
                else:
                    message["args"] = msg.split()
                message["command"] = message["args"].pop(0)
                messages.append(message)
        return Message(messages, left)

    def transmit(self, msg):
        transmsg = ""
        for m in msg.data:
            if "command" in m:
                if m["command"] == "001":
                    chanlist = self.settings["channel"].split(",")
                    for chan in chanlist:
                        transmsg += "JOIN %s\r\n" % chan.strip()
                if m["command"] == "PING":
                    transmsg += "PONG %s\r\n" % m["args"][0]
                if m["command"] == "PRIVMSG":
                    transmsg += "PRIVMSG %s\r\n" % m["args"]
        if not self.settings["hello"]:
            set_nick = "NICK %s\r\n" % self.settings["nick"]
            set_user = "USER %s %s bla :%s\r\n" % (self.settings["nick"],
                                                   self.settings["host"],
                                                   self.settings["nick"],
                                                  )
            transmsg = transmsg + set_nick + set_user
            self.settings["hello"] = True
        return Message(transmsg, msg.left)
