"""局域网联机设置：创建房间（主机/执红）或加入房间（客户端/执黑）。"""
from __future__ import annotations

import pygame

from .. import theme
from ..app import Scene
from ..widgets import Button, TextInput
from ...net.lan import NetGame, DEFAULT_PORT, local_ip


class LanScene(Scene):
    def on_enter(self) -> None:
        self.state = "choose"     # choose / host / join
        self.net = None
        self.error = ""
        self._build_choose()

    # ---------- 选择 ----------
    def _build_choose(self) -> None:
        cx = theme.WIDTH // 2
        self.widgets = [
            Button((cx - 160, 240, 320, 64), "创建房间（执红先行）",
                   self._host, font_size=24),
            Button((cx - 160, 330, 320, 64), "加入房间（执黑后行）",
                   self._join_form, font_size=24, color=theme.BLACK_PIECE),
            Button((cx - 160, 440, 320, 54), "返回菜单", self._to_menu,
                   font_size=22, color=(150, 120, 90)),
        ]
        self.ip_input = None

    def _host(self) -> None:
        self.app.sound.play("button")
        self.state = "host"
        self.net = NetGame("host")
        self.net.host(DEFAULT_PORT)
        cx = theme.WIDTH // 2
        self.widgets = [
            Button((cx - 120, 480, 240, 54), "取消", self._cancel, font_size=22,
                   color=(150, 120, 90)),
        ]

    def _join_form(self) -> None:
        self.app.sound.play("button")
        self.state = "join"
        cx = theme.WIDTH // 2
        self.ip_input = TextInput((cx - 160, 300, 320, 52), placeholder="输入主机 IP，如 192.168.1.5",
                                  max_len=15, font_size=22, numeric_dot=True)
        self.ip_input.focused = True
        self.widgets = [
            self.ip_input,
            Button((cx - 160, 380, 150, 52), "连接", self._connect, font_size=22),
            Button((cx + 10, 380, 150, 52), "返回", self._cancel, font_size=22,
                   color=(150, 120, 90)),
        ]

    def _connect(self) -> None:
        ip = (self.ip_input.text or "").strip()
        if not ip:
            self.error = "请输入主机 IP 地址"
            return
        self.app.sound.play("button")
        self.error = ""
        self.net = NetGame("client")
        self.net.join(ip, DEFAULT_PORT)

    def _cancel(self) -> None:
        if self.net:
            self.net.close()
            self.net = None
        self.error = ""
        self.on_enter()

    def _to_menu(self) -> None:
        self.app.sound.play("button")
        from .menu import MenuScene
        self.app.go(MenuScene(self.app))

    # ---------- 事件 / 更新 ----------
    def handle(self, event: pygame.event.Event) -> None:
        for w in self.widgets:
            w.handle(event)

    def update(self, dt: float) -> None:
        if self.net and self.net.status == "connected":
            from .game import GameScene
            self.app.go(GameScene(self.app, mode="lan", net=self.net))
        elif self.net and self.net.status == "error":
            self.error = f"连接失败：{self.net.error or '请检查 IP 与网络'}"
            self.net = None
            if self.state == "host":
                self._build_choose()
                self.state = "choose"

    # ---------- 绘制 ----------
    def draw(self, surf: pygame.Surface) -> None:
        surf.fill(theme.BG)
        title = theme.get_font(40, bold=True).render("局域网联机", True, theme.RED_PIECE)
        surf.blit(title, title.get_rect(centerx=theme.WIDTH // 2, y=90))
        cx = theme.WIDTH // 2
        if self.state == "choose":
            tip = "两台电脑连到同一个 Wi-Fi / 局域网，一台创建、一台加入即可对弈"
            self._center_text(surf, tip, 180, theme.get_font(20), theme.TEXT_DIM)
        elif self.state == "host":
            self._center_text(surf, "房间已创建，等待对方加入…", 210,
                              theme.get_font(26, bold=True), theme.TEXT)
            ip = local_ip()
            self._center_text(surf, f"本机 IP：{ip}", 280,
                              theme.get_font(30, bold=True), theme.GOLD)
            self._center_text(surf, f"端口：{DEFAULT_PORT}", 330,
                              theme.get_font(22), theme.TEXT_DIM)
            self._center_text(surf, "把上面的 IP 告诉对方，让他选择“加入房间”并输入", 390,
                              theme.get_font(18), theme.TEXT_DIM)
        elif self.state == "join":
            self._center_text(surf, "输入主机的 IP 地址后点击连接", 250,
                              theme.get_font(22), theme.TEXT)
            if self.net and self.net.status == "connecting":
                self._center_text(surf, "正在连接…", 450, theme.get_font(22), theme.GOLD)
        if self.error:
            self._center_text(surf, self.error, 540, theme.get_font(20, bold=True), theme.CHECK)
        for w in self.widgets:
            w.draw(surf)

    def _center_text(self, surf, text, y, font, color) -> None:
        t = font.render(text, True, color)
        surf.blit(t, t.get_rect(centerx=theme.WIDTH // 2, y=y))
