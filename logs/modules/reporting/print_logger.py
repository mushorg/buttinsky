#!/usr/bin/env python
# Copyright (C) 2012 Buttinsky Developers.
# See 'COPYING' for copying permission.

import logging

from base_logger import BaseLogger


class PrintLogger(BaseLogger):

    def __init__(self, create_tables=True):

        self.logger = logging.getLogger('PrintLogger')
        self.logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = \
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        self.options = {'enabled': 'True'}

    def insert(self, msg):
        self.logger.info(msg)
