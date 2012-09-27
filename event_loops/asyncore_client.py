# Doc: http://docs.python.org/library/asyncore.html

import asyncore
import socket


class Client(asyncore.dispatcher):

    def __init__(self, protocol, settings):
        self.protocol = protocol()
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((settings["host"], settings["port"]))
        self.out_buffer = settings["hello"]
        self.in_buffer = ""

    def handle_connect(self):
        pass

    def handle_close(self):
        self.close()

    def handle_read(self):
        self.in_buffer += self.recv(8192)
        self.in_buffer, messages = self.protocol.parse_msg(self.in_buffer)
        for msg in messages:
            self.out_buffer += self.protocol.handle_message(msg)

    def writable(self):
        return (len(self.out_buffer) > 0)

    def handle_write(self):
        sent = self.send(self.out_buffer)
        self.out_buffer = self.out_buffer[sent:]

if __name__ == "__main__":
    client = Client(None, None)
    asyncore.loop()
