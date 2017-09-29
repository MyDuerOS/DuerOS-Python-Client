# -*- coding: utf-8 -*-

import json
import os
import sys
import uuid

DEFAULT_CONFIG_FILE = os.path.join(os.path.expanduser('~'), '.dueros.json')


def load(configfile=None):
    if configfile is None:
        if os.path.isfile(DEFAULT_CONFIG_FILE):
            configfile = DEFAULT_CONFIG_FILE
        else:
            product_id = "EddyLiu-" + uuid.uuid4().hex
            # return {
            #     "dueros-device-id": product_id,
            #     "host_url": "dueros-h2.baidu.com",
            #     "client_id": "5GFgMRfHOhIvI0B8AZB78nt676FeWA9n",
            #     "client_secret": "eq2eCNfbtOrGwdlA4vB1N1EaiwjBMu7i"
            # }

            return {
                "dueros-device-id": product_id,
                "host_url": "dueros-h2.baidu.com",
                "client_id": "5GFgMRfHOhIvI0B8AZB78nt676FeWA9n",
                "client_secret": "eq2eCNfbtOrGwdlA4vB1N1EaiwjBMu7i"
            }

    with open(configfile, 'r') as f:
        config = json.load(f)
        require_keys = ['dueros-device-id', 'client_id', 'client_secret']
        for key in require_keys:
            if not ((key in config) and config[key]):
                raise KeyError('{} should include "{}"'.format(configfile, key))

    return config


def save(config, configfile=None):
    if configfile is None:
        configfile = DEFAULT_CONFIG_FILE

    with open(configfile, 'w') as f:
        json.dump(config, f, indent=4)
