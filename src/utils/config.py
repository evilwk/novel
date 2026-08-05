# -*- coding: utf-8 -*-

import configparser

from .paths import CONFIG_FILE

_config = configparser.ConfigParser()


def get_network_proxy() -> str:
    return _config["network"].get("proxy", "").strip()


def get_network_timeout() -> int:
    return _config["network"].getint("timeout", 10)


def init() -> None:
    if CONFIG_FILE.exists():
        _config.read(CONFIG_FILE)
    else:
        # socks5h:// or http://
        _config["network"] = {
            "proxy": "",
            "timeout": "10",
        }
        with open(CONFIG_FILE, "w+") as file:
            _config.write(file)


init()
