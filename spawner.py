import gevent

from gevent.server import StreamServer
from gevent import queue

from event_loops import gevent_client
from configobj import ConfigObj

from protocols import irc
from behaviors import simple_response
from modules import reporter_handler
from stack import Layer

import gevent.pool
group = gevent.pool.Group()

global messageQueue

class MonitorSpawner(object):

    def work(self):
        try:
            g = gevent.spawn(self.listen)
            g.join()
        finally:
            g.kill()

    def listen(self):
        while True:
            net_settings = messageQueue.get()

            stackstr = net_settings['stack']
            brack1 = stackstr.split('[')[1]
            brack2 = brack1.split(']')[0]
            li = brack2.split(',')

            stack = None
            for i in li:
                plugins = self._getPlugin(i.strip(), net_settings)
                if stack == None:
                    stack = list()
                if isinstance(plugins, list):
                    for plug in plugins:
                        stack.append(plug)
                else:
                    stack.append(plugins)

            previous = None
            for i in stack[1:]:
                if previous != None:
                    previous.setUpper(i)
                i.setLower(previous)
                previous = i

            group.spawn(stack[0].connect)

    def _getPlugin(self, name, settings):

        if name == "TCP":
            client = gevent_client.Client(settings["host"],
                                          settings["port"])
            layer1 = Layer(gevent_client.Layer1(client))
            client.setLayer1(layer1)
            return [client, layer1]

        if name == "LOG":
            log = Layer(reporter_handler.ReporterHandler())
            log.settings(settings)
            return log

        if name == "DEFAULT_IRC":
            protocol = Layer(irc.IRCProtocol())
            protocol.settings(settings)
            return protocol

        if name == "SIMPLE_RESPONSE":
            response = Layer(simple_response.SimpleResponse())
            response.settings(settings)
            return response


from SimpleXMLRPCServer import SimpleXMLRPCServer
from gevent.monkey import patch_all
patch_all()


def load(identifier, config):
    arg = 'settings/' + config.strip() + '.set'
    try:
        net_settings = ConfigObj(arg, list_values=True, _inspec=True)
        messageQueue.put(net_settings)
    except KeyError:
        return -1
    return identifier

def create(identifier, config):
    return "Create command, recvd id: " + identifier

def status():
    return "Recvd status command"

def stop(identifier):
    return "Stop command, recvd id: " + identifier

def restart(identifier):
    return "Restart command, recvd id: " + identifier

def delete(identifier):
    return "Delete command, recvd id: " + identifier

def echo(msg):
    return "Msg recvd: " + msg

if __name__ == '__main__':
    messageQueue = queue.Queue()
    gevent.spawn(MonitorSpawner().work)
    server = SimpleXMLRPCServer(("localhost", 8000))
    print "Listening on port 8000..."

    server.register_function(load, "load")
    server.register_function(create, "create")
    server.register_function(status, "status")
    server.register_function(stop, "stop")
    server.register_function(restart, "restart")
    server.register_function(delete, "delete")
    server.register_function(echo, "echo")

    server.serve_forever()

