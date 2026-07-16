"""引擎规则回归测试：走子生成（perft）、将军、记谱、AI 合法性。"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from chinese_chess.engine.board import Board
from chinese_chess.engine.ai import AI
from chinese_chess.engine.pieces import RED, BLACK, other
from chinese_chess.game.notation import move_to_chinese
from chinese_chess.game.puzzles import clean_puzzles


def perft(board, color, depth):
    if depth == 0:
        return 1
    total = 0
    for m in board.legal_moves(color):
        cap = board.do_move(m)
        total += perft(board, other(color), depth - 1)
        board.undo_move(m, cap)
    return total


def test_perft_matches_known_values():
    b = Board()
    # 中国象棋初始局面公认的 perft 值
    assert perft(b, RED, 1) == 44
    assert perft(b, RED, 2) == 1920
    assert perft(b, RED, 3) == 79666


def test_initial_notation():
    b = Board()
    assert move_to_chinese(b, (7, 1, 7, 4)) == "炮八平五"
    assert move_to_chinese(b, (9, 1, 7, 2)) == "马八进七"
    assert move_to_chinese(b, (9, 7, 7, 6)) == "马二进三"


def test_flying_general_is_illegal():
    """两将不能照面：制造一个会导致白脸将的走子，应被判为非法。"""
    b = Board(setup=False)
    from chinese_chess.engine.pieces import Piece, KING, ROOK
    b.grid[0][4] = Piece(BLACK, KING)
    b.grid[9][4] = Piece(RED, KING)
    b.grid[5][4] = Piece(RED, ROOK)   # 挡在中间
    b.turn = RED
    # 车横向移开会让两将照面 -> 该步非法，不应出现在合法走子中
    illegal = (5, 4, 5, 3)
    assert illegal not in b.legal_moves(RED)


def test_puzzles_are_legal():
    for p in clean_puzzles():
        b = p.build_board()
        assert b.find_king(RED) is not None
        assert b.find_king(BLACK) is not None
        assert not b.kings_face()
        assert len(b.legal_moves(RED)) > 0


def test_ai_returns_legal_move():
    b = Board()
    ai = AI(2, random.Random(0))
    m = ai.choose(b, RED)
    assert m in b.legal_moves(RED)


def test_full_ai_game_terminates():
    b = Board()
    ais = {RED: AI(1, random.Random(1)), BLACK: AI(2, random.Random(2))}
    color = RED
    for _ in range(400):
        if b.game_over() is not None:
            break
        m = ais[color].choose(b, color)
        assert m in b.legal_moves(color)
        b.do_move(m)
        color = other(color)
