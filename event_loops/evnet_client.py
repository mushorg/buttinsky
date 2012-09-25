# Code: https://github.com/rep/evnet
# Doc: https://github.com/rep/evnet

# Example from here: https://github.com/rep/evnet/blob/master/examples/evnetcat.py

from evnet import PlainClientConnection, loop, unloop

class Client(object):

    def __init__(self, host, port):
        connection = (host, port)
        self.c = PlainClientConnection(connection)
        self.c._on('ready', self.ready)
        self.c._on('close', self.closed)
        self.c._on('read', self.read)

    def ready(self):
        print 'ready'

    def read(self, d):
        print repr(d)

    def closed(self):
        unloop()


if __name__ == '__main__':
    c = Client('chat.freenode.net', 6665)
    loop()
