#!/usr/bin/env python
# Copyright (C) 2012 Buttinsky Developers.
# See 'COPYING' for copying permission.

import cmd
import sys
import xmlrpclib
import getopt
import socket
import json
import os

from configobj import ConfigObj
import modules.util.validate as validate


class CLI(cmd.Cmd):

    def __init__(self, connection):
        cmd.Cmd.__init__(self)
        self.prompt = '\033[1;30m>>\033[0m '
        self.conn = connection
        self.doc_header = 'Available commands (type help <topic>):'
        self.undoc_header = ''
        self.intro = "\
            ____        __  __  _            __        \n\
           / __ )__  __/ /_/ /_(_)___  _____/ /____  __\n\
          / __  / / / / __/ __/ / __ \/ ___/ //_/ / / /\n\
         / /_/ / /_/ / /_/ /_/ / / / (__  ) ,< / /_/ / \n\
        /_____/\__,_/\__/\__/_/_/ /_/____/_/|_|\__, /  \n\
                                              /____/   \n\
        \033[1;30mButtinsky Command Line Interface\n\tType 'help' for a list of commands\033[0m\n\n"

    def do_create(self, arg):
        """
        \033[1;30msyntax: create <file> <conf> -- create new configuration from JSON encoded string, store it in file\033[0m
        """
        args = arg.split(' ')
        try:
            ret = self.conn.create(args[0], json.dumps(''.join(args[1])))
            print ret
        except IndexError:
            print "Not enough parameters: create <file> <conf>"
        except xmlrpclib.Fault as err:
            print "Command failed: ",
            print err

    def do_echo(self, arg):
        """
        \033[1;30msyntax: echo <message> -- send message to echo function to test non-blocking functionality\033[0m
        """
        try:
            ret = self.conn.echo(arg)
            print ret
        except xmlrpclib.Fault as err:
            print "Command failed: ",
            print err

    def do_load(self, arg):
        """
        \033[1;30msyntax: load <id> <filename> -- load configuration from specified filename and identify it using id\033[0m
        """
        args = arg.split(' ')
        try:
            validate.validate(args[1])
            ret = self.conn.load(args[0], args[1])
            print ret
        except IndexError:
            print "Not enough parameters: load <id> <filename>"
        except IOError:
            print "Invalid settings name. Use 'status' to get a list of available setting files."
        except xmlrpclib.Fault as err:
            print "Command failed: ",
            print err

    def do_status(self, arg):
        """
        \033[1;30msyntax: status -- show all running monitors\033[0m
        """
        try:
            ret = self.conn.status()
            print "\n\033[1;30mFile\t\tMonitor ID\n====\t\t==========\n\033[0m"
            for k, v in ret.iteritems():
                if k == "":
                    for i in v:
                        print i + "\tNone"
                else:
                    print v + "\t" + k
            print ""
        except xmlrpclib.Fault as err:
            print "Command failed: ",
            print err

    def do_stop(self, arg):
        """
        \033[1;30msyntax: stop <id> -- stop execution of monitor identified by id\033[0m
        """
        try:
            ret = self.conn.stop(arg)
        except xmlrpclib.Fault as err:
            print "Command failed: ",
            print err

    def do_restart(self, arg):
        """
        \033[1;30msyntax: restart <id> -- restart execution of monitor identified by id\033[0m
        """
        try:
            ret = self.conn.restart(arg)
        except xmlrpclib.Fault as err:
            print "Command failed: ",
            print err

    def do_list(self, arg):
        """
        \033[1;30msyntax: list <file> -- list contens of file\033[0m
        """ 
        try:
            ret = self.conn.list(arg)
            print "\n\033[1;30mContents of " + arg + "\033[0m\n"
            print ret + "\n"
        except IOError:
            print "Invalid settings name. Use 'status' to get a list of available setting files."
        except xmlrpclib.Fault as err:
            print "Command failed: ",
            print err

    def do_delete(self, arg):
        """
        \033[1;30msyntax: delete <file> -- delete configuration specified in file\033[0m
        """
        try:
            ret = self.conn.delete(arg)
        except IOError:
            print "Invalid settings name. Use 'status' to get a list of available setting files."
        except xmlrpclib.Fault as err:
            print "Command failed: ",
            print err

    def do_quit(self, arg):
        """
        \033[1;30msyntax: quit -- exit the client gracefully, Shortcuts: 'q', 'CTRL-D'\033[0m
        """
        sys.exit(1)

    def help_help(self):
        print "\t\033[1;30msyntax: help <topic> -- Show help for a particular topic. List all commands if topic is not specified\033[0m"

    def default(self, arg):
        print "Unknown command: " + arg + "\n"

    def emptyline(self):
        pass

    # shortcuts
    do_q = do_quit
    do_EOF = do_quit  # quit with CTRL-D


def usage():
    print "\nusage: cli.py [-h] [-s server] [-p port]\n\n"\
          "\t-h\t\tthis help text\n"\
          "\t-s server\thostname of the server, default: localhost\n"\
          "\t-p port\t\tport number of the server, default: 8000\n"


def main():
    if not os.path.isfile("conf/buttinsky.cfg"):
        sys.exit("Modify and rename conf/buttinsky.cfg.dist to conf/buttinsky.cfg.")
    buttinsky_config = ConfigObj("conf/buttinsky.cfg")
    server = buttinsky_config["xmlrpc"]["server"]
    port = buttinsky_config["xmlrpc"]["port"]
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hs:p:")
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit()
        elif opt in ("-s"):
            server = arg
        elif opt in ("-p"):
            port = arg

    url = "http://" + server + ":" + port + "/"
    conn = xmlrpclib.ServerProxy(url)

    try:
        ret = conn.echo("echo")
    except socket.error:
        print server + ":" + port + " seems to be down :(\n"
        sys.exit(2)
    except xmlrpclib.Fault as err:
        print "Operation denied\n"
        print err
        sys.exit(2)

    CLI(conn).cmdloop()

if __name__ == "__main__":
    main()
