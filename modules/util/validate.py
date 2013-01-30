#!/usr/bin/env python

import json
import os
import validictory

irc_schema = {  "type": "object",
                "properties":{
                "config": {
                        "type": "object",                
                        "properties": {
                            "protocol_plugin": {
			        "type": "string"
		            },
	                    "connection_protocol_type": {
			        "type": "string"
		            },
		            "log_plugins": {
			        "type": "string",
		            },
		            "nick": {
			        "type": "string",
		            },
		            "host": {
			        "type": "string",
		            },
		            "port": {
			        "type": "string",
		            },
		            "channel": {
			        "type": "string",
		            },
		            "reconn_attempts": {
			        "type": "string",
		            }
	                  }
                        }
                     }
                  }

def irc_validate(filename):
    json_data = open('settings/' + filename)
    data = json.load(json_data)
    try:
        validictory.validate(data, irc_schema)
    except ValueError, error:
        print error
