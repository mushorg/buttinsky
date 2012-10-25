#!/usr/bin/env python
# Copyright (C) 2012 Buttinsky Developers.
# See 'COPYING' for copying permission.

from configobj import ConfigObj
from event_loops import gevent_client
from protocols import irc
from behaviours import simple_response
from logs import simple_log

from stack import *

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

    client = gevent_client.Client(net_settings["host"], 
                                  net_settings["port"])  

    # layer1 <-> log <-> protocol <-> behaviour
    protocol = Layer(irc.IRCProtocol())
    protocol.settings(net_settings)
    layer1 = Layer(gevent_client.Layer1(client))    
    response = Layer(simple_response.SimpleResponse())
    log = Layer(simple_log.SimpleLog(), layer1, protocol)

    response.setLower(protocol)
    protocol.setLower(log)
    protocol.setUpper(response)
    layer1.setUpper(log)

    client.setLayer1(layer1)    
    client.connect()
