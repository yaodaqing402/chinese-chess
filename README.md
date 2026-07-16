# 中国象棋 · 少儿版 🏮

一款适合小朋友的中国象棋游戏，界面清爽、鼠标操作、带段位成长系统，陪孩子在对弈中一步步提升棋力。支持 **Windows** 与 **macOS**。

![版本](https://img.shields.io/badge/version-1.0.0-red) ![平台](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-blue)

## ✨ 功能特色

- 🎯 **人机对战**：五档难度（入门 → 初级 → 中级 → 高级 → 大师），从零基础到高手循序渐进；可选执红先行或执黑后行。
- 🏅 **段位成长系统**：赢棋积分晋级（小棋童 → 入门棋士 → … → 象棋大师），难度越高得分越多，输棋只小幅扣分，保护小朋友积极性。
- 👥 **双人对战**：同一台电脑上两人轮流下棋。
- 🌐 **局域网联机**：两台电脑连到同一 Wi-Fi / 局域网，一台创建房间、一台输入 IP 加入即可对弈。
- 📚 **教学残局**：内置经典残局闯关（双车错、马后炮、小兵立功……），每关带思路提示，练习基本杀法。
- 📖 **棋谱记录与回放**：每盘自动保存，支持逐步 / 自动回放，可管理（删除）棋谱，着法以标准中文记谱显示（如「炮二平五」「马八进七」）。
- 🔊 **落子音效**：落子、吃子、将军、胜负均有音效（可在菜单开关）。
- 🖱️ **鼠标操作**：点选棋子高亮所有可走点，再点目标即可落子，简单直观。
- 💡 **悔棋与提示**：随时悔棋、请求提示，适合小朋友边玩边学。

## 🚀 快速开始

### 方式一：下载打包好的应用（推荐）

前往 [Releases](../../releases) 下载对应系统的压缩包，解压后运行：
- **Windows**：解压后进入文件夹，双击 `ChineseChess_vX.Y.Z.exe`
- **macOS**：解压得到 `ChineseChess_vX.Y.Z.app`，右键 → 打开（首次需在「系统设置 → 隐私与安全性」允许运行）

### 方式二：源码运行

需要 Python 3.10+。

- **macOS**：双击 `启动象棋.command`（首次会自动装依赖）
- **Windows**：双击 `启动象棋.bat`

或手动：

```bash
pip install -r requirements.txt
PYTHONPATH=src python -m chinese_chess
```

## 🎮 操作说明

| 操作 | 说明 |
|------|------|
| 点击己方棋子 | 选中，并高亮所有可走位置（绿点＝可走，绿圈＝可吃子）|
| 点击目标位置 | 落子 |
| 悔棋 | 撤回上一步（人机模式撤回一整回合）|
| 提示 | 高亮一个推荐着法 |
| 回放里 ← / → | 上一步 / 下一步 |

## 🗂️ 项目结构

```
src/chinese_chess/
├── engine/        # 核心引擎：棋盘、规则、走子生成、AI（Alpha-Beta 搜索）
├── game/          # 业务层：控制器、记谱、棋谱记录、段位成长、残局
├── net/           # 局域网联机（TCP socket）
└── ui/            # 图形界面（pygame）：主题、音效、控件、棋盘绘制、各场景
tests/             # 引擎规则回归测试（perft / 记谱 / AI）
packaging/         # PyInstaller 打包脚本
.github/workflows/ # GitHub Actions：打 tag 自动构建 Win/Mac 并发布 Release
```

## 🧪 开发与测试

```bash
pip install -r requirements.txt pytest
python -m pytest tests/          # 运行引擎回归测试
```

引擎走子生成已通过公认的 perft 校验（初始局面 1/2/3 层分别为 44 / 1920 / 79666）。

## 📦 打包

```bash
pip install pyinstaller
pyinstaller packaging/chinese_chess.spec --clean -y
# 产物在 dist/ 下
```

## 📜 许可证

MIT License
