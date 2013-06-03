#!/usr/bin/env python
# Copyright (C) 2012 Buttinsky Developers.
# See 'COPYING' for copying permission.

import os
import sys

from configobj import ConfigObj

import gevent.monkey
gevent.monkey.patch_all()

from SimpleXMLRPCServer import SimpleXMLRPCServer

from modules.reporting import hpfeeds_logger

from spawner import MonitorSpawner, ButtinskyXMLRPCServer
import cli

import gevent
from gevent import queue

import logging
import logging.config

logging.config.fileConfig('conf/logging.ini')
logger = logging.getLogger(__name__)


buttinsky_config = ConfigObj("conf/buttinsky.cfg")


class Buttinsky(object):

    def __init__(self):
        logger.info("Starting Buttinsky")
        self.servers = []
        if not os.path.isfile("conf/buttinsky.cfg"):
            sys.exit("Modify and rename conf/buttinsky.cfg.dist to conf/buttinsky.cfg.")
        hpfeeds_logger.HPFeedsLogger()
        messageQueue = queue.Queue()
        gevent.spawn(MonitorSpawner(messageQueue).work)
        buttinsky_config = ConfigObj("conf/buttinsky.cfg")
        hostname = buttinsky_config["xmlrpc"]["server"]
        port = int(buttinsky_config["xmlrpc"]["port"])
        server = SimpleXMLRPCServer((hostname, port), logRequests=False)
        logger.debug("Listening on port 8000...")
        server.register_instance(ButtinskyXMLRPCServer(messageQueue))
        if buttinsky_config["hpfeeds"]["enabled"] == "True":
            gevent.spawn(ButtinskyXMLRPCServer(messageQueue).load_sink)
        try:
            xmlrpc_server = gevent.spawn(server.serve_forever)
            cli_thread = gevent.spawn(cli.main)
            cli_thread.join()
            xmlrpc_server.kill()
        except (KeyboardInterrupt, SystemExit):
            logger.debug("Quitting... Bye!")


if __name__ == "__main__":
    buttinsky = Buttinsky()