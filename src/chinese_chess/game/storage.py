"""用户数据目录与设置读写（跨平台）。"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

APP_NAME = "ChineseChess"


def data_dir() -> Path:
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    d = base / APP_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def records_dir() -> Path:
    d = data_dir() / "records"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _settings_path() -> Path:
    return data_dir() / "settings.json"


DEFAULT_SETTINGS: Dict[str, Any] = {
    "player_name": "小棋手",
    "sound": True,
    "difficulty": 1,
    "rank_score": 0,
    "wins": 0,
    "losses": 0,
}


def load_settings() -> Dict[str, Any]:
    path = _settings_path()
    data = dict(DEFAULT_SETTINGS)
    if path.exists():
        try:
            data.update(json.loads(path.read_text(encoding="utf-8")))
        except (ValueError, OSError):
            pass
    return data


def save_settings(settings: Dict[str, Any]) -> None:
    try:
        _settings_path().write_text(
            json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass
