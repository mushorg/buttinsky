# Code: https://github.com/SiteSupport/gevent
# Doc (out-dated?): http://www.gevent.org/contents.html

# Example from here: https://gist.github.com/1506694

import gevent

from gevent import socket, queue


class Tcp(object):
    '''Handles TCP connections, `timeout` is in secs.'''
    
    def __init__(self, host, port, timeout=300):
        self._ibuffer = ''
        self._obuffer = ''
        self.iqueue = queue.Queue()
        self.oqueue = queue.Queue()
        self.host = host
        self.port = port
        self.timeout = timeout
        self._socket = self._create_socket()
    
    def _create_socket(self):
        return socket.socket()
    
    def connect(self):
        self._socket.connect((self.host, self.port))
        try:
            jobs = [gevent.spawn(self._recv_loop), gevent.spawn(self._send_loop)]
            gevent.joinall(jobs)
        finally:
            gevent.killall(jobs)
    
    def disconnect(self):
        self._socket.close()
    
    def _recv_loop(self):
        while True:
            data = self._socket.recv(4096)
            self._ibuffer += data
            while '\r\n' in self._ibuffer:
                line, self._ibuffer = self._ibuffer.split('\r\n', 1)
                self.iqueue.put(line)
    
    def _send_loop(self):
        while True:
            line = self.oqueue.get().splitlines()[0][:500]
            self._obuffer += line.encode('utf-8', 'replace') + '\r\n'
            while self._obuffer:
                sent = self._socket.send(self._obuffer)
                self._obuffer = self._obuffer[sent:]


class SslTcp(Tcp):
    '''SSL wrapper for TCP connections.'''

    def _create_socket(self):
        return wrap_socket(Tcp._create_socket(self), server_side=False)


class IrcNullMessage(Exception):
    pass


class Irc(object):
    '''Provides a basic interface to an IRC server.'''
    
    def __init__(self, settings):
        self.server = settings['server']
        self.nick = settings['nick']
        self.realname = settings['realname']
        self.port = settings['port']
        self.ssl = settings['ssl']
        self.channels = settings['channels']
        self.line = {'prefix': '', 'command': '', 'args': ['', '']}
        self.lines = queue.Queue() # responses from the server
        self.logger = logger
        
        self._connect() 
        self._event_loop()
    
    def _create_connection(self):
        transport = SslTcp if self.ssl else Tcp
        return transport(self.server, self.port)
    
    def _connect(self):
        self.conn = self._create_connection()
        gevent.spawn(self.conn.connect)
        self._set_nick(self.nick)
        self.cmd('USER', (self.nick, ' 3 ', '* ', self.realname))
    
    def _disconnect(self):
        self.conn.disconnect()
    
    def _parsemsg(self, s):
        '''
        Breaks a message from an IRC server into its prefix, command, 
        and arguments.
        '''
        
        prefix = ''
        trailing = []
        if not s:
            raise IrcNullMessage('Received an empty line from the server.')
        if s[0] == ':':
            prefix, s = s[1:].split(' ', 1)
        if s.find(' :') != -1:
            s, trailing = s.split(' :', 1)
            args = s.split()
            args.append(trailing)
        else:
            args = s.split()
        command = args.pop(0)
        return prefix, command, args
    
    def _event_loop(self):
        '''
        The main event loop.
        
        Data from the server is parsed here using `parsemsg`. Parsed events
        are put in the object's event queue, `self.events`.
        '''
        
        while True:
            line = self.conn.iqueue.get()
            logger.info(line)
            prefix, command, args = self._parsemsg(line)
            self.line = {'prefix': prefix, 'command': command, 'args': args}
            self.lines.put(self.line)
            if command == '433': # nick in use
                self.nick = self.nick + '_'
                self._set_nick(self.nick)
            if command == 'PING':
                self.cmd('PONG', args)
            if command == '001':
                self._join_chans(self.channels)
    
    def _set_nick(self, nick):
        self.cmd('NICK', nick)
    
    def _join_chans(self, channels):
        return [self.cmd('JOIN', channel) for channel in channels]
    
    def reply(self, prefix, msg):
        self.msg(prefix.split('!')[0], msg)
    
    def msg(self, target, msg):
        self.cmd('PRIVMSG', (target + ' :' + msg))
    
    def cmd(self, command, args, prefix=None):
        
        if prefix:
            self._send(prefix + command + ' ' + ''.join(args))
        else:
            self._send(command + ' ' + ''.join(args))
            
    def _send(self, s):
        logger.info(s)
        self.conn.oqueue.put(s)


if __name__ == '__main__':
    
    SETTINGS = {
        'server': 'irc.voxinfinitus.net', 
        'nick': 'Kaa', 
        'realname': 'Kaa the Python', 
        'port': 6697, 
        'ssl': True, 
        'channels': ['#voxinfinitus', '#radioreddit', '#techsupport'], 
        }
    
    bot = lambda : Irc(SETTINGS)
    jobs = [gevent.spawn(bot)]
    gevent.joinall(jobs)