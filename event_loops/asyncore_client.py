# Doc: http://docs.python.org/library/asyncore.html

import asyncore
import socket
from cStringIO import StringIO

class Client(asyncore.dispatcher):

    def __init__(self, ip, port):
        asyncore.dispatcher.__init__(self)
        self.write_buffer = ''
        self.read_buffer = StringIO()
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        address = (ip, port)
        self.connect(address)

    def handle_connect(self):
        pass

    def handle_close(self):
        self.close()

    def writable(self):
        is_writable = (len(self.write_buffer) > 0)
        if is_writable:
            pass
        return is_writable
    
    def readable(self):
        return True

    def handle_write(self):
        sent = self.send(self.write_buffer)
        self.write_buffer = self.write_buffer[sent:]

    def handle_read(self):
        data = self.recv(8192)
        self.read_buffer.write(data)

if __name__ == '__main__':
    clients = [
        Client('', 80),
        Client('', 80),
        ]
    asyncore.loop() 