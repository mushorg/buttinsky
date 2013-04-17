#!/usr/bin/env python
# Copyright (C) 2013 Buttinsky Developers.
# See 'COPYING' for copying permission.

"""

- Parses a Netzob project exported as XML.
- Handles state machine updates based on protocol model and input to handleInput. 
- Botnet mimicking (symbol output) is done when a state transition occurs.

Currently a PoC. 
The following protocol shows model of 'behaviors/models/customNetzobIRCModel.xml'
and can be used for similar text based protocols such as IRC and HTTP.

On channel join:
Bot: im alive
Botherder: hail the master
Bot: hello world, my name is settings($nick)
Botherder: ddos $domain
Bot: ddosing $domain

TODO:

- Support for several variables in protocol messages
- Output symbols based on probability and add handle delay of certain response
- Save unsupported protocol messages in delimiter separated logs (for further modeling 
  of the unkown messages in Netzob).
- Support binary protocols

"""


import binascii
from xml.dom import minidom


class NetzobModelParser(object):

    def __init__(self, path):
        self.STATES = []
        self.SYMBOLS = []
        self.TRANSITIONS = {}
        self.state = None
        self.__parse_model(path)

    def __findSymbol(self, id):
        for s in self.SYMBOLS:
            if s["id"] == id:
                return s

    def __findRef(self, id):
        for s in self.SYMBOLS:
            for f in s["fields"]:
                if f["varId"] == id:
                    return s

    def handleInput(self, input, settings, init=False):
        msg = ""
        if self.state == None:
            initialState = self.STATES[0]["id"]
            trans = self.TRANSITIONS[initialState]
            if trans["input"] == None and init:
                symbol = trans["outputs"][0]
                found = self.__findSymbol(symbol)
                for i in found["fields"]:
                    msg = msg + i["value"]
                self.state = trans["endState"]
                return msg
            return ""

        trans = self.TRANSITIONS[self.state]
        found = self.__findSymbol(trans["input"])
        inputSymbol = ""
        for i in found["fields"]:
            inputSymbol = inputSymbol + i["value"]
         
        if input == inputSymbol:    
            found = self.__findSymbol(trans["outputs"][0])          
            outputSymbol = ""
            for i in found["fields"]:
                outputSymbol = outputSymbol + i["value"]
            if "settings" in outputSymbol:
                setting = outputSymbol.split("settings($")[1].split(")")[0]
                msg = outputSymbol.replace("settings($" + setting + ")", settings[setting].encode("ascii"))
        elif inputSymbol in input:
            found = self.__findSymbol(trans["input"])
            sp = input.split(inputSymbol)
            found = self.__findSymbol(trans["outputs"][0])              
            for i in found["fields"]:
                if len(i["ref"]) > 0:
                    for j in sp:
                        if len(j) > 0:
                            msg = msg + j              
                else:
                    msg = msg + i["value"]
                
        if msg != "":
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
            symbol = {}
            symbol["id"] = symbolID
            symbol["fields"] = list()

            for field in fields:
                f = field.getElementsByTagName("netzob:field")
                for entry in f:
                    format = entry.getElementsByTagName("netzob:format")
                    var = entry.getElementsByTagName("netzob:variable")
                    for v in var:
                        id = v.getAttribute("id").encode("ascii")
                    type = var[0].getElementsByTagName("netzob:type")
                    mutable = var[0].getAttribute("mutable").encode("ascii")
                    type = type[0].firstChild.data.encode("ascii")
                    ref = ""
                    try:
                        ref = var[0].getElementsByTagName("netzob:ref")
                        ref = ref[0].firstChild.data.encode("ascii")
                    except:
                        pass
                    try:
                        value = var[0].getElementsByTagName("netzob:originalValue")
                        value = value[0].firstChild.data.encode("ascii")
                    except:
                        value = ""
                    symbol["fields"].append({"varId": id, "value": value,"ref":ref, "mutable":mutable})                   
            self.SYMBOLS.append(symbol)                
         
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
