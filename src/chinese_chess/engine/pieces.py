"""中国象棋棋子定义与棋盘常量。

棋盘坐标：10 行 x 9 列，row 0 在最上方（黑方底线），row 9 在最下方（红方底线）。
红方在下、向上走（row 递减）；黑方在上、向下走（row 递增）。楚河汉界位于 row 4 与 row 5 之间。
"""
from __future__ import annotations

# 阵营
RED = "r"
BLACK = "b"

# 棋子种类
KING = "K"      # 将 / 帅
ADVISOR = "A"   # 士 / 仕
ELEPHANT = "E"  # 象 / 相
HORSE = "H"     # 马
ROOK = "R"      # 车
CANNON = "C"    # 炮
PAWN = "P"      # 卒 / 兵

# 棋盘尺寸
ROWS = 10
COLS = 9

# 显示用汉字
RED_CHARS = {KING: "帅", ADVISOR: "仕", ELEPHANT: "相", HORSE: "马",
             ROOK: "车", CANNON: "炮", PAWN: "兵"}
BLACK_CHARS = {KING: "将", ADVISOR: "士", ELEPHANT: "象", HORSE: "马",
               ROOK: "车", CANNON: "炮", PAWN: "卒"}

# 记谱用（红方数字用汉字，黑方用阿拉伯数字，符合传统习惯）
RED_NUMS = ["一", "二", "三", "四", "五", "六", "七", "八", "九"]


def other(color: str) -> str:
    return BLACK if color == RED else RED


def in_board(row: int, col: int) -> bool:
    return 0 <= row < ROWS and 0 <= col < COLS


def in_palace(color: str, row: int, col: int) -> bool:
    if col < 3 or col > 5:
        return False
    if color == RED:
        return 7 <= row <= 9
    return 0 <= row <= 2


def crossed_river(color: str, row: int) -> bool:
    """该棋子（颜色为 color）是否已过河。"""
    if color == RED:
        return row <= 4
    return row >= 5


class Piece:
    __slots__ = ("color", "kind")

    def __init__(self, color: str, kind: str):
        self.color = color
        self.kind = kind

    @property
    def char(self) -> str:
        return (RED_CHARS if self.color == RED else BLACK_CHARS)[self.kind]

    @property
    def is_red(self) -> bool:
        return self.color == RED

    def copy(self) -> "Piece":
        return Piece(self.color, self.kind)

    def __repr__(self) -> str:
        return f"Piece({self.color}{self.kind})"
