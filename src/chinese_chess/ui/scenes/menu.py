"""主菜单：显示玩家段位成长，进入各种对局模式。"""
from __future__ import annotations

import pygame

from .. import theme
from ..app import Scene
from ..widgets import Button, TextInput
from ...engine.ai import DIFFICULTIES
from ...engine.pieces import RED, BLACK
from ...game import rank


class MenuScene(Scene):
    def on_enter(self) -> None:
        self.overlay = None          # None / 'pve' / 'puzzle' / 'name'
        self.buttons = []
        self.overlay_widgets = []
        self._build_main()

    # ---------- 主菜单按钮 ----------
    def _build_main(self) -> None:
        self.buttons = []
        bx = theme.WIDTH - 340
        bw, bh, gap = 280, 62, 20
        top = 150
        items = [
            ("人机对战", lambda: self._open("pve")),
            ("双人对战", lambda: self._start_pvp()),
            ("教学残局", lambda: self._open("puzzle")),
            ("局域网联机", lambda: self._open_lan()),
            ("棋谱记录", lambda: self._open_records()),
        ]
        for i, (label, cb) in enumerate(items):
            self.buttons.append(Button((bx, top + i * (bh + gap), bw, bh), label,
                                       cb, font_size=26))
        # 底部小按钮
        by = theme.HEIGHT - 90
        self.buttons.append(Button((bx, by, 132, 50), self._sound_label(),
                                   self._toggle_sound, font_size=20, color=(150, 120, 90)))
        self.buttons.append(Button((bx + 148, by, 132, 50), "改名字",
                                   lambda: self._open("name"), font_size=20, color=(150, 120, 90)))

    def _sound_label(self) -> str:
        return "音效：开" if self.app.settings.get("sound", True) else "音效：关"

    # ---------- 动作 ----------
    def _toggle_sound(self) -> None:
        on = not self.app.settings.get("sound", True)
        self.app.settings["sound"] = on
        self.app.sound.set_enabled(on)
        self.app.save()
        self.app.sound.play("button")
        self._build_main()

    def _open(self, name: str) -> None:
        self.app.sound.play("button")
        self.overlay = name
        self.overlay_widgets = []
        if name == "pve":
            self._build_pve_overlay()
        elif name == "puzzle":
            self._build_puzzle_overlay()
        elif name == "name":
            self._build_name_overlay()

    def _close_overlay(self) -> None:
        self.overlay = None
        self.overlay_widgets = []

    def _start_pvp(self) -> None:
        self.app.sound.play("button")
        from .game import GameScene
        self.app.go(GameScene(self.app, mode="pvp"))

    def _open_lan(self) -> None:
        self.app.sound.play("button")
        from .lan import LanScene
        self.app.go(LanScene(self.app))

    def _open_records(self) -> None:
        self.app.sound.play("button")
        from .records import RecordsScene
        self.app.go(RecordsScene(self.app))

    # ---------- 人机难度选择 ----------
    def _build_pve_overlay(self) -> None:
        self._pve_color = RED
        ox, oy, ow, oh = theme.WIDTH // 2 - 250, 120, 500, 480
        self._overlay_rect = pygame.Rect(ox, oy, ow, oh)
        w = self.overlay_widgets
        for i, (name, *_rest) in enumerate(DIFFICULTIES):
            y = oy + 90 + i * 58
            w.append(Button((ox + 60, y, ow - 120, 48), f"{name}（第{i+1}级）",
                            lambda i=i: self._start_pve(i), font_size=23))
        w.append(Button((ox + 60, oy + oh - 130, 180, 46), "执红先行",
                        lambda: self._set_pve_color(RED), font_size=20, color=theme.RED_PIECE))
        w.append(Button((ox + ow - 240, oy + oh - 130, 180, 46), "执黑后行",
                        lambda: self._set_pve_color(BLACK), font_size=20, color=theme.BLACK_PIECE))
        w.append(Button((ox + ow // 2 - 70, oy + oh - 66, 140, 44), "返回",
                        self._close_overlay, font_size=20, color=(150, 120, 90)))

    def _set_pve_color(self, color: str) -> None:
        self._pve_color = color
        self.app.sound.play("button")

    def _start_pve(self, difficulty: int) -> None:
        self.app.sound.play("button")
        self.app.settings["difficulty"] = difficulty
        self.app.save()
        from .game import GameScene
        self.app.go(GameScene(self.app, mode="pve", difficulty=difficulty,
                              human_color=self._pve_color))

    # ---------- 残局选择 ----------
    def _build_puzzle_overlay(self) -> None:
        from ...game.puzzles import clean_puzzles
        self._puzzles = clean_puzzles()
        ox, oy, ow = theme.WIDTH // 2 - 260, 120, 520
        oh = 140 + len(self._puzzles) * 60
        self._overlay_rect = pygame.Rect(ox, oy, ow, oh)
        for i, p in enumerate(self._puzzles):
            y = oy + 84 + i * 60
            self.overlay_widgets.append(
                Button((ox + 40, y, ow - 80, 50), p.name,
                       lambda i=i: self._start_puzzle(i), font_size=22))
        self.overlay_widgets.append(
            Button((ox + ow // 2 - 70, oy + oh - 62, 140, 44), "返回",
                   self._close_overlay, font_size=20, color=(150, 120, 90)))

    def _start_puzzle(self, idx: int) -> None:
        self.app.sound.play("button")
        from .game import GameScene
        self.app.go(GameScene(self.app, mode="puzzle", puzzle_index=idx))

    # ---------- 改名字 ----------
    def _build_name_overlay(self) -> None:
        ox, oy, ow, oh = theme.WIDTH // 2 - 220, 220, 440, 240
        self._overlay_rect = pygame.Rect(ox, oy, ow, oh)
        self._name_input = TextInput((ox + 60, oy + 100, ow - 120, 48),
                                     text=self.app.settings.get("player_name", "小棋手"),
                                     placeholder="输入你的名字", max_len=8, font_size=24)
        self._name_input.focused = True
        self.overlay_widgets = [
            self._name_input,
            Button((ox + 60, oy + oh - 66, 130, 46), "保存", self._save_name, font_size=22),
            Button((ox + ow - 190, oy + oh - 66, 130, 46), "取消",
                   self._close_overlay, font_size=22, color=(150, 120, 90)),
        ]

    def _save_name(self) -> None:
        name = self._name_input.text.strip() or "小棋手"
        self.app.settings["player_name"] = name
        self.app.save()
        self.app.sound.play("button")
        self._close_overlay()

    # ---------- 事件 ----------
    def handle(self, event: pygame.event.Event) -> None:
        if self.overlay:
            for w in self.overlay_widgets:
                w.handle(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._close_overlay()
            return
        for b in self.buttons:
            b.handle(event)

    # ---------- 绘制 ----------
    def draw(self, surf: pygame.Surface) -> None:
        surf.fill(theme.BG)
        self._draw_decor(surf)
        self._draw_title(surf)
        self._draw_rank_card(surf)
        for b in self.buttons:
            b.draw(surf)
        if self.overlay:
            self._draw_overlay(surf)

    def _draw_decor(self, surf: pygame.Surface) -> None:
        # 左侧一枚大棋子装饰（置于段位卡下方，避免遮挡）
        cx, cy, r = 250, theme.HEIGHT - 160, 112
        pygame.draw.circle(surf, theme.PIECE_FACE, (cx, cy), r)
        pygame.draw.circle(surf, theme.RED_PIECE, (cx, cy), r - 10, 6)
        f = theme.get_font(130, bold=True)
        t = f.render("帥", True, theme.RED_PIECE)
        surf.blit(t, t.get_rect(center=(cx, cy)))

    def _draw_title(self, surf: pygame.Surface) -> None:
        f = theme.get_font(64, bold=True)
        shadow = f.render("中国象棋", True, (120, 80, 40))
        surf.blit(shadow, (63, 53))
        t = f.render("中国象棋", True, theme.RED_PIECE)
        surf.blit(t, (60, 50))
        sub = theme.get_font(26).render("少儿版 · 快乐学棋，步步高升", True, theme.TEXT_DIM)
        surf.blit(sub, (64, 126))

    def _draw_rank_card(self, surf: pygame.Surface) -> None:
        s = self.app.settings
        score = s.get("rank_score", 0)
        idx, name = rank.rank_of(score)
        nxt_name, need = rank.next_rank(score)
        card = pygame.Rect(60, 200, 400, 180)
        pygame.draw.rect(surf, theme.PANEL_BG, card, border_radius=16)
        pygame.draw.rect(surf, theme.GOLD, card, width=3, border_radius=16)
        # 玩家名 + 段位
        pn = theme.get_font(28, bold=True).render(s.get("player_name", "小棋手"), True, theme.TEXT)
        surf.blit(pn, (card.x + 24, card.y + 20))
        rk = theme.get_font(30, bold=True).render(f"★ {name}", True, theme.GOLD)
        surf.blit(rk, (card.x + 24, card.y + 60))
        # 进度条
        bar = pygame.Rect(card.x + 24, card.y + 108, card.width - 48, 18)
        pygame.draw.rect(surf, (225, 214, 194), bar, border_radius=9)
        p = rank.progress(score)
        fill = pygame.Rect(bar.x, bar.y, int(bar.width * p), bar.height)
        pygame.draw.rect(surf, theme.GOLD, fill, border_radius=9)
        if nxt_name:
            tip = f"积分 {score}　距【{nxt_name}】还差 {need} 分"
        else:
            tip = f"积分 {score}　已达最高段位！"
        surf.blit(theme.get_font(18).render(tip, True, theme.TEXT_DIM), (card.x + 24, card.y + 132))
        rec = f"胜 {s.get('wins', 0)}　负 {s.get('losses', 0)}"
        surf.blit(theme.get_font(18).render(rec, True, theme.TEXT_DIM), (card.x + 24, card.y + 154))

    def _draw_overlay(self, surf: pygame.Surface) -> None:
        theme.draw_veil(surf, 130)
        r = self._overlay_rect
        pygame.draw.rect(surf, theme.PANEL_BG, r, border_radius=18)
        pygame.draw.rect(surf, theme.GOLD, r, width=3, border_radius=18)
        titles = {"pve": "选择难度", "puzzle": "选择残局关卡", "name": "修改名字"}
        t = theme.get_font(30, bold=True).render(titles.get(self.overlay, ""), True, theme.TEXT)
        surf.blit(t, t.get_rect(center=(r.centerx, r.y + 40)))
        if self.overlay == "pve":
            hint = f"当前选择：{'执红先行' if self._pve_color == RED else '执黑后行'}"
            h = theme.get_font(20).render(hint, True, theme.RED_PIECE if self._pve_color == RED else theme.BLACK_PIECE)
            surf.blit(h, h.get_rect(center=(r.centerx, r.bottom - 150)))
        elif self.overlay == "puzzle" and self._puzzles:
            pass
        for w in self.overlay_widgets:
            w.draw(surf)
