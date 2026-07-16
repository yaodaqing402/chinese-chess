"""界面主题：配色、尺寸、字体加载。"""
from __future__ import annotations

import pygame

# ---------- 窗口 / 布局 ----------
WIDTH = 980
HEIGHT = 720
FPS = 60

MARGIN = 46          # 棋盘外框到第一条线的间距
CELL = 64            # 相邻两条线的间距
BOARD_W = MARGIN * 2 + CELL * 8   # 604
BOARD_H = MARGIN * 2 + CELL * 9   # 668
BOARD_TOP = (HEIGHT - BOARD_H) // 2
PANEL_X = BOARD_W                 # 右侧信息面板起点

# ---------- 配色 ----------
BG = (238, 224, 200)             # 整体背景（米黄）
BOARD_BG = (232, 197, 138)       # 棋盘木色
BOARD_BG2 = (222, 184, 122)      # 棋盘木色（深）
LINE = (90, 60, 30)              # 棋盘线条
RIVER_TEXT = (120, 90, 55)
PANEL_BG = (248, 241, 228)
PANEL_LINE = (210, 195, 168)

RED_PIECE = (196, 48, 43)
RED_PIECE_DARK = (150, 30, 28)
BLACK_PIECE = (40, 44, 52)
BLACK_PIECE_DARK = (20, 22, 28)
PIECE_FACE = (245, 233, 205)     # 棋子圆盘底色
PIECE_FACE_EDGE = (208, 180, 130)

SELECT = (60, 160, 90)           # 选中框
MOVE_DOT = (60, 150, 90)         # 可走点
LAST_MOVE = (230, 170, 40)       # 上一步高亮
CHECK = (220, 60, 50)            # 被将军高亮

TEXT = (60, 45, 30)
TEXT_DIM = (130, 115, 95)
TEXT_LIGHT = (250, 245, 235)

BTN = (176, 92, 60)
BTN_HOVER = (196, 112, 74)
BTN_DISABLED = (188, 176, 158)
BTN_TEXT = (252, 246, 236)
GOLD = (208, 158, 60)

_font_cache: dict = {}
# 跨平台中文字体候选（按优先级）
_CJK_CANDIDATES = [
    "PingFang SC", "STHeiti", "Heiti SC", "Hiragino Sans GB",
    "Microsoft YaHei", "微软雅黑", "SimHei", "黑体",
    "Noto Sans CJK SC", "Source Han Sans SC", "Arial Unicode MS",
    "WenQuanYi Micro Hei",
]
_cjk_font_name = None


def _resolve_cjk() -> str:
    global _cjk_font_name
    if _cjk_font_name is not None:
        return _cjk_font_name
    available = set(pygame.font.get_fonts())
    def norm(s: str) -> str:
        return s.lower().replace(" ", "")
    avail_norm = {norm(a): a for a in available}
    for cand in _CJK_CANDIDATES:
        key = norm(cand)
        if key in avail_norm:
            _cjk_font_name = pygame.font.match_font(avail_norm[key]) or cand
            return _cjk_font_name
        m = pygame.font.match_font(cand)
        if m:
            _cjk_font_name = m
            return _cjk_font_name
    # 兜底：让 pygame 自选，可能不含中文，但不至于崩溃
    _cjk_font_name = pygame.font.match_font("arial") or pygame.font.get_default_font()
    return _cjk_font_name


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    if key not in _font_cache:
        f = pygame.font.Font(_resolve_cjk(), size)
        f.set_bold(bold)
        _font_cache[key] = f
    return _font_cache[key]
