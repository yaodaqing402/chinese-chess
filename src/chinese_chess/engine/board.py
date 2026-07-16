"""棋盘状态、走子生成与规则判定。"""
from __future__ import annotations

from typing import List, Optional, Tuple

from .pieces import (
    RED, BLACK, KING, ADVISOR, ELEPHANT, HORSE, ROOK, CANNON, PAWN,
    ROWS, COLS, Piece, other, in_board, in_palace, crossed_river,
)

# 一步走子：(起点行, 起点列, 终点行, 终点列)
Move = Tuple[int, int, int, int]

# 初始布局（row 0 为黑方底线）
_BACK_RANK = [ROOK, HORSE, ELEPHANT, ADVISOR, KING, ADVISOR, ELEPHANT, HORSE, ROOK]


class Board:
    def __init__(self, setup: bool = True):
        self.grid: List[List[Optional[Piece]]] = [[None] * COLS for _ in range(ROWS)]
        self.turn: str = RED  # 红先
        if setup:
            self.setup_initial()

    # ---------- 初始化与拷贝 ----------
    def setup_initial(self) -> None:
        self.grid = [[None] * COLS for _ in range(ROWS)]
        for col, kind in enumerate(_BACK_RANK):
            self.grid[0][col] = Piece(BLACK, kind)
            self.grid[9][col] = Piece(RED, kind)
        self.grid[2][1] = Piece(BLACK, CANNON)
        self.grid[2][7] = Piece(BLACK, CANNON)
        self.grid[7][1] = Piece(RED, CANNON)
        self.grid[7][7] = Piece(RED, CANNON)
        for col in (0, 2, 4, 6, 8):
            self.grid[3][col] = Piece(BLACK, PAWN)
            self.grid[6][col] = Piece(RED, PAWN)
        self.turn = RED

    def clone(self) -> "Board":
        b = Board(setup=False)
        b.turn = self.turn
        for r in range(ROWS):
            row = self.grid[r]
            for c in range(COLS):
                p = row[c]
                if p is not None:
                    b.grid[r][c] = Piece(p.color, p.kind)
        return b

    def piece_at(self, r: int, c: int) -> Optional[Piece]:
        return self.grid[r][c]

    # ---------- 查询 ----------
    def find_king(self, color: str) -> Optional[Tuple[int, int]]:
        for r in range(ROWS):
            for c in range(COLS):
                p = self.grid[r][c]
                if p is not None and p.kind == KING and p.color == color:
                    return (r, c)
        return None

    def all_pieces(self, color: str):
        for r in range(ROWS):
            for c in range(COLS):
                p = self.grid[r][c]
                if p is not None and p.color == color:
                    yield r, c, p

    # ---------- 伪合法走子生成 ----------
    def pseudo_moves(self, color: str) -> List[Move]:
        moves: List[Move] = []
        for r, c, p in self.all_pieces(color):
            gen = getattr(self, "_moves_" + p.kind)
            gen(r, c, color, moves)
        return moves

    def piece_moves(self, r: int, c: int) -> List[Move]:
        """某个格子上棋子的全部合法走子（供 UI 高亮）。"""
        p = self.grid[r][c]
        if p is None:
            return []
        pseudo: List[Move] = []
        getattr(self, "_moves_" + p.kind)(r, c, p.color, pseudo)
        return [m for m in pseudo if self._is_legal(m, p.color)]

    def _add(self, moves: List[Move], fr: int, fc: int, tr: int, tc: int, color: str) -> None:
        if not in_board(tr, tc):
            return
        target = self.grid[tr][tc]
        if target is None or target.color != color:
            moves.append((fr, fc, tr, tc))

    def _moves_K(self, r: int, c: int, color: str, moves: List[Move]) -> None:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            tr, tc = r + dr, c + dc
            if in_palace(color, tr, tc):
                self._add(moves, r, c, tr, tc, color)

    def _moves_A(self, r: int, c: int, color: str, moves: List[Move]) -> None:
        for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            tr, tc = r + dr, c + dc
            if in_palace(color, tr, tc):
                self._add(moves, r, c, tr, tc, color)

    def _moves_E(self, r: int, c: int, color: str, moves: List[Move]) -> None:
        for dr, dc in ((2, 2), (2, -2), (-2, 2), (-2, -2)):
            tr, tc = r + dr, c + dc
            if not in_board(tr, tc):
                continue
            if crossed_river(color, tr):  # 象不过河
                continue
            # 象眼被塞
            if self.grid[r + dr // 2][c + dc // 2] is not None:
                continue
            self._add(moves, r, c, tr, tc, color)

    def _moves_H(self, r: int, c: int, color: str, moves: List[Move]) -> None:
        # (脚方向, 落点)
        legs = (
            ((1, 0), (2, 1)), ((1, 0), (2, -1)),
            ((-1, 0), (-2, 1)), ((-1, 0), (-2, -1)),
            ((0, 1), (1, 2)), ((0, 1), (-1, 2)),
            ((0, -1), (1, -2)), ((0, -1), (-1, -2)),
        )
        for (lr, lc), (mr, mc) in legs:
            leg_r, leg_c = r + lr, c + lc
            if not in_board(leg_r, leg_c):
                continue
            if self.grid[leg_r][leg_c] is not None:  # 蹩马腿：马脚有子则此方向不可走
                continue
            self._add(moves, r, c, r + mr, c + mc, color)

    def _moves_R(self, r: int, c: int, color: str, moves: List[Move]) -> None:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            tr, tc = r + dr, c + dc
            while in_board(tr, tc):
                target = self.grid[tr][tc]
                if target is None:
                    moves.append((r, c, tr, tc))
                else:
                    if target.color != color:
                        moves.append((r, c, tr, tc))
                    break
                tr += dr
                tc += dc

    def _moves_C(self, r: int, c: int, color: str, moves: List[Move]) -> None:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            tr, tc = r + dr, c + dc
            jumped = False
            while in_board(tr, tc):
                target = self.grid[tr][tc]
                if not jumped:
                    if target is None:
                        moves.append((r, c, tr, tc))  # 未翻山：只能走空格
                    else:
                        jumped = True  # 遇到炮架
                else:
                    if target is not None:
                        if target.color != color:
                            moves.append((r, c, tr, tc))  # 翻山吃子
                        break
                tr += dr
                tc += dc

    def _moves_P(self, r: int, c: int, color: str, moves: List[Move]) -> None:
        forward = -1 if color == RED else 1  # 红向上（row 减）
        self._add(moves, r, c, r + forward, c, color)
        if crossed_river(color, r):  # 过河后可左右
            self._add(moves, r, c, r, c + 1, color)
            self._add(moves, r, c, r, c - 1, color)

    # ---------- 规则判定 ----------
    def kings_face(self) -> bool:
        """两将是否照面（同一列且中间无子）——白脸将。"""
        rk = self.find_king(RED)
        bk = self.find_king(BLACK)
        if rk is None or bk is None:
            return False
        if rk[1] != bk[1]:
            return False
        col = rk[1]
        lo, hi = sorted((rk[0], bk[0]))
        for r in range(lo + 1, hi):
            if self.grid[r][col] is not None:
                return False
        return True

    def is_attacked(self, r: int, c: int, by_color: str) -> bool:
        """(r,c) 是否被 by_color 方攻击（用于将军判定）。"""
        for m in self.pseudo_moves(by_color):
            if m[2] == r and m[3] == c:
                return True
        return False

    def in_check(self, color: str) -> bool:
        king = self.find_king(color)
        if king is None:
            return True
        return self.is_attacked(king[0], king[1], other(color))

    def _is_legal(self, move: Move, color: str) -> bool:
        captured = self.do_move(move)
        bad = self.in_check(color) or self.kings_face()
        self.undo_move(move, captured)
        return not bad

    def legal_moves(self, color: str) -> List[Move]:
        return [m for m in self.pseudo_moves(color) if self._is_legal(m, color)]

    # ---------- 落子 / 悔棋 ----------
    def do_move(self, move: Move) -> Optional[Piece]:
        fr, fc, tr, tc = move
        captured = self.grid[tr][tc]
        self.grid[tr][tc] = self.grid[fr][fc]
        self.grid[fr][fc] = None
        self.turn = other(self.turn)
        return captured

    def undo_move(self, move: Move, captured: Optional[Piece]) -> None:
        fr, fc, tr, tc = move
        self.grid[fr][fc] = self.grid[tr][tc]
        self.grid[tr][tc] = captured
        self.turn = other(self.turn)

    # ---------- 胜负 ----------
    def is_checkmate_or_stalemate(self, color: str) -> bool:
        """color 方无合法走子——被将死或困毙，均判负。"""
        return len(self.legal_moves(color)) == 0

    def game_over(self) -> Optional[str]:
        """返回胜方颜色；未结束返回 None。"""
        if self.find_king(RED) is None:
            return BLACK
        if self.find_king(BLACK) is None:
            return RED
        if self.is_checkmate_or_stalemate(self.turn):
            return other(self.turn)
        return None
