"""棋谱记录：保存、加载、列表、删除，用于回放与管理。"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from ..engine.board import Board, Move
from .notation import move_to_chinese
from .storage import records_dir


@dataclass
class GameRecord:
    mode: str = "pve"              # pve / pvp / lan / puzzle
    red_name: str = "红方"
    black_name: str = "黑方"
    result: Optional[str] = None   # 'r' / 'b' / None(未完成/和)
    difficulty: int = -1
    created: float = 0.0
    moves: List[List[int]] = field(default_factory=list)   # [[fr,fc,tr,tc], ...]
    notations: List[str] = field(default_factory=list)

    def add(self, board_before: Board, move: Move) -> None:
        self.notations.append(move_to_chinese(board_before, move))
        self.moves.append(list(move))

    @property
    def title(self) -> str:
        t = time.strftime("%Y-%m-%d %H:%M", time.localtime(self.created or time.time()))
        mode_cn = {"pve": "人机", "pvp": "双人", "lan": "联机", "puzzle": "残局"}.get(self.mode, self.mode)
        res = {"r": "红胜", "b": "黑胜"}.get(self.result or "", "未完")
        return f"{t}  [{mode_cn}]  {self.red_name} vs {self.black_name}  {res}  {len(self.moves)}回合"


def _filename(rec: GameRecord) -> str:
    ts = time.strftime("%Y%m%d_%H%M%S", time.localtime(rec.created or time.time()))
    return f"game_{ts}.json"


def save_record(rec: GameRecord) -> Path:
    if not rec.created:
        rec.created = time.time()
    path = records_dir() / _filename(rec)
    # 避免同秒重名
    i = 1
    while path.exists():
        path = records_dir() / _filename(rec).replace(".json", f"_{i}.json")
        i += 1
    path.write_text(json.dumps(asdict(rec), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_record(path: Path) -> Optional[GameRecord]:
    try:
        data: Dict = json.loads(Path(path).read_text(encoding="utf-8"))
        return GameRecord(**data)
    except (ValueError, OSError, TypeError):
        return None


def list_records() -> List[tuple]:
    """返回 [(path, GameRecord), ...]，按时间倒序。"""
    out = []
    for p in records_dir().glob("*.json"):
        rec = load_record(p)
        if rec is not None:
            out.append((p, rec))
    out.sort(key=lambda x: x[1].created, reverse=True)
    return out


def delete_record(path: Path) -> bool:
    try:
        Path(path).unlink()
        return True
    except OSError:
        return False
