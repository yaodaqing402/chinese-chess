"""教学残局：经典/入门残局闯关，帮助小朋友练习基本杀法。

玩家执红先行，目标是将死黑方。黑方由电脑防守。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from ..engine.board import Board
from ..engine.pieces import (
    RED, BLACK, KING, ADVISOR, ELEPHANT, HORSE, ROOK, CANNON, PAWN, Piece,
)

# 一个棋子： (颜色, 种类, 行, 列)
Placement = Tuple[str, str, int, int]


@dataclass
class Puzzle:
    name: str
    tip: str
    setup: List[Placement]

    def build_board(self) -> Board:
        b = Board(setup=False)
        for color, kind, r, c in self.setup:
            b.grid[r][c] = Piece(color, kind)
        b.turn = RED
        return b


PUZZLES: List[Puzzle] = [
    Puzzle(
        name="第1关 · 双车错",
        tip="两只车配合，一车将军、一车控住退路，一步步把对方将逼死。",
        setup=[
            (RED, KING, 9, 3), (RED, ROOK, 3, 0), (RED, ROOK, 4, 8),
            (BLACK, KING, 0, 4), (BLACK, ADVISOR, 0, 3), (BLACK, ADVISOR, 0, 5),
        ],
    ),
    Puzzle(
        name="第2关 · 车炮争锋",
        tip="炮需要“炮架”才能吃子，试试用车和炮一起做杀。",
        setup=[
            (RED, KING, 9, 4), (RED, ROOK, 2, 8), (RED, CANNON, 7, 4),
            (BLACK, KING, 0, 4), (BLACK, ADVISOR, 0, 3), (BLACK, ELEPHANT, 0, 2),
        ],
    ),
    Puzzle(
        name="第3关 · 马后炮",
        tip="经典杀法“马后炮”：先用马控住对方将门口的点，再用炮沿直线将军。",
        setup=[
            (RED, KING, 9, 4), (RED, HORSE, 2, 3), (RED, CANNON, 5, 4),
            (BLACK, KING, 0, 4), (BLACK, ADVISOR, 0, 3), (BLACK, ADVISOR, 0, 5),
        ],
    ),
    Puzzle(
        name="第4关 · 小兵立功",
        tip="过河的兵（卒）可以左右走，还能立大功哦！配合车把对方将军。",
        setup=[
            (RED, KING, 9, 4), (RED, ROOK, 5, 0), (RED, PAWN, 1, 4),
            (BLACK, KING, 0, 4), (BLACK, ADVISOR, 0, 5),
        ],
    ),
]


def clean_puzzles() -> List[Puzzle]:
    """去掉同格重复摆放导致的非法关卡（构造期自检兜底）。"""
    valid = []
    for p in PUZZLES:
        seen = set()
        ok = True
        reds_king = blacks_king = False
        for color, kind, r, c in p.setup:
            if (r, c) in seen:
                ok = False
                break
            seen.add((r, c))
            if kind == KING and color == RED:
                reds_king = True
            if kind == KING and color == BLACK:
                blacks_king = True
        if ok and reds_king and blacks_king:
            valid.append(p)
    return valid
