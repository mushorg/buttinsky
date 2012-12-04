# Code: https://github.com/SiteSupport/gevent
# Doc (out-dated?): http://www.gevent.org/contents.html

# Example from here: https://gist.github.com/1506694

import gevent

from gevent import socket, queue


class TCP(object):
    def __init__(self, net_settings):
        self._ibuffer = ''
        self._obuffer = ''
        self.iqueue = queue.Queue()
        self.oqueue = queue.Queue()
        self.oqueue.put(net_settings["hello"])
        self.host = net_settings["host"]
        self.port = net_settings.as_int("port")
        self._socket = self._create_socket()

    def _create_socket(self):
        return socket.socket()

    def connect(self):
        self._socket.connect((self.host, self.port))
        try:
            jobs = [gevent.spawn(self._recv_loop),
                    gevent.spawn(self._send_loop)
                    ]
            gevent.joinall(jobs)
        finally:
            gevent.killall(jobs)

    def disconnect(self):
        self._socket.close()

    def _recv_loop(self):
        while True:
            data = self._socket.recv(4096)
            self.iqueue.put(data)

    def _send_loop(self):
        while True:
            line = self.oqueue.get()
            self._obuffer += line.encode('utf-8', 'replace')
            while self._obuffer:
                sent = self._socket.send(self._obuffer)
                self._obuffer = self._obuffer[sent:]


class Client(object):
    def __init__(self, protocol, net_settings):
        self.protocol = protocol(net_settings)
        self.lines = queue.Queue()
        self._connect(net_settings)
        self._event_loop()

    def _create_connection(self, net_settings):
        return TCP(net_settings)

    def _connect(self, net_settings):
        self.conn = self._create_connection(net_settings)
        gevent.spawn(self.conn.connect)

    def _disconnect(self):
        self.conn.disconnect()

    def _send(self, s):
        self.conn.oqueue.put(s)

    def _event_loop(self):
        while True:
            line = self.conn.iqueue.get()
            data, messages = self.protocol.parse_msg(line)
            if len(data) > 0:
                self.conn.iqueue.put(data)
            if len(messages) > 0:
                print messages
                self.lines.put(messages)
                for msg in messages:
                    self._send(self.protocol.handle_message(msg))
