#!/usr/bin/env python
# Copyright (C) 2012 Buttinsky Developers.
# See 'COPYING' for copying permission.

from configobj import ConfigObj

from event_loops import gevent_client
from protocols import irc
from behaviors import simple_response
from modules import reporter_handler

from stack import Layer

buttinsky_config = ConfigObj("conf/buttinsky.cfg")


class Buttinsky(object):

    def __init__(self):
        pass


if __name__ == "__main__":
    #gevent.signal(signal.SIGQUIT, gevent.shutdown)
    net_settings = ConfigObj("settings/freenode.set", _inspec=True)
    set_nick = "NICK %s\r\n" % net_settings["nick"]
    set_user = "USER %s %s bla :%s\r\n" % (net_settings["nick"],
                                           net_settings["host"],
                                           net_settings["nick"],
                                           )
    net_settings["hello"] = set_nick + set_user

    client = gevent_client.Client(net_settings["host"],
                                  net_settings["port"])

    # layer_network <-> layer_log <-> layer_protocol <-> layer_behavior
    layer_network = Layer(gevent_client.Layer1(client))
    layer_log = Layer(reporter_handler.ReporterHandler(), layer_network)
    layer_protocol = Layer(irc.IRCProtocol(), layer_log)
    layer_behavior = Layer(simple_response.SimpleResponse(), layer_protocol)

    layer_protocol.settings(net_settings)

    layer_network.setUpper(layer_log)
    layer_log.setUpper(layer_protocol)
    layer_protocol.setUpper(layer_behavior)

    client.setLayer1(layer_network)
    client.connect()
