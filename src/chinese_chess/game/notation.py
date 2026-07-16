"""将走子转换为中文记谱（如“炮二平五”“马８进７”）。

红方纵线用汉字一~九，自红方的右侧向左编号；黑方纵线用阿拉伯数字，自黑方的右侧向左编号。
"""
from __future__ import annotations

from typing import Optional

from ..engine.board import Board, Move
from ..engine.pieces import (
    RED, KING, ADVISOR, ELEPHANT, HORSE, ROOK, CANNON, PAWN, RED_NUMS, other,
)

_ARABIC = ["１", "２", "３", "４", "５", "６", "７", "８", "９"]
# 走直线的子：进退用步数；走斜线的子：进退用目标纵线
_STRAIGHT = {KING, ROOK, CANNON, PAWN}


def _file_str(color: str, col: int) -> str:
    if color == RED:
        return RED_NUMS[8 - col]      # 红：col8=一 ... col0=九
    return _ARABIC[col]                # 黑：col0=１ ... col8=９


def _step_str(color: str, n: int) -> str:
    return RED_NUMS[n - 1] if color == RED else _ARABIC[n - 1]


def move_to_chinese(board: Board, move: Move) -> str:
    """在走子发生【之前】的棋盘上调用，返回该步的中文记谱。"""
    fr, fc, tr, tc = move
    p = board.grid[fr][fc]
    if p is None:
        return "?"
    color = p.color
    name = p.char

    # 同一列是否有同色同类棋子（需要前/后区分）
    prefix = ""
    same_col = [r for r in range(10)
                if board.grid[r][fc] is not None
                and board.grid[r][fc].color == color
                and board.grid[r][fc].kind == p.kind]
    if len(same_col) >= 2:
        # 红方“前”指更靠近对方（row 小）；黑方“前”指 row 大
        same_col.sort()
        is_front = (fr == same_col[0]) if color == RED else (fr == same_col[-1])
        prefix = "前" if is_front else "后"
        origin = ""  # 用前/后代替起始纵线
    else:
        origin = _file_str(color, fc)

    forward_dir = -1 if color == RED else 1  # 红进=row 减

    if tr == fr:  # 平移
        action = "平" + _file_str(color, tc)
    else:
        advancing = (tr - fr) * forward_dir > 0  # 目标更靠前（与前进方向同号）
        verb = "进" if advancing else "退"
        if p.kind in _STRAIGHT:
            action = verb + _step_str(color, abs(tr - fr))
        else:  # 斜行子：用目标纵线
            action = verb + _file_str(color, tc)

    return f"{prefix}{name}{origin}{action}"


def result_text(winner: Optional[str]) -> str:
    if winner is None:
        return "对局进行中"
    return "红方胜" if winner == RED else "黑方胜"
