"""对局场景：支持人机、双人、局域网联机、教学残局四种模式。"""
from __future__ import annotations

import threading
from typing import List, Optional, Tuple

import pygame

from .. import theme
from ..app import Scene
from ..board_view import BoardView
from ..widgets import Button
from ...engine.ai import AI, DIFFICULTIES
from ...engine.board import Move
from ...engine.pieces import RED, BLACK, other
from ...game import rank
from ...game.controller import GameController
from ...game.record import save_record

ANIM_DUR = 0.18


class GameScene(Scene):
    def __init__(self, app, mode: str = "pvp", difficulty: int = -1,
                 human_color: str = RED, puzzle_index: Optional[int] = None, net=None):
        super().__init__(app)
        self.mode = mode
        self.difficulty = difficulty
        self.human_color = human_color
        self.puzzle_index = puzzle_index
        self.net = net

    def on_enter(self) -> None:
        self._setup_controller()
        self.view = BoardView(flip=self._should_flip())
        self.selected: Optional[Tuple[int, int]] = None
        self.legal: List[Move] = []
        self.anim: Optional[dict] = None
        self._pending_gameover = False
        self.ai_thinking = False
        self._ai_result: Optional[Move] = None
        self._ai_lock = threading.Lock()
        self.hint_move: Optional[Move] = None
        self.hint_timer = 0.0
        self.message = ""
        self.end_dialog = None
        self._awarded = False
        self._saved = False
        self._build_buttons()

    # ---------- 初始化 ----------
    def _setup_controller(self) -> None:
        pn = self.app.settings.get("player_name", "小棋手")
        if self.mode == "pve":
            ai_name = DIFFICULTIES[max(0, self.difficulty)][0]
            red_name = pn if self.human_color == RED else f"电脑·{ai_name}"
            black_name = pn if self.human_color == BLACK else f"电脑·{ai_name}"
            self.ctrl = GameController("pve", red_name, black_name, self.difficulty)
            self.ai = AI(self.difficulty)
            self.ai_color = other(self.human_color)
        elif self.mode == "puzzle":
            from ...game.puzzles import clean_puzzles
            self.puzzle = clean_puzzles()[self.puzzle_index or 0]
            self.ctrl = GameController("puzzle", pn, "电脑", 3)
            self.ctrl.board = self.puzzle.build_board()
            self.ai = AI(3)
            self.human_color = RED
            self.ai_color = BLACK
        elif self.mode == "lan":
            self.human_color = self.net.color
            rn = pn if self.human_color == RED else "对手"
            bn = pn if self.human_color == BLACK else "对手"
            self.ctrl = GameController("lan", rn, bn)
            self.ai = None
            self.ai_color = None
        else:  # pvp
            self.ctrl = GameController("pvp", pn + "(红)", "挑战者(黑)")
            self.ai = None
            self.ai_color = None

    def _should_flip(self) -> bool:
        return self.mode in ("pve", "lan") and self.human_color == BLACK

    def _build_buttons(self) -> None:
        x = theme.PANEL_X + 24
        w = theme.WIDTH - theme.PANEL_X - 48
        y = theme.HEIGHT - 190
        self.buttons = []
        half = (w - 16) // 2
        if self.mode == "lan":
            self.buttons.append(Button((x, y, half, 46), "提示", self._hint, font_size=20))
            self.buttons.append(Button((x + half + 16, y, half, 46), "认输", self._resign,
                                       font_size=20, color=(170, 80, 70)))
        else:
            self.buttons.append(Button((x, y, half, 46), "悔棋", self._undo, font_size=20))
            self.buttons.append(Button((x + half + 16, y, half, 46), "提示", self._hint, font_size=20))
        y2 = y + 58
        self.buttons.append(Button((x, y2, half, 46), "重新开始", self._restart, font_size=20,
                                   color=(150, 120, 90)))
        self.buttons.append(Button((x + half + 16, y2, half, 46), "返回菜单", self._to_menu,
                                   font_size=20, color=(150, 120, 90)))

    # ---------- 按钮动作 ----------
    def _undo(self) -> None:
        if self.anim or self.ai_thinking or self.mode == "lan":
            return
        if self.mode == "puzzle":
            ok = self.ctrl.undo_turn()
        elif self.mode == "pve":
            ok = self.ctrl.undo_turn()
        else:
            ok = self.ctrl.undo_once()
        if ok:
            self.app.sound.play("button")
            self.selected = None
            self.legal = []
            self.end_dialog = None

    def _hint(self) -> None:
        if self.anim or self.ai_thinking or self.ctrl.winner:
            return
        if self.mode in ("pve", "lan") and self.ctrl.turn != self.human_color:
            return
        m = self.ctrl.hint(self.ctrl.turn)
        if m:
            self.hint_move = m
            self.hint_timer = 2.5
            self.app.sound.play("button")

    def _resign(self) -> None:
        if self.ctrl.winner:
            return
        if self.mode == "lan" and self.net:
            self.net.send_resign()
        self.ctrl.winner = other(self.human_color if self.mode != "pvp" else self.ctrl.turn)
        self.ctrl.record.result = self.ctrl.winner
        self._open_end_dialog()

    def _restart(self) -> None:
        self.app.sound.play("button")
        if self.mode == "lan":
            self._to_menu()
            return
        self.on_enter()

    def _to_menu(self) -> None:
        if self.mode == "lan" and self.net:
            self.net.close()
        self.app.sound.play("button")
        from .menu import MenuScene
        self.app.go(MenuScene(self.app))

    # ---------- 输入 ----------
    def handle(self, event: pygame.event.Event) -> None:
        if self.end_dialog:
            for b in self.end_dialog["buttons"]:
                b.handle(event)
            return
        for b in self.buttons:
            b.handle(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._on_click(event.pos)

    def _my_turn(self) -> bool:
        if self.mode == "pvp":
            return True
        return self.ctrl.turn == self.human_color

    def _on_click(self, pos) -> None:
        if self.anim or self.ai_thinking or self.ctrl.winner:
            return
        if not self._my_turn():
            return
        if pos[0] >= theme.BOARD_W:
            return
        cell = self.view.pos_to_cell(*pos)
        if cell is None:
            return
        r, c = cell
        piece = self.ctrl.board.piece_at(r, c)
        if self.selected:
            move = (self.selected[0], self.selected[1], r, c)
            if any(move == m for m in self.legal):
                self._apply_move(move, from_local=True)
                return
            if piece is not None and piece.color == self.ctrl.turn:
                self._select(r, c)
            else:
                self.selected = None
                self.legal = []
        elif piece is not None and piece.color == self.ctrl.turn:
            self._select(r, c)

    def _select(self, r: int, c: int) -> None:
        self.selected = (r, c)
        self.legal = self.ctrl.legal_from(r, c)
        self.app.sound.play("select")

    # ---------- 落子 ----------
    def _apply_move(self, move: Move, from_local: bool) -> None:
        is_capture = self.ctrl.board.piece_at(move[2], move[3]) is not None
        self.ctrl.play(move)
        moved = self.ctrl.board.piece_at(move[2], move[3])
        self.selected = None
        self.legal = []
        self.hint_move = None
        self.app.sound.play("capture" if is_capture else "move")
        self.anim = {"move": move, "piece": moved, "t": 0.0}
        self._pending_gameover = True
        if from_local and self.mode == "lan" and self.net:
            self.net.send_move(move)

    def _on_anim_done(self) -> None:
        chk = self.ctrl.in_check()
        if self.ctrl.winner:
            self.app.sound.play("win" if self._human_won() else "lose")
            self._open_end_dialog()
        elif chk:
            self.app.sound.play("check")

    def _human_won(self) -> bool:
        if self.mode == "pvp":
            return True
        return self.ctrl.winner == self.human_color

    # ---------- 更新 ----------
    def update(self, dt: float) -> None:
        if self.hint_timer > 0:
            self.hint_timer -= dt
            if self.hint_timer <= 0:
                self.hint_move = None
        # 动画推进
        if self.anim:
            self.anim["t"] += dt / ANIM_DUR
            if self.anim["t"] >= 1.0:
                self.anim = None
                if self._pending_gameover:
                    self._pending_gameover = False
                    self._on_anim_done()
            return
        if self.end_dialog:
            return
        # 网络消息
        if self.mode == "lan" and self.net:
            self._poll_net()
        # 电脑走子
        if self.mode in ("pve", "puzzle") and not self.ctrl.winner:
            if self.ctrl.turn == self.ai_color and not self.ai_thinking:
                self._start_ai()
            if self.ai_thinking:
                with self._ai_lock:
                    result = self._ai_result
                if result is not None or (result is None and not self._ai_alive()):
                    self.ai_thinking = False
                    if result:
                        self._apply_move(result, from_local=False)

    def _ai_alive(self) -> bool:
        return getattr(self, "_ai_thread", None) is not None and self._ai_thread.is_alive()

    def _start_ai(self) -> None:
        self.ai_thinking = True
        self._ai_result = None
        board_copy = self.ctrl.board.clone()
        color = self.ai_color

        def work():
            move = self.ai.choose(board_copy, color)
            with self._ai_lock:
                self._ai_result = move
        self._ai_thread = threading.Thread(target=work, daemon=True)
        self._ai_thread.start()

    def _poll_net(self) -> None:
        for msg in self.net.poll():
            t = msg.get("type")
            if t == "move" and self.ctrl.turn != self.human_color:
                move = tuple(msg["move"])
                if any(move == m for m in self.ctrl.board.legal_moves(self.ctrl.turn)):
                    self._apply_move(move, from_local=False)
            elif t == "resign":
                self.ctrl.winner = self.human_color
                self.ctrl.record.result = self.ctrl.winner
                self._open_end_dialog()
        if self.net.status in ("closed", "error") and not self.ctrl.winner and not self.end_dialog:
            self.message = "对手已断开连接"

    # ---------- 结束对话框 ----------
    def _open_end_dialog(self) -> None:
        if self.end_dialog:
            return
        if not self._saved and len(self.ctrl.record.moves) > 0:
            save_record(self.ctrl.record)
            self._saved = True
        award = None
        if self.mode == "pve" and not self._awarded:
            self._awarded = True
            won = self.ctrl.winner == self.human_color
            award = rank.award(self.app.settings, won, max(0, self.difficulty))
            self.app.save()
        elif self.mode == "puzzle" and self.ctrl.winner == RED and not self._awarded:
            self._awarded = True
            award = rank.award(self.app.settings, True, 2)
            self.app.save()
        ox, oy, ow, oh = theme.WIDTH // 2 - 220, 200, 440, 300
        rect = pygame.Rect(ox, oy, ow, oh)
        btns = [
            Button((ox + 50, oy + oh - 74, 150, 50),
                   "返回菜单" if self.mode == "lan" else "再来一局",
                   self._restart if self.mode != "lan" else self._to_menu, font_size=22),
            Button((ox + ow - 200, oy + oh - 74, 150, 50), "返回菜单",
                   self._to_menu, font_size=22, color=(150, 120, 90)),
        ]
        self.end_dialog = {"rect": rect, "buttons": btns, "award": award}

    # ---------- 绘制 ----------
    def draw(self, surf: pygame.Surface) -> None:
        check_color = self.ctrl.in_check()
        show_moves = self.legal if not self.anim else None
        self.view.draw(surf, self.ctrl.board, selected=self.selected,
                       moves=show_moves, last_move=self.ctrl.last_move,
                       check_color=check_color, anim=self.anim)
        if self.hint_move:
            self.view._ring(surf, self.hint_move[0], self.hint_move[1], theme.SELECT)
            self.view._ring(surf, self.hint_move[2], self.hint_move[3], theme.SELECT)
        self._draw_panel(surf)
        for b in self.buttons:
            b.draw(surf)
        if self.end_dialog:
            self._draw_end_dialog(surf)

    def _draw_panel(self, surf: pygame.Surface) -> None:
        panel = pygame.Rect(theme.PANEL_X, 0, theme.WIDTH - theme.PANEL_X, theme.HEIGHT)
        pygame.draw.rect(surf, theme.PANEL_BG, panel)
        pygame.draw.line(surf, theme.PANEL_LINE, (theme.PANEL_X, 0), (theme.PANEL_X, theme.HEIGHT), 2)
        x = theme.PANEL_X + 24
        # 标题
        titles = {"pve": "人机对战", "pvp": "双人对战", "lan": "局域网联机", "puzzle": "教学残局"}
        t = theme.get_font(30, bold=True).render(titles.get(self.mode, ""), True, theme.RED_PIECE)
        surf.blit(t, (x, 22))
        sub = ""
        if self.mode == "pve":
            sub = f"难度：{DIFFICULTIES[max(0, self.difficulty)][0]}"
        elif self.mode == "puzzle":
            sub = self.puzzle.name
        elif self.mode == "lan":
            sub = f"你执{'红' if self.human_color == RED else '黑'}方"
        if sub:
            surf.blit(theme.get_font(20).render(sub, True, theme.TEXT_DIM), (x, 60))
        # 轮到谁
        self._draw_turn(surf, x, 92)
        # 残局提示
        top = 140
        if self.mode == "puzzle":
            top = self._draw_wrapped(surf, self.puzzle.tip, x, 132,
                                     theme.WIDTH - theme.PANEL_X - 48, theme.get_font(18), theme.TEXT_DIM) + 8
        # 着法列表
        self._draw_moves(surf, x, top)
        if self.message:
            m = theme.get_font(20, bold=True).render(self.message, True, theme.CHECK)
            surf.blit(m, (x, theme.HEIGHT - 232))

    def _draw_turn(self, surf, x, y) -> None:
        if self.ctrl.winner:
            txt, col = "对局结束", theme.TEXT
        else:
            red_turn = self.ctrl.turn == RED
            who = "红方" if red_turn else "黑方"
            col = theme.RED_PIECE if red_turn else theme.BLACK_PIECE
            extra = ""
            if self.ai_thinking:
                extra = "（电脑思考中…）"
            elif self.mode in ("pve", "lan") and self.ctrl.turn != self.human_color:
                extra = "（等待对方）"
            txt = f"轮到 {who} 走{extra}"
        pygame.draw.circle(surf, col, (x + 10, y + 12), 9)
        surf.blit(theme.get_font(22, bold=True).render(txt, True, col), (x + 28, y))

    def _draw_wrapped(self, surf, text, x, y, maxw, font, color) -> int:
        line = ""
        for ch in text:
            if font.size(line + ch)[0] > maxw:
                surf.blit(font.render(line, True, color), (x, y))
                y += font.get_height() + 2
                line = ch
            else:
                line += ch
        if line:
            surf.blit(font.render(line, True, color), (x, y))
            y += font.get_height() + 2
        return y

    def _draw_moves(self, surf, x, y) -> None:
        font = theme.get_font(18)
        head = theme.get_font(20, bold=True).render("着法记录", True, theme.TEXT)
        surf.blit(head, (x, y))
        y += 30
        list_bottom = theme.HEIGHT - 210
        notations = self.ctrl.record.notations
        line_h = 26
        rows = (list_bottom - y) // line_h
        # 每行显示一个回合（红/黑）
        pairs = []
        for i in range(0, len(notations), 2):
            no = i // 2 + 1
            red = notations[i]
            blk = notations[i + 1] if i + 1 < len(notations) else ""
            pairs.append((no, red, blk))
        for no, red, blk in pairs[-rows:]:
            line = f"{no:>2}. {red:<7} {blk}"
            surf.blit(font.render(line, True, theme.TEXT), (x, y))
            y += line_h

    def _draw_end_dialog(self, surf) -> None:
        theme.draw_veil(surf, 140)
        r = self.end_dialog["rect"]
        pygame.draw.rect(surf, theme.PANEL_BG, r, border_radius=20)
        pygame.draw.rect(surf, theme.GOLD, r, width=4, border_radius=20)
        won = self._human_won()
        if self.mode == "pvp":
            title = ("红方" if self.ctrl.winner == RED else "黑方") + " 获胜！"
            col = theme.RED_PIECE if self.ctrl.winner == RED else theme.BLACK_PIECE
        elif won:
            title = "恭喜你赢啦！"
            col = theme.RED_PIECE
        else:
            title = "再接再厉！"
            col = theme.BLACK_PIECE
        t = theme.get_font(38, bold=True).render(title, True, col)
        surf.blit(t, t.get_rect(center=(r.centerx, r.y + 60)))
        award = self.end_dialog.get("award")
        y = r.y + 120
        if award:
            d = award["delta"]
            sign = "+" if d >= 0 else ""
            info = f"积分 {sign}{d}　当前 {award['score']} 分"
            surf.blit(theme.get_font(22).render(info, True, theme.TEXT),
                      theme.get_font(22).render(info, True, theme.TEXT).get_rect(center=(r.centerx, y)))
            y += 40
            if award["promoted"]:
                p = theme.get_font(24, bold=True).render(f"晋级：{award['rank_name']}！", True, theme.GOLD)
                surf.blit(p, p.get_rect(center=(r.centerx, y)))
        for b in self.end_dialog["buttons"]:
            b.draw(surf)
