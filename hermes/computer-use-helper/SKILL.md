---
name: computer-use-helper
description: macOS computer-use routing guide. Use when operating macOS apps or desktop UI, especially to choose between cua-driver, AppleScript/osascript, shell commands, keyboard/mouse events, and screenshot-based assistance instead of always using one technique.
---

# macOS Computer Use Helper

这个 skill 用来限定和指导 macOS 操作：先根据操作类型选择最合适的技术，再执行。不要默认所有事情都用同一种工具。

核心原则：

- 需要读取或操作 App UI 结构时，优先使用 `cua-driver`，因为它通过 macOS Accessibility API 获取和操作 UI。
- 需要截图、视觉定位、确认屏幕状态时，优先使用 `cua-driver`，因为它集成了 Screen Recording 辅助定位。
- 打开应用、切换应用、基础窗口管理、全屏展示等系统级动作，不要用 `cua-driver` 作为首选；优先用 AppleScript/`osascript` 或系统命令。
- 鼠标点击、键盘输入、快捷键等低层交互，选择最直接、最稳定、最少副作用的技术。
- 每次执行前先判断操作类型；如果一种技术能直接表达意图，就不要绕到更脆弱的视觉点击。

## 技术选择顺序

### 1. 打开或激活应用

打开应用、启动应用、把应用带到前台，优先使用 AppleScript 或系统命令。

推荐方式：

```bash
osascript -e 'tell application "Safari" to activate'
open -a "Safari"
```

不要为了打开应用而使用 `cua-driver`。

如果用户要求打开的应用适合全屏展示，打开后应尽量将其切到全屏。全屏动作也不要优先使用 `cua-driver`，应优先使用 AppleScript/System Events 或 macOS 窗口快捷键。

常见全屏方式：

```bash
osascript -e 'tell application "Safari" to activate' \
  -e 'tell application "System Events" to keystroke "f" using {control down, command down}'
```

如果应用已经全屏，避免重复触发全屏快捷键导致退出全屏。可先通过窗口状态、屏幕布局或应用特性判断；判断不可靠时，使用更保守的窗口最大化方式。

### 2. 读取 UI 状态或操作控件

凡是牵涉 macOS Accessibility API 能表达的 UI 读取和控件操作，优先使用 `cua-driver`。

适合 `cua-driver` 的场景：

- 读取当前窗口、按钮、文本框、菜单、表格、列表等 UI 结构。
- 点击一个可访问性树中存在的按钮、菜单项、复选框、输入框。
- 判断某个窗口、弹窗、错误提示、菜单项是否存在。
- 在复杂 App 里根据元素名称、角色、层级定位控件。
- 操作原生 macOS 应用、Electron 应用、浏览器外壳、系统设置等可访问性表现较好的界面。

推荐流程：

1. 使用 `cua-driver` 获取当前应用或窗口的可访问性快照。
2. 基于元素的 role、title、description、value、index 定位目标。
3. 对目标元素执行 click、set value、press 等操作。
4. 操作后重新获取快照或截图验证结果。

不要在能通过 Accessibility 精准定位控件时，退化成裸坐标点击。

### 3. 截图、视觉定位和屏幕验证

凡是需要看屏幕、定位图像、判断元素是否可见、确认页面布局，优先使用 `cua-driver` 的截图能力。

适合截图辅助的场景：

- Accessibility 树缺少目标元素，或元素名称不可靠。
- 需要确认弹窗、菜单、画布、图片、视频、游戏界面、图形化区域。
- 需要判断窗口是否全屏、内容是否遮挡、界面是否已经刷新。
- 需要在点击前确认视觉位置，或在点击后确认变化。

如果截图只是用来验证状态，优先截图验证；如果截图用于点击，先尝试结合 Accessibility 元素定位，最后才使用坐标。

### 4. 鼠标点击

鼠标点击按稳定性选择技术：

1. 如果目标是可访问性元素，使用 `cua-driver` 点击该元素。
2. 如果目标不是 AX 元素但能通过截图可靠定位，使用 `cua-driver` 截图定位后点击。
3. 如果是系统菜单、菜单栏、Dock 等可脚本化目标，优先 AppleScript/System Events。
4. 最后才使用裸坐标点击。

裸坐标点击要求：

- 点击前确认目标窗口在前台。
- 点击前确认窗口尺寸和目标位置。
- 点击后验证结果。
- 不要把坐标写死成长期假设，除非用户明确要求一次性操作。

### 5. 键盘输入和快捷键

键盘输入按意图选择技术：

- 给文本框设置值：如果文本框在 Accessibility 树中可见，优先用 `cua-driver` 直接 set value。
- 在当前焦点输入短文本：可使用 System Events keystroke 或合适的 keyboard event。
- 发送快捷键：优先使用 AppleScript/System Events，尤其是全屏、复制、粘贴、保存、关闭窗口等系统或应用快捷键。
- 大段文本输入：优先使用剪贴板或直接设置控件值，但不要覆盖用户剪贴板，除非用户明确允许；如果需要使用剪贴板，应先保存原剪贴板并在完成后恢复。

常见快捷键：

```bash
osascript -e 'tell application "System Events" to keystroke "f" using {control down, command down}'
osascript -e 'tell application "System Events" to keystroke "s" using {command down}'
osascript -e 'tell application "System Events" to key code 53'
```

