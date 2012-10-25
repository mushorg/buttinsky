# Code: https://github.com/SiteSupport/gevent
# Doc (out-dated?): http://www.gevent.org/contents.html

# Example from here: https://gist.github.com/1506694

import gevent

from stack import *
from gevent import socket, queue


class TCP(object):
    def __init__(self, host, port):
        self._ibuffer = ''
        self._obuffer = ''
        self.iqueue = queue.Queue()
        self.oqueue = queue.Queue()
        self.host = host
        self.port = int(port)
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
    def __init__(self, host, port):
        self.lines = queue.Queue()
        self.host = host
        self.port = port
        self.layer1 = None

    def setLayer1(self, layer1):
        self.layer1 = layer1
       
    def _create_connection(self):
        return TCP(self.host, self.port)

    def connect(self):
        self.conn = self._create_connection()
        gevent.spawn(self.conn.connect)
        self._event_loop()

    def disconnect(self):
        self.conn.disconnect()

    def queue(self, msg):
        self.conn.iqueue.put(msg)

    def send(self, s):
        self.conn.oqueue.put(s)

    def _event_loop(self):
        while True:
            line = self.conn.iqueue.get()
            if self.layer1 != None:
                self.layer1.receive(Message(line))

class Layer1(LayerPlugin):

    def __init__(self, client):
        self.client = client

    def receive(self, msg):
        return msg

    def transmit(self, msg):
        if len(msg.left) > 0:
            self.client.queue(msg.left)
        if len(msg.data) > 0:
            self.client.send(msg.data)
