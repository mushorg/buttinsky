#!/usr/bin/env python
# Copyright (C) 2012 Buttinsky Developers.
# See 'COPYING' for copying permission.

from stack import LayerPlugin, Message

import binascii
from xml.dom import minidom

class CustomIRCProtocol(LayerPlugin):

    def __init__(self):
        self.state = None
        self.STATES = None
        self.SYMBOLS = None
        self.TRANSITIONS = None

    def settings(self, settings):
        self.settings = settings["protocol"]

    def receive(self, msgs):
        if self.STATES == None:
            self.parse_model()
        
        messages = []
        for m in msgs.data:
            print m
            if "command" in m:
                if m["command"] == "JOIN" and self.state == None:
                    reply_msg = self.init()
                    if reply_msg == None:
                        break
                    reply = dict()
                    reply["command"] = "PRIVMSG"
                    reply["args"]= self.settings["channel"].encode("ascii") + " :" + reply_msg
                    messages.append(reply)
                if m["command"] == "PRIVMSG" and self.state != None:
                    reply_msg = self.handleState(m["args"][1])
                    if reply_msg == None:
                        #messages.append(m)
                        break
                    reply = dict()
                    reply["command"] = "PRIVMSG"
                    reply["args"] = self.settings["channel"].encode("ascii") + " :" + reply_msg
                    messages.append(reply)
                else:
                    messages.append(m)
    
        return Message(messages, msgs.left)

    def transmit(self, msg):
        return msg

    def init(self):
        initState = self.STATES[0]["id"]
        trans = self.TRANSITIONS[initState]
        if trans["input"] == None:
            self.state = trans["endState"]
            symbol = trans["outputs"][0]
            msg = self.SYMBOLS[symbol]
            return msg

    def handleState(self, input):
        msg = None
        trans = self.TRANSITIONS[self.state]
        inputSymbol = self.SYMBOLS[trans["input"]]
        
        if input == inputSymbol:    
            outputSymbol = self.SYMBOLS[trans["outputs"][0]]
            if "<settings($nick)>" in outputSymbol:
                msg = outputSymbol.replace("<settings($nick)>", self.settings["nick"].encode("ascii"))
        else:
            outputSymbol = self.SYMBOLS[trans["outputs"][0]]
            if "<var($domain)>" in outputSymbol:
                inputCmd = inputSymbol.split("<var($domain)>")[0].strip()
                if inputCmd in input:
                    domain = input.split(inputCmd)[1].strip()
                    msg = outputSymbol.replace("<var($domain)>", domain)
        if msg != None:
            self.state = trans["endState"]
            return msg    


    def bin2Ascii(self, bin_text):
        return ''.join(chr(int(bin_text[i:i+8], 2)) for i in xrange(0, len(bin_text), 8))

    def parse_model(self):
        self.STATES = []
        self.SYMBOLS = {}
        self.TRANSITIONS = {}

        xmldoc = minidom.parse('behaviors/models/customNetzobIRCModel.xml')
        grammar = xmldoc.getElementsByTagName('netzob:grammar')
        automata = grammar[0].getElementsByTagName('netzob:automata')
        states = grammar[0].getElementsByTagName('netzob:states')
        state = grammar[0].getElementsByTagName('netzob:state')
        transitions = grammar[0].getElementsByTagName('netzob:transitions')
        transition = grammar[0].getElementsByTagName('netzob:transition')
        symbols = xmldoc.getElementsByTagName('netzob:symbols')
        symbol = symbols[0].getElementsByTagName('netzob:symbol')

        symbolID = 0
        for s in symbol:
            symbolID = s.getAttribute("id").encode("ascii")
            f = s.getElementsByTagName("netzob:field")
            fields = s.getElementsByTagName("netzob:fields")
            string = ""
            for field in fields:
                f = field.getElementsByTagName("netzob:field")
                for entry in f:
                    format = entry.getElementsByTagName("netzob:format")
                    var = entry.getElementsByTagName("netzob:variable")
                    type = var[0].getElementsByTagName("netzob:type")
                    value = var[0].getElementsByTagName("netzob:originalValue")
                    if len(value) > 0:
                        string = string + self.bin2Ascii(value[0].firstChild.data)
            self.SYMBOLS[symbolID] = string

        for node in state:
            stateID = node.getAttribute("id").encode("ascii")
            stateName = node.getAttribute("name").encode("ascii")
            self.STATES.append({"id": stateID, "name": stateName})

        for node in transition:
            start = node.getElementsByTagName("netzob:startState")
            startState = start[0].firstChild.data.encode("ascii")

            end = node.getElementsByTagName("netzob:endState")
            endState =  end[0].firstChild.data.encode("ascii")
            input = node.getElementsByTagName("netzob:input")
            stateInput = input[0].getAttribute("symbol").encode("ascii")
            if stateInput == "EmptySymbol":
                stateInput = None
            outputs = node.getElementsByTagName("netzob:outputs")
            for outs in outputs:
                out = outs.getElementsByTagName("netzob:output")
            outSymbol = list()
            for o in out:
                outSymbol.append(o.getAttribute("symbol").encode('ascii'))
            if len(outSymbol) == 0:
                outSymbol = None
            self.TRANSITIONS[startState] = {"endState": endState, "input": stateInput, "outputs": outSymbol}
         
