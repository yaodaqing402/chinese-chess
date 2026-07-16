"""棋谱回放：前进/后退/自动播放，逐步重现对局。"""
from __future__ import annotations

import pygame

from .. import theme
from ..app import Scene
from ..board_view import BoardView
from ..widgets import Button
from ...engine.board import Board
from ...engine.pieces import RED, BLACK
from ...game.record import load_record


class ReplayScene(Scene):
    def __init__(self, app, path):
        super().__init__(app)
        self.path = path

    def on_enter(self) -> None:
        self.record = load_record(self.path)
        self.view = BoardView()
        self.ply = 0                       # 已走步数
        self.auto = False
        self.auto_timer = 0.0
        self._rebuild()
        self._build_buttons()
        if self.record is None:
            self.moves = []

    def _rebuild(self) -> None:
        """按 self.ply 重放棋盘。"""
        self.board = Board()
        self.moves = [tuple(m) for m in (self.record.moves if self.record else [])]
        self.last_move = None
        for i in range(self.ply):
            self.last_move = self.moves[i]
            self.board.do_move(self.moves[i])

    def _build_buttons(self) -> None:
        x = theme.PANEL_X + 24
        w = theme.WIDTH - theme.PANEL_X - 48
        half = (w - 16) // 2
        y = theme.HEIGHT - 200
        self.buttons = [
            Button((x, y, half, 46), "|< 开始", lambda: self._goto(0), font_size=20),
            Button((x + half + 16, y, half, 46), "上一步", self._prev, font_size=20),
            Button((x, y + 56, half, 46), "下一步", self._next, font_size=20),
            Button((x + half + 16, y + 56, half, 46), "末尾 >|",
                   lambda: self._goto(len(self.moves)), font_size=20),
            Button((x, y + 112, half, 46), "自动播放", self._toggle_auto, font_size=20,
                   color=theme.GOLD),
            Button((x + half + 16, y + 112, half, 46), "返回", self._back,
                   font_size=20, color=(150, 120, 90)),
        ]

    # ---------- 控制 ----------
    def _goto(self, ply: int) -> None:
        self.ply = max(0, min(ply, len(self.moves)))
        self._rebuild()
        self.app.sound.play("button")

    def _next(self) -> None:
        if self.ply < len(self.moves):
            self.last_move = self.moves[self.ply]
            cap = self.board.piece_at(self.last_move[2], self.last_move[3])
            self.board.do_move(self.moves[self.ply])
            self.ply += 1
            self.app.sound.play("capture" if cap else "move")

    def _prev(self) -> None:
        if self.ply > 0:
            self._goto(self.ply - 1)

    def _toggle_auto(self) -> None:
        self.auto = not self.auto
        self.auto_timer = 0.0
        self.buttons[4].label = "暂停" if self.auto else "自动播放"

    def _back(self) -> None:
        self.app.sound.play("button")
        from .records import RecordsScene
        self.app.go(RecordsScene(self.app))

    # ---------- 更新 ----------
    def update(self, dt: float) -> None:
        if self.auto:
            self.auto_timer += dt
            if self.auto_timer >= 0.8:
                self.auto_timer = 0.0
                if self.ply < len(self.moves):
                    self._next()
                else:
                    self._toggle_auto()

    def handle(self, event: pygame.event.Event) -> None:
        for b in self.buttons:
            b.handle(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                self._next()
            elif event.key == pygame.K_LEFT:
                self._prev()

    # ---------- 绘制 ----------
    def draw(self, surf: pygame.Surface) -> None:
        check = RED if self.board.in_check(RED) else (BLACK if self.board.in_check(BLACK) else None)
        self.view.draw(surf, self.board, last_move=self.last_move, check_color=check)
        self._draw_panel(surf)
        for b in self.buttons:
            b.draw(surf)

    def _draw_panel(self, surf) -> None:
        panel = pygame.Rect(theme.PANEL_X, 0, theme.WIDTH - theme.PANEL_X, theme.HEIGHT)
        pygame.draw.rect(surf, theme.PANEL_BG, panel)
        pygame.draw.line(surf, theme.PANEL_LINE, (theme.PANEL_X, 0), (theme.PANEL_X, theme.HEIGHT), 2)
        x = theme.PANEL_X + 24
        surf.blit(theme.get_font(28, bold=True).render("棋谱回放", True, theme.RED_PIECE), (x, 22))
        if self.record is None:
            surf.blit(theme.get_font(20).render("棋谱读取失败", True, theme.CHECK), (x, 70))
            return
        info = f"第 {self.ply} / {len(self.moves)} 步"
        surf.blit(theme.get_font(20).render(info, True, theme.TEXT_DIM), (x, 62))
        # 着法列表（高亮当前）
        font = theme.get_font(18)
        y = 100
        notations = self.record.notations
        line_h = 26
        bottom = theme.HEIGHT - 220
        rows = (bottom - y) // line_h
        cur_pair = (self.ply - 1) // 2 if self.ply > 0 else -1
        pairs = []
        for i in range(0, len(notations), 2):
            no = i // 2 + 1
            red = notations[i]
            blk = notations[i + 1] if i + 1 < len(notations) else ""
            pairs.append((no - 1, no, red, blk))
        start = max(0, cur_pair - rows + 3)
        for idx, no, red, blk in pairs[start:start + rows]:
            color = theme.RED_PIECE if idx == cur_pair else theme.TEXT
            line = f"{no:>2}. {red:<7} {blk}"
            surf.blit(font.render(line, True, color), (x, y))
            y += line_h
