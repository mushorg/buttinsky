#!/usr/bin/env python
# Copyright (C) 2012 Buttinsky Developers.
# See 'COPYING' for copying permission.

import json

import gevent

from configobj import ConfigObj

from modules.util import hpfeeds
from base_source import BaseSource


class HPFeedsSink(BaseSource):

    def __init__(self):
        self.buttinsky_config = ConfigObj("conf/buttinsky.cfg")
        self.options = {'enabled': 'False'}
        self.hpc = hpfeeds.new(self.buttinsky_config["hpfeeds"]["host"],
                               self.buttinsky_config["hpfeeds"]["port"],
                               self.buttinsky_config["hpfeeds"]["ident"],
                               self.buttinsky_config["hpfeeds"]["secret"])

        def on_message(identifier, channel, payload):
            try:
                analysis_report = json.loads(str(payload))
                self.received(analysis_report)
            except:
                pass

        def on_error(payload):
            self.hpc.stop()

        self.hpc.subscribe(self.buttinsky_config["hpfeeds"]["source_channel"])
        gevent.spawn(self.hpc.run(on_message, on_error))
        self.hpc.close()
        return 0

    def received(self, payload):
        print payload


if __name__ == "__main__":
    HPFeedsSink()
