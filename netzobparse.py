#!/usr/bin/env python
# Copyright (C) 2013 Buttinsky Developers.
# See 'COPYING' for copying permission.

"""

Parses a Netzob project exported as XML.

Handles state machine updates based on protocol model and input to handleInput.
Currently a PoC. The following protocol shows model of behaviors/models/customNetzobIRCModel.xml

On channel join:
Bot: im alive
Botherder: hail the master
Bot: hello world, my name is <settings($nick)>
Botherder: ddos <var($domain)>
Bot: ddosing <var($domain)>

"""


import binascii
from xml.dom import minidom


class NetzobModelParser(object):

    def __init__(self, path):
        self.STATES = []
        self.SYMBOLS = {}
        self.TRANSITIONS = {}
        self.state = None
        self.__parse_model(path)

    def handleInput(self, input, settings):
        msg = None
        if self.state == None:
            initialState = self.STATES[0]["id"]
            trans = self.TRANSITIONS[initialState]
            if trans["input"] == None:
                self.state = trans["endState"]
                symbol = trans["outputs"][0]
                msg = self.SYMBOLS[symbol]
                return msg
        
        trans = self.TRANSITIONS[self.state]
        inputSymbol = self.SYMBOLS[trans["input"]]
        
        if input == inputSymbol:    
            outputSymbol = self.SYMBOLS[trans["outputs"][0]]
            if "<settings($nick)>" in outputSymbol:
                msg = outputSymbol.replace("<settings($nick)>", settings["nick"].encode("ascii"))
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

    def __bin2Ascii(self, bin_text):
        return ''.join(chr(int(bin_text[i:i+8], 2)) for i in xrange(0, len(bin_text), 8))

    def __parse_model(self, path):
        xmldoc = minidom.parse(path)
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
                    type = type[0].firstChild.data
                    value = var[0].getElementsByTagName("netzob:originalValue")
                    if len(value) > 0:
                        if type == "Binary":
                            string = string + self.__bin2Ascii(value[0].firstChild.data)
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

         
