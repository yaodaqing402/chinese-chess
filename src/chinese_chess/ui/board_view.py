"""棋盘与棋子的绘制，以及像素坐标 <-> 棋盘坐标的换算。"""
from __future__ import annotations

from typing import List, Optional, Tuple

import pygame

from . import theme
from ..engine.board import Board, Move
from ..engine.pieces import RED, ROWS, COLS

_STAR_CANNON = [(2, 1), (2, 7), (7, 1), (7, 7)]
_STAR_PAWN = [(3, 0), (3, 2), (3, 4), (3, 6), (3, 8),
              (6, 0), (6, 2), (6, 4), (6, 6), (6, 8)]


class BoardView:
    def __init__(self, flip: bool = False):
        self.flip = flip
        self._bg: Optional[pygame.Surface] = None

    # ---------- 坐标换算 ----------
    def _disp(self, row: int, col: int) -> Tuple[int, int]:
        if self.flip:
            return ROWS - 1 - row, COLS - 1 - col
        return row, col

    def point_pos(self, row: int, col: int) -> Tuple[int, int]:
        dr, dc = self._disp(row, col)
        x = theme.MARGIN + dc * theme.CELL
        y = theme.BOARD_TOP + theme.MARGIN + dr * theme.CELL
        return x, y

    def pos_to_cell(self, mx: int, my: int) -> Optional[Tuple[int, int]]:
        for row in range(ROWS):
            for col in range(COLS):
                x, y = self.point_pos(row, col)
                if (mx - x) ** 2 + (my - y) ** 2 <= (theme.CELL * 0.46) ** 2:
                    return row, col
        return None

    # ---------- 背景（棋盘线）----------
    def _build_bg(self) -> pygame.Surface:
        surf = pygame.Surface((theme.BOARD_W, theme.HEIGHT))
        surf.fill(theme.BG)
        pad = 30
        board_rect = pygame.Rect(theme.MARGIN - pad, theme.BOARD_TOP + theme.MARGIN - pad,
                                 theme.CELL * 8 + pad * 2, theme.CELL * 9 + pad * 2)
        # 木纹渐变
        for i in range(board_rect.height):
            t = i / max(1, board_rect.height)
            col = tuple(int(theme.BOARD_BG[k] * (1 - t) + theme.BOARD_BG2[k] * t) for k in range(3))
            pygame.draw.line(surf, col, (board_rect.x, board_rect.y + i),
                             (board_rect.right, board_rect.y + i))
        pygame.draw.rect(surf, theme.LINE, board_rect, width=3, border_radius=6)

        def P(r, c):
            return self.point_pos(r, c)

        # 横线
        for r in range(ROWS):
            pygame.draw.line(surf, theme.LINE, P(r, 0), P(r, 8), 2)
        # 竖线（河界处上下断开，两侧列贯通）
        for c in range(COLS):
            if c == 0 or c == 8:
                pygame.draw.line(surf, theme.LINE, P(0, c), P(9, c), 2)
            else:
                pygame.draw.line(surf, theme.LINE, P(0, c), P(4, c), 2)
                pygame.draw.line(surf, theme.LINE, P(5, c), P(9, c), 2)
        # 九宫斜线
        for (r1, c1, r2, c2) in [(0, 3, 2, 5), (0, 5, 2, 3), (7, 3, 9, 5), (7, 5, 9, 3)]:
            pygame.draw.line(surf, theme.LINE, P(r1, c1), P(r2, c2), 2)
        # 炮/兵位星点装饰
        for (r, c) in _STAR_CANNON + _STAR_PAWN:
            self._draw_star(surf, r, c)
        # 楚河汉界
        f = theme.get_font(30, bold=True)
        for text, cx in (("楚 河", 2), ("漢 界", 6)):
            t = f.render(text, True, theme.RIVER_TEXT)
            x, y = P(4 if not self.flip else 5, cx)
            mid_y = (P(4, cx)[1] + P(5, cx)[1]) // 2
            surf.blit(t, t.get_rect(center=(P(4, cx)[0] + theme.CELL // 2, mid_y)))
        return surf

    def _draw_star(self, surf: pygame.Surface, r: int, c: int) -> None:
        x, y = self.point_pos(r, c)
        d, g = 8, 4
        for sx in (-1, 1):
            for sy in (-1, 1):
                if c == 0 and sx == -1:
                    continue
                if c == 8 and sx == 1:
                    continue
                px, py = x + sx * g, y + sy * g
                pygame.draw.line(surf, theme.LINE, (px, py), (px + sx * d, py), 2)
                pygame.draw.line(surf, theme.LINE, (px, py), (px, py + sy * d), 2)

    # ---------- 绘制 ----------
    def draw(self, surf: pygame.Surface, board: Board,
             selected: Optional[Tuple[int, int]] = None,
             moves: Optional[List[Move]] = None,
             last_move: Optional[Move] = None,
             check_color: Optional[str] = None,
             anim: Optional[dict] = None) -> None:
        if self._bg is None:
            self._bg = self._build_bg()
        surf.blit(self._bg, (0, 0))

        # 上一步高亮
        if last_move:
            for (r, c) in [(last_move[0], last_move[1]), (last_move[2], last_move[3])]:
                self._ring(surf, r, c, theme.LAST_MOVE)

        radius = int(theme.CELL * 0.42)
        anim_from = anim_to = None
        if anim:
            anim_from = (anim["move"][0], anim["move"][1])
            anim_to = (anim["move"][2], anim["move"][3])

        # 棋子
        for r in range(ROWS):
            for c in range(COLS):
                p = board.grid[r][c]
                if p is None:
                    continue
                if anim and (r, c) == anim_to:
                    continue  # 动画中：终点棋子由动画层绘制
                x, y = self.point_pos(r, c)
                self._piece(surf, x, y, radius, p,
                            highlight=(check_color == p.color and _is_king(p)))

        # 选中框 + 可走点
        if selected:
            self._select_box(surf, selected[0], selected[1])
        if moves:
            for m in moves:
                self._move_hint(surf, m[2], m[3], board.grid[m[2]][m[3]] is not None)

        # 动画中的滑动棋子
        if anim:
            fx, fy = self.point_pos(*anim_from)
            tx, ty = self.point_pos(*anim_to)
            t = anim["t"]
            x = int(fx + (tx - fx) * t)
            y = int(fy + (ty - fy) * t)
            self._piece(surf, x, y, radius, anim["piece"])

    def _piece(self, surf, x, y, radius, piece, highlight=False):
        # 阴影：直接在主表面上画一个偏暗的实心圆（不用带 alpha 通道的临时表面，
        # 否则在部分显卡/Retina 后端上整块透明矩形会被渲染成黑框）
        pygame.draw.circle(surf, theme.PIECE_SHADOW, (x + 2, y + 4), radius)
        # 圆盘
        pygame.draw.circle(surf, theme.PIECE_FACE, (x, y), radius)
        pygame.draw.circle(surf, theme.PIECE_FACE_EDGE, (x, y), radius, 2)
        ring = theme.RED_PIECE if piece.is_red else theme.BLACK_PIECE
        pygame.draw.circle(surf, ring, (x, y), radius - 5, 3)
        if highlight:
            pygame.draw.circle(surf, theme.CHECK, (x, y), radius + 3, 3)
        # 文字
        font = theme.get_font(int(radius * 1.35), bold=True)
        color = theme.RED_PIECE if piece.is_red else theme.BLACK_PIECE
        t = font.render(piece.char, True, color)
        surf.blit(t, t.get_rect(center=(x, y)))

    def _ring(self, surf, r, c, color):
        x, y = self.point_pos(r, c)
        s = int(theme.CELL * 0.46)
        rect = pygame.Rect(x - s, y - s, s * 2, s * 2)
        pygame.draw.rect(surf, color, rect, width=3, border_radius=6)

    def _select_box(self, surf, r, c):
        x, y = self.point_pos(r, c)
        s = int(theme.CELL * 0.46)
        L = 14
        for sx in (-1, 1):
            for sy in (-1, 1):
                cx, cy = x + sx * s, y + sy * s
                pygame.draw.line(surf, theme.SELECT, (cx, cy), (cx - sx * L, cy), 4)
                pygame.draw.line(surf, theme.SELECT, (cx, cy), (cx, cy - sy * L), 4)

    def _move_hint(self, surf, r, c, is_capture):
        x, y = self.point_pos(r, c)
        if is_capture:
            pygame.draw.circle(surf, theme.MOVE_DOT, (x, y), int(theme.CELL * 0.44), 4)
        else:
            # 直接画实心圆点，避免带 alpha 的临时表面在某些后端上变黑块
            pygame.draw.circle(surf, theme.MOVE_DOT, (x, y), 9)
            pygame.draw.circle(surf, theme.PIECE_FACE, (x, y), 4)


def _is_king(piece) -> bool:
    from ..engine.pieces import KING
    return piece.kind == KING
