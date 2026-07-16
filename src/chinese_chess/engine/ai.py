"""电脑对手：Alpha-Beta 极大极小搜索 + 棋子位置价值表。

难度由搜索深度与随机性决定，方便小朋友从入门逐步挑战高手。
"""
from __future__ import annotations

import random
import time
from typing import List, Optional, Tuple

from .board import Board, Move
from .pieces import (
    RED, BLACK, KING, ADVISOR, ELEPHANT, HORSE, ROOK, CANNON, PAWN,
    ROWS, COLS, other,
)

# 基础子力价值
VALUES = {KING: 100000, ROOK: 900, CANNON: 450, HORSE: 400,
          ADVISOR: 200, ELEPHANT: 200, PAWN: 100}

# 位置价值表（红方视角，row 9 在下方己方底线）。黑方镜像使用。
_PAWN_PST = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [90, 90, 110, 120, 120, 120, 110, 90, 90],
    [90, 90, 110, 120, 120, 120, 110, 90, 90],
    [70, 70, 90, 100, 100, 100, 90, 70, 70],
    [50, 50, 60, 70, 70, 70, 60, 50, 50],
    [0, 0, 0, 20, 20, 20, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
]
_HORSE_PST = [
    [10, 10, 10, 12, 10, 12, 10, 10, 10],
    [10, 18, 22, 18, 12, 18, 22, 18, 10],
    [14, 22, 26, 24, 20, 24, 26, 22, 14],
    [12, 20, 24, 26, 24, 26, 24, 20, 12],
    [12, 18, 22, 24, 24, 24, 22, 18, 12],
    [12, 16, 20, 22, 22, 22, 20, 16, 12],
    [10, 16, 18, 20, 20, 20, 18, 16, 10],
    [8, 12, 16, 18, 14, 18, 16, 12, 8],
    [6, 10, 12, 12, 10, 12, 12, 10, 6],
    [4, 6, 8, 8, 6, 8, 8, 6, 4],
]
_ROOK_PST = [
    [14, 14, 12, 18, 16, 18, 12, 14, 14],
    [16, 20, 18, 24, 26, 24, 18, 20, 16],
    [12, 16, 14, 20, 22, 20, 14, 16, 12],
    [12, 18, 16, 22, 22, 22, 16, 18, 12],
    [12, 14, 12, 18, 18, 18, 12, 14, 12],
    [12, 16, 14, 20, 20, 20, 14, 16, 12],
    [6, 12, 10, 16, 16, 16, 10, 12, 6],
    [8, 10, 8, 16, 16, 16, 8, 10, 8],
    [10, 12, 10, 18, 18, 18, 10, 12, 10],
    [8, 10, 8, 16, 16, 16, 8, 10, 8],
]
_CANNON_PST = [
    [6, 4, 0, -10, -12, -10, 0, 4, 6],
    [2, 2, 0, -4, -14, -4, 0, 2, 2],
    [2, 2, 0, -10, -8, -10, 0, 2, 2],
    [0, 0, -2, 4, 10, 4, -2, 0, 0],
    [0, 0, 0, 2, 8, 2, 0, 0, 0],
    [-2, 0, 4, 2, 6, 2, 4, 0, -2],
    [0, 0, 0, 2, 4, 2, 0, 0, 0],
    [4, 0, 8, 6, 10, 6, 8, 0, 4],
    [0, 2, 4, 6, 6, 6, 4, 2, 0],
    [0, 0, 2, 6, 6, 6, 2, 0, 0],
]

_PST = {PAWN: _PAWN_PST, HORSE: _HORSE_PST, ROOK: _ROOK_PST, CANNON: _CANNON_PST}

# 难度：名称、最大搜索深度、随机挑选前 N 步、每步误差概率、思考时间上限（秒）
DIFFICULTIES = [
    ("入门", 1, 3, 0.35, 0.5),
    ("初级", 2, 2, 0.20, 0.8),
    ("中级", 3, 1, 0.08, 1.5),
    ("高级", 4, 1, 0.0, 2.2),
    ("大师", 5, 1, 0.0, 2.8),
]

MATE = 90000


def evaluate(board: Board, color: str) -> int:
    """从 color 方视角的局面分值。"""
    score = 0
    for r in range(ROWS):
        for c in range(COLS):
            p = board.grid[r][c]
            if p is None:
                continue
            v = VALUES[p.kind]
            pst = _PST.get(p.kind)
            if pst is not None:
                # 红方直接查表，黑方镜像行
                v += pst[r][c] if p.color == RED else pst[ROWS - 1 - r][c]
            score += v if p.color == color else -v
    return score


