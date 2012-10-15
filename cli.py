#!/usr/bin/env python
# Copyright (C) 2012 Buttinsky Developers.
# See 'COPYING' for copying permission.

import cmd, sys, re
from configobj import ConfigObj
from event_loops import gevent_client
from protocols import irc


class CLI(cmd.Cmd):

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = ">> "
        self.intro = "\nType 'help' or '?' for a list of commands\n"
        self.config = ConfigObj("settings/template.set")

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
        client = gevent_client.Client(irc.IRCProtocol, net_settings)

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
