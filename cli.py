#!/usr/bin/env python
# Copyright (C) 2012 Buttinsky Developers.
# See 'COPYING' for copying permission.

import cmd
import sys

from configobj import ConfigObj

from event_loops import gevent_client

from protocols import irc
from behaviours import simple_response
from logs import simple_log

from stack import Layer


class CLI(cmd.Cmd):

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = ">> "
        self.intro = "\nType 'help' or '?' for a list of commands\n"
        self.config = ConfigObj("settings/template.set", _inspec=True)

    def do_monitor(self, arg):
        """
        Spawn new monitor client with settings from file settings/template.set
        Usage: monitor section
        """
        try:
            net_settings = self.config[arg]
        except KeyError:
            print "Error: Unknown section " + arg
            return
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

    def do_exit(self, arg):
        """
        Exit gracefully
        """
        print "So long!"
        sys.exit(0)

    def do_quit(self, arg):
        """
        Exit gracefully
        """
        self.do_exit(arg)


if __name__ == "__main__":
    CLI().cmdloop()
