# Code: https://github.com/SiteSupport/gevent
# Doc (out-dated?): http://www.gevent.org/contents.html

# Example from here: https://gist.github.com/1506694

import gevent
from socket import AF_INET, SOCK_STREAM, SOCK_DGRAM
from gevent import socket, queue
from stack import LayerPlugin, Message
from socks import socksocket, PROXY_TYPE_SOCKS4, PROXY_TYPE_SOCKS5


class TCPSocket(object):
    def __init__(self, host, port):
        self._address = (str(host), int(port))
        self._socket = socket.socket(AF_INET, SOCK_STREAM)

    def connect(self):
        self._socket.connect(self._address)

    def disconnect(self):
        self._socket.close()

    def send(self, data):
        return self._socket.send(data)

    def recv(self, size):
        return self._socket.recv(size)


class TCPSocks4Socket(TCPSocket):
    def __init__(self, host, port, socks_host, socks_port):
        self._address = (str(host), int(port))
        self._socket = socksocket(AF_INET, SOCK_STREAM)
        self._socket.setproxy(PROXY_TYPE_SOCKS4,
                              str(socks_host), int(socks_port))


class TCPSocks5Socket(TCPSocket):
    def __init__(self, host, port, socks_host, socks_port):
        self._address = (str(host), int(port))
        self._socket = socksocket(AF_INET, SOCK_STREAM)
        self._socket.setproxy(PROXY_TYPE_SOCKS5,
                              str(socks_host), int(socks_port))


class UDPSocket(object):
    def __init__(self, host, port):
        self._address = (str(host), int(port))
        self._socket = socket.socket(AF_INET, SOCK_DGRAM)

    def connect(self):
        pass

    def disconnect(self):
        self._socket.close()

    def send(self, data):
        return self._socket.sendto(data, self._address)

    def recv(self, size):
        data, _addr = self._socket.recvfrom(size)
        return data


class Connection(object):
    def __init__(self, host, port):
        self._ibuffer = ''
        self._obuffer = ''
        self.iqueue = queue.Queue()
        self.oqueue = queue.Queue()
        self.host = host
        self.port = port
        self._socket = self._create_socket()
        self.jobs = None

    def _create_socket(self):
        raise NotImplementedError

    def connect(self):
        self._socket.connect()
        try:
            self.jobs = [gevent.spawn(self._recv_loop),
                         gevent.spawn(self._send_loop)]
            gevent.joinall(self.jobs)
        finally:
            gevent.killall(self.jobs)

    def disconnect(self):
        self._socket.disconnect()

    def _recv_loop(self):
        while True:
            try:
                data = self._socket.recv(4096)
                self.iqueue.put(data)
            except:
                return

    def _send_loop(self):
        while True:
            line = self.oqueue.get()
            self._obuffer += line.encode('utf-8', 'replace')
            while self._obuffer:
                sent = self._socket.send(self._obuffer)
                self._obuffer = self._obuffer[sent:]


class TCPConnection(Connection):
    def _create_socket(self):
        return TCPSocket(self.host, self.port)


class UDPConnection(Connection):
    def _create_socket(self):
        return UDPSocket(self.host, self.port)


class ProxyConnection(Connection):
    def __init__(self, host, port, proxy_host, proxy_port):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        super(ProxyConnection, self).__init__(host, port)


class TCPSocks4ProxyConnection(ProxyConnection):
    def _create_socket(self):
        return TCPSocks4Socket(
            self.host, self.port,
            self.proxy_host, self.proxy_port)


class TCPSocks5ProxyConnection(ProxyConnection):
    def _create_socket(self):
        return TCPSocks5Socket(
            self.host, self.port,
            self.proxy_host, self.proxy_port)


class Client(object):
    def __init__(self, host, port, protocol="TCP",
                 proxy_type="", proxy_host=None, proxy_port=None):
        self.lines = queue.Queue()
        self.host = host
        self.port = port
        self.protocol = protocol
        self.proxy_type = proxy_type
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.layer1 = None

    def setLayer1(self, layer1):
        self.layer1 = layer1

    def _create_connection(self):
        if self.protocol == "UDP":
            return UDPConnection(self.host, self.port)
        else:  # defaults to TCP
            if self.proxy_type == "socks4":
                return TCPSocks4ProxyConnection(
                    self.host, self.port,
                    self.proxy_host, self.proxy_port)
            elif self.proxy_type == "socks5":
                return TCPSocks5ProxyConnection(
                    self.host, self.port,
                    self.proxy_host, self.proxy_port)
            else:  # TCP without proxy
                return TCPConnection(self.host, self.port)

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
