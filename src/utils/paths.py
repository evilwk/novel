# -*- coding: utf-8 -*-
"""项目内的固定路径"""

from pathlib import Path

ROOT: Path = Path(__file__).resolve().parents[2]

RULE_FILE: Path = ROOT / "novel.json"
CONFIG_FILE: Path = ROOT / "config.ini"
EPUB_DIR: Path = ROOT / "epub"
