#!/usr/bin/env python
# Copyright (C) 2012 Buttinsky Developers.
# See 'COPYING' for copying permission.

import json
import xmlrpclib

import gevent
from configobj import ConfigObj
import hpfeeds
from base_source import BaseSource


class HPFeedsSink(BaseSource):

    def __init__(self):
        self.buttinsky_config = ConfigObj("conf/buttinsky.cfg")
        url = "http://" + self.buttinsky_config["xmlrpc"]["server"] + ":" + self.buttinsky_config["xmlrpc"]["port"]  + "/"
        self.xmlrpc_conn = xmlrpclib.ServerProxy(url)
        self.options = {'enabled': 'False'}
        self.hpc = hpfeeds.new(self.buttinsky_config["hpfeeds"]["host"],
                               int(self.buttinsky_config["hpfeeds"]["port"]),
                               self.buttinsky_config["hpfeeds"]["ident"],
                               self.buttinsky_config["hpfeeds"]["secret"])

        def on_message(identifier, channel, payload):
            try:
                analysis_report = json.loads(str(payload))
                try:
                    # TODO: Fix botnet id
                    config = {"config":
                                    {
                                    "nick": analysis_report["irc_nick"],
                                    "host": analysis_report["irc_addr"].split(":", 1)[0],
                                    "port": analysis_report["irc_addr"].split(":", 1)[1],
                                    "server_pwd": analysis_report["irc_server_pwd"],
                                    "channel": analysis_report["irc_channel"]
                                    }
                              }
                    ret = self.xmlrpc_conn.create("12341231", json.dumps(config))
                    print ret
                except:
                    raise
            except:
                raise

        def on_error(payload):
            self.hpc.stop()

        self.hpc.subscribe(self.buttinsky_config["hpfeeds"]["source_channel"])
        gevent.spawn(self.hpc.run(on_message, on_error))
        self.hpc.close()


if __name__ == "__main__":
    HPFeedsSink()
