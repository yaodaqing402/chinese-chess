"""应用入口：窗口、主循环、场景管理、全局资源（音效/设置）。"""
from __future__ import annotations

import os
import sys
from typing import Optional

import pygame

from . import theme
from .sound import SoundManager
from ..game.storage import load_settings, save_settings


class Scene:
    """场景基类。子类实现事件处理、更新与绘制。"""
    def __init__(self, app: "App"):
        self.app = app

    def on_enter(self) -> None:
        pass

    def handle(self, event: pygame.event.Event) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self, surf: pygame.Surface) -> None:
        pass


class App:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.pre_init(44100, -16, 2, 512)
        except pygame.error:
            pass
        self.settings = load_settings()
        self.screen = pygame.display.set_mode((theme.WIDTH, theme.HEIGHT))
        pygame.display.set_caption("中国象棋 · 少儿版")
        self.clock = pygame.time.Clock()
        self.sound = SoundManager(enabled=self.settings.get("sound", True))
        self.running = True
        self.scene: Optional[Scene] = None

    def go(self, scene: Scene) -> None:
        self.scene = scene
        scene.on_enter()

    def save(self) -> None:
        save_settings(self.settings)

    def run(self) -> None:
        # 延迟导入，避免循环引用
        from .scenes.menu import MenuScene
        self.go(MenuScene(self))
        while self.running:
            dt = self.clock.tick(theme.FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif self.scene is not None:
                    self.scene.handle(event)
            if self.scene is not None:
                self.scene.update(dt)
                self.scene.draw(self.screen)
            pygame.display.flip()
        self.save()
        pygame.quit()


def _selftest() -> int:
    """无显示环境自检（供 CI）：初始化窗口、构建各场景并各绘制一帧。"""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    app = App()
    from .scenes.menu import MenuScene
    from .scenes.game import GameScene
    from .scenes.records import RecordsScene
    app.go(MenuScene(app))
    app.scene.draw(app.screen)
    for mode in ("pvp", "pve", "puzzle"):
        app.go(GameScene(app, mode=mode, difficulty=1))
        app.scene.update(0.016)
        app.scene.draw(app.screen)
    app.go(RecordsScene(app))
    app.scene.draw(app.screen)
    out = os.environ.get("CHINESE_CHESS_SELFTEST_OUT")
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write("SELFTEST PASS\n")
    print("SELFTEST PASS")
    pygame.quit()
    return 0


def main() -> int:
    if os.environ.get("CHINESE_CHESS_SELFTEST"):
        return _selftest()
    App().run()
    return 0