### 6. 文件、目录和命令行操作

凡是文件系统、命令行、配置文件、日志、进程、端口、包管理器等任务，优先使用 shell 命令，而不是 GUI 自动化。

适合 shell 的场景：

- 创建、读取、修改文件。
- 查找文件和文本。
- 启动本地服务。
- 查看进程、端口、日志。
- 安装依赖、运行测试、构建项目。

只有当用户明确要求在 Finder、某个 App UI、系统设置界面里操作时，才转向 macOS UI 自动化。

### 7. 系统设置和权限

系统设置、隐私权限、安全弹窗等场景通常混合使用多种技术：

- 打开对应设置面板：优先使用 `open` 或 AppleScript。
- 读取和点击设置项：优先使用 `cua-driver` 的 Accessibility。
- 视觉确认权限状态：使用 `cua-driver` 截图。
- 涉及授权、登录、支付、发送消息、删除文件等敏感动作时，先向用户确认。

### 8. 多应用任务

如果任务需要同时打开或操作多个应用，不要并行处理这些应用。应按应用和步骤串行处理，避免前台窗口、焦点、快捷键、截图和 Accessibility 快照混乱。

执行要求：

- 一次只操作一个应用。
- 每一步操作前，先将当前要操作的应用激活并置于最前面。
- 当前应用操作完成并验证后，再切换到下一个应用。
- 发送快捷键、输入文本、截图定位、读取 Accessibility 树之前，都要确认目标应用是前台应用。
- 如果多个应用都需要全屏，按顺序逐个打开、置前、全屏、验证；不要同时触发多个应用的窗口动作。

推荐节奏：

1. 打开并激活应用 A。
2. 如需要，将应用 A 全屏。
3. 完成应用 A 内的 UI 操作并验证。
4. 打开并激活应用 B。
5. 如需要，将应用 B 全屏。
6. 完成应用 B 内的 UI 操作并验证。

## 决策表

| 操作类型 | 首选技术 | 备注 |
| --- | --- | --- |
| 打开应用 | `open -a` / AppleScript | 不用 `cua-driver` |
| 激活应用 | AppleScript `activate` | 简单可靠 |
| 应用全屏 | AppleScript/System Events 快捷键 | 不用 `cua-driver` 首选 |
| 读取 UI 树 | `cua-driver` | 使用 Accessibility API |
| 点击按钮/菜单/输入框 | `cua-driver` | 先定位 AX 元素 |
| 截图和视觉验证 | `cua-driver` | 使用 Screen Recording |
| 图像区域点击 | `cua-driver` 截图定位 | 点击后验证 |
| 输入文本到已知控件 | `cua-driver` set value | 比模拟键盘更稳定 |
| 发送快捷键 | AppleScript/System Events | 适合系统级快捷键 |
| 文件和项目操作 | shell | 避免 GUI 自动化 |
| 系统权限设置 | `open` + `cua-driver` | 打开用系统命令，操作用 AX |
| 多应用操作 | 串行处理 + 逐个置前 | 不要并行操作多个应用 |

## 执行习惯

在开始操作 macOS 前，先用一句话明确技术选择：

- “这是打开应用和窗口管理，使用 AppleScript/`open`。”
- “这是读取并点击 UI 控件，使用 `cua-driver`。”
- “这是截图定位和视觉确认，使用 `cua-driver`。”
- “这是文件操作，使用 shell。”

如果操作步骤比较多，要先拆分为多个清晰步骤再执行。不要把长流程混成一次不可见的连续操作。

分步执行要求：

- 每一步只完成一个明确目标。
- 每完成一步，都要告知用户该步骤的执行情况。
- 步骤反馈要具体说明发生了什么，以及是否成功。
- 如果某一步失败或结果不确定，要说明当前状态，并调整后续步骤。
- 多应用任务也按步骤串行反馈，不要等所有应用都操作完才一次性汇报。

示例：

- “第 1 步完成：Safari 已打开并置于前台。”
- “第 2 步完成：Safari 已切换为全屏。”
- “第 3 步完成：已经点击登录按钮，正在等待页面响应。”
- “第 4 步未完成：没有在当前窗口找到目标按钮，我会先重新获取 UI 快照。”

操作后要验证：

- UI 操作用新的 Accessibility 快照验证。
- 视觉操作用截图验证。
- 命令行操作用退出码、输出、文件状态或进程状态验证。

完成用户要求的 computer use 操作后，最后要明确告知用户操作已经完成。措辞应具体说明完成了什么，而不是只说“完成了”。

示例：

- “Safari 已打开并切换为全屏。”
- “系统设置里的辅助功能权限检查已完成。”
- “文件已经在 Finder 中定位并选中。”
- “目标按钮已经点击，弹窗已关闭。”

如果首选技术失败，不要反复用同一失败方式硬试。换到下一层更合适的技术，并说明原因。

## 禁止倾向

- 不要把 `cua-driver` 当成打开应用的默认工具。
- 不要在 Accessibility 能定位元素时直接坐标点击。
- 不要在 shell 能直接完成文件任务时打开 Finder 或编辑器。
- 不要为了发送系统快捷键而先截图找位置。
- 不要无确认地执行发送、删除、购买、授权、发布等外部可见或破坏性动作。
- 不要覆盖用户剪贴板，除非用户明确允许，或能可靠保存并恢复。
