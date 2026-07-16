"""单局对弈的控制器：走子、悔棋、提示、胜负与棋谱记录。UI 无关。"""
from __future__ import annotations

from typing import List, Optional, Tuple

from ..engine.ai import AI
from ..engine.board import Board, Move
from ..engine.pieces import RED, BLACK, other
from .record import GameRecord


class GameController:
    def __init__(self, mode: str = "pve", red_name: str = "红方", black_name: str = "黑方",
                 difficulty: int = -1):
        self.board = Board()
        self.mode = mode
        self.record = GameRecord(mode=mode, red_name=red_name, black_name=black_name,
                                 difficulty=difficulty)
        self.history: List[Tuple[Move, Optional[object]]] = []
        self.winner: Optional[str] = None
        self.last_move: Optional[Move] = None

    # ---------- 落子 ----------
    @property
    def turn(self) -> str:
        return self.board.turn

    def legal_from(self, r: int, c: int) -> List[Move]:
        p = self.board.piece_at(r, c)
        if p is None or p.color != self.board.turn or self.winner is not None:
            return []
        return self.board.piece_moves(r, c)

    def play(self, move: Move) -> None:
        self.record.add(self.board, move)
        captured = self.board.do_move(move)
        self.history.append((move, captured))
        self.last_move = move
        self._update_result()

    def _update_result(self) -> None:
        self.winner = self.board.game_over()
        if self.winner is not None:
            self.record.result = self.winner

    def undo_once(self) -> bool:
        if not self.history:
            return False
        move, captured = self.history.pop()
        self.board.undo_move(move, captured)
        self.record.moves.pop()
        self.record.notations.pop()
        self.winner = None
        self.record.result = None
        self.last_move = self.history[-1][0] if self.history else None
        return True

    def undo_turn(self) -> bool:
        """人机模式下悔一整个回合（撤回电脑与自己的各一步）。"""
        undone = self.undo_once()
        if self.mode == "pve":
            undone = self.undo_once() or undone
        return undone

    # ---------- 状态 ----------
    def in_check(self) -> Optional[str]:
        for color in (RED, BLACK):
            if self.board.in_check(color):
                return color
        return None

    def hint(self, color: Optional[str] = None) -> Optional[Move]:
        """给当前走子方一个较强的建议着法。"""
        if self.winner is not None:
            return None
        color = color or self.board.turn
        helper = AI(difficulty=3)
        return helper.choose(self.board, color)
