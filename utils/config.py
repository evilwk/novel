# -*- coding: utf-8 -*-

import configparser
import os

_config_file = "config.ini"
_config = configparser.ConfigParser()


def get_network_proxy():
    return _config["network"].get("proxy", "").strip()


def get_network_timeout():
    return _config["network"].getint("timeout", 10)


def init():
    if os.path.exists(_config_file):
        _config.read(_config_file)
    else:
        # socks5h:// or http://
        _config["network"] = {
            "proxy": "",
            "timeout": 10,
        }
        with open(_config_file, "w+") as file:
            _config.write(file)


init()
