#!/usr/bin/env python
# Copyright (C) 2012 Buttinsky Developers.
# See 'COPYING' for copying permission.


class IRCProtocol(object):

    def __init__(self, net_settings):
        self.settings = {
                  "host": net_settings["host"],
                  "port": net_settings.as_int("port"),
                  "channel": net_settings["channel"],
                  "nick": net_settings["nick"],
                  }

    def parse_msg(self, data):
        left = ""
        if not data or "\r\n" not in data:
            return "", []
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
        return left, messages

    def handle_message(self, msg):
        if "command" in msg:
            if msg["command"] == "001":
                return "JOIN %s\r\n" % self.settings["channel"]
            if msg["command"] == "PING":
                return "PONG %s\r\n" % msg["args"][0]
        return ""
