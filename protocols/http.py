#!/usr/bin/env python
# Copyright (C) 2012 Buttinsky Developers.
# See 'COPYING' for copying permission.

from stack import LayerPlugin, Message
from mimetools import Message as mtmsg
from StringIO import StringIO as strio


class HTTPProtocol(LayerPlugin):

    def settings(self, settings):
        pr_settings = settings["protocol"]
        self._default_method = pr_settings.get("default_method", "GET")
        self._default_uri = pr_settings.get("default_URI", "/")
        self._default_version = pr_settings.get("default_version", "HTTP/1.1")
        self._default_headers = pr_settings.get("default_headers", {})

    def transmit(self, msg):
        method = msg.data.get("method", self._default_method)
        uri = msg.data.get("URI", self._default_uri)
        version = msg.data.get("version", self._default_version)
        request = "{} {} {}\r\n".format(method, uri, version)

        headers = dict(self._default_headers.items() +
                       msg.data.get("headers", {}).items())
        for name, value in headers.items():
            request += "{}: {}\r\n".format(name, value)

        body = msg.data.get("body", "")
        request += "\r\n{}".format(body)

        return Message(request, msg.left)

    def receive(self, msg):
        response = msg.data
        try:
            status, response = response.split("\r\n", 1)
            version, code, reason = status.split(" ", 2)
            response, body = response.split("\r\n\r\n", 1)
            headers = mtmsg(strio(response))
        except:
            return None
        else:
            return Message({
                "version": version,
                "code": code,
                "reason": reason,
                "headers": headers,
                "body": body,
            })
