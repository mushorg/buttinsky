#!/usr/bin/env python

import json
import validictory

network_schema = {
    "type": "object",
    "properties": {
        "host": {
            "type": "string",
        },
        "port": {
            "type": "string",
        },
        "protocol_type": {
            "type": "string",
        },
        "reconn_attempts": {
            "type": "string",
        },
        "proxy_type": {
            "type": "string",
            "blank": True,
        },
        "proxy_host": {
            "type": "string",
            "blank": True,
        },
        "proxy_port": {
            "type": "string",
            "blank": True,
        }
    }
}

log_schema = {
    "type": "object",
    "properties": {
        "plugins": {
            "type": "string",
        }
    }
}

protocol_schema = {
    "type": "object",
    "properties": {
        "plugin": {
            "type": "string",
        }
    }
}

behavior_schema = {
    "type": "object",
    "properties": {
        "plugin": {
            "type": "string",
        }
    }
}

config_schema = {
    "type": "object",
    "properties": {
        "config": {
            "type": "object",
            "properties": {
                "network": network_schema,
                "log": log_schema,
                "protocol": protocol_schema,
                "behavior": behavior_schema,
            }
        }
    }
}

irc_protocol_schema = {
    "type": "object",
    "properties": {
        "plugin": {
            "type": "string",
        },
        "nick": {
            "type": "string",
        },
        "channel": {
            "type": "string",
        }
    }
}

irc_config_schema = {
    "type": "object",
    "properties": {
        "config": {
            "type": "object",
            "properties": {
                "network": network_schema,
                "log": log_schema,
                "protocol": irc_protocol_schema,
                "behavior": behavior_schema,
            }
        }
    }
}

http_protocol_schema = {}  # TODO
http_config_schema = {}  # TODO


def validate(filename):
    json_data = open('settings/' + filename)
    data = json.load(json_data)
    try:
        validictory.validate(data, config_schema)
    except ValueError, error:
        print error
