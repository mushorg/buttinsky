#!/usr/bin/env python
# Copyright (C) 2012 Buttinsky Developers.
# See 'COPYING' for copying permission.

import asyncore

from configobj import ConfigObj

from event_loops import asyncore_client
from protocols import irc

buttinsky_config = ConfigObj("conf/buttinsky.cfg")


class Buttinsky(object):

    def __init__(self):
        pass


if __name__ == "__main__":
    net_settings = ConfigObj("settings/template.set")
    set_nick = "NICK %s\r\n" % net_settings["nick"]
    set_user = "USER %s %s bla :%s\r\n" % (net_settings["nick"],
                                           net_settings["host"],
                                           net_settings["nick"],
                                           )
    net_settings["hello"] = set_nick + set_user
    client = asyncore_client.Client(irc.IRCProtocol, net_settings)
    asyncore.loop()