class AI:
    def __init__(self, difficulty: int = 2, rng: Optional[random.Random] = None):
        self.set_difficulty(difficulty)
        self.rng = rng or random.Random()
        self.nodes = 0

    def set_difficulty(self, level: int) -> None:
        level = max(0, min(level, len(DIFFICULTIES) - 1))
        self.level = level
        self.name, self.depth, self.topn, self.blunder, self.time_limit = DIFFICULTIES[level]

    def _gen(self, board: Board, color: str) -> List[Move]:
        """搜索用走子生成：伪合法走子 + 飞将吃子。

        搜索不逐点做“将军过滤”（太慢），而是让对手下一层直接“吃将”来体现——
        若某步把自己的将暴露，对手会在下一层吃掉它并得到被将死分，从而自然避开。
        飞将（白脸将）作为一步可吃对方将的走子加入，规则才完整。
        """
        moves = board.pseudo_moves(color)
        king = board.find_king(color)
        ek = board.find_king(other(color))
        if king and ek and king[1] == ek[1]:
            col = king[1]
            lo, hi = sorted((king[0], ek[0]))
            if all(board.grid[r][col] is None for r in range(lo + 1, hi)):
                moves.append((king[0], col, ek[0], col))
        return moves

    def _order(self, board: Board, moves: List[Move]) -> List[Move]:
        """吃子优先（MVV-LVA 近似），提升剪枝效率。"""
        def key(m: Move) -> int:
            target = board.grid[m[2]][m[3]]
            attacker = board.grid[m[0]][m[1]]
            if target is None:
                return 0
            return VALUES[target.kind] * 10 - VALUES[attacker.kind]
        return sorted(moves, key=key, reverse=True)

    def _search(self, board: Board, color: str, depth: int, alpha: int, beta: int) -> int:
        self.nodes += 1
        if depth == 0:
            return evaluate(board, color)
        moves = self._order(board, self._gen(board, color))
        best = -MATE * 2
        for m in moves:
            target = board.grid[m[2]][m[3]]
            cap = board.do_move(m)
            if target is not None and target.kind == KING:
                board.undo_move(m, cap)
                return MATE + depth  # 直接吃到对方将，立即获胜
            val = -self._search(board, other(color), depth - 1, -beta, -alpha)
            board.undo_move(m, cap)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best

    def choose(self, board: Board, color: str) -> Optional[Move]:
        """为 color 方选出一步棋（仅返回真正合法的走子）。

        采用迭代加深：从浅到深逐层搜索，超时或达到最大深度即停，
        用上一层的结果做排序以提升剪枝效率，也保证响应时间可控。
        """
        self.nodes = 0
        moves = board.legal_moves(color)  # 根节点用严格合法走子，保证落子合规
        if not moves:
            return None

        deadline = time.time() + self.time_limit
        # 初始按 MVV-LVA 排序
        scored: List[Tuple[int, Move]] = [(0, m) for m in self._order(board, moves)]

        for depth in range(1, self.depth + 1):
            ordered = [m for _s, m in sorted(scored, key=lambda x: x[0], reverse=True)]
            this: List[Tuple[int, Move]] = []
            alpha, beta = -MATE * 2, MATE * 2
            best = -MATE * 2
            aborted = False
            for m in ordered:
                cap = board.do_move(m)
                val = -self._search(board, other(color), depth - 1, -beta, -alpha)
                board.undo_move(m, cap)
                this.append((val, m))
                if val > best:
                    best = val
                    alpha = max(alpha, best)
                if depth >= 3 and time.time() > deadline:
                    aborted = True
                    break
            if not aborted:
                scored = this            # 本层完整完成，采用其结果
            if aborted or best >= MATE:   # 超时或已找到杀棋，停止加深
                break

        scored.sort(key=lambda x: x[0], reverse=True)

        # 低难度时偶尔犯错 / 从较优的前几步里随机，模拟不同水平的对手
        if self.blunder and self.rng.random() < self.blunder and len(scored) > 1:
            pool = scored[: min(len(scored), self.topn + 3)]
            return self.rng.choice(pool)[1]
        topn = max(1, self.topn)
        pool = scored[:topn]
        return self.rng.choice(pool)[1]
