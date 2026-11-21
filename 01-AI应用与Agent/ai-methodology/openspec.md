# OpenSpec 最佳实践

OpenSpec 是一套面向 AI 编程助手的规格驱动开发流程。它不会替代 Cursor、Claude Code、Codex 等工具，而是通过项目里的 `openspec/` 目录和 AI 工具专属命令文件，把“需求、设计、任务、规格、归档”沉淀成可追踪的工程流程。

在 Cursor 中使用时，OpenSpec 会生成 `.cursor/commands/opsx-*.md`，Cursor 读取这些命令文件后，就可以通过 `/opsx-*` 命令执行 OpenSpec 工作流。

## 安装

```shell
npm install -g @fission-ai/openspec@latest
```

也可以不全局安装，直接使用：

```shell
npx @fission-ai/openspec@latest --help
```

## 从空白项目开始

如果是一个完全空白的项目，建议先创建项目目录，再初始化 OpenSpec 和 Cursor 命令。

```shell
mkdir my-app
cd my-app
openspec init --tools cursor --force
```

初始化后会生成：

```text
openspec/
  config.yaml
  specs/
  changes/
  changes/archive/

.cursor/
  commands/
    opsx-propose.md
    opsx-explore.md
    opsx-apply.md
    opsx-sync.md
    opsx-archive.md
```

完成后重启 Cursor，让 Cursor 重新加载 `.cursor/commands/` 里的命令。

## 空白项目的推荐节奏

空白项目不要一开始就让 AI “直接写完整系统”。更稳的做法是先建立项目骨架，再逐个功能推进。

第一步，创建初始化变更：

```text
/opsx-propose initialize-project

从空白项目初始化一个 React + TypeScript + Vite 应用，并实现基础首页：
- 使用 npm
- 使用 TypeScript
- 使用 Vite
- 首页显示应用名称和一个可点击按钮
- 添加基本的 dev/build 脚本
```

然后执行：

```text
/opsx-apply initialize-project
```

完成后再进入第二个功能，例如：

```text
/opsx-propose add-todo-feature

在现有应用中增加 Todo 功能：
- 新增 Todo
- 完成 Todo
- 删除 Todo
- localStorage 持久化
- 支持全部/未完成/已完成过滤
```

再执行：

```text
/opsx-apply add-todo-feature
```

这种方式的好处是：每个变更都有独立的 proposal、design、tasks 和 spec，后续回看、调整、归档都更清晰。

## Cursor 中的核心命令

### `/opsx-propose`

用于创建一个新的 OpenSpec 变更，并生成需求、设计、任务和规格草案。

适合在“准备开始一个明确功能”时使用。

示例：

```text
/opsx-propose build-todo-app

从空白项目创建一个 React + TypeScript Todo 应用：
- 使用 Vite
- 支持新增、完成、删除 Todo
- 支持按全部/未完成/已完成过滤
- 数据保存在 localStorage
- 页面需要简洁可用
```

生成目录类似：

```text
openspec/changes/build-todo-app/
  .openspec.yaml
  proposal.md
  design.md
  tasks.md
  specs/
    todo-app/
      spec.md
```

### `/opsx-apply`

用于根据某个变更里的任务真正开始实现代码。

示例：

```text
/opsx-apply build-todo-app
```

它会读取：

```text
openspec/changes/build-todo-app/proposal.md
openspec/changes/build-todo-app/design.md
openspec/changes/build-todo-app/tasks.md
openspec/changes/build-todo-app/specs/
```

然后按 `tasks.md` 逐项实现。每完成一个任务，应该把任务从：

```markdown
- [ ] 实现 Todo 新增功能
```

更新为：

```markdown
- [x] 实现 Todo 新增功能
```

### `/opsx-explore`

用于探索、分析、澄清需求，不应该直接进入实现。

适合这些场景：

- 想法还比较模糊
- 不确定应该怎么拆任务
- 不确定现有代码是否支持某个功能
- 想先让 Cursor 阅读代码和规格，给出方案建议

示例：

```text
/opsx-explore

我想给 Todo App 增加拖拽排序。请先分析：
- 当前代码是否容易支持排序
- localStorage 结构需不需要调整
- 是否建议使用第三方拖拽库
- 应该拆成哪些 OpenSpec 变更
```

它的价值是把“模糊想法”变成“可落地的变更计划”。通常探索完成后，再执行：

```text
/opsx-propose add-drag-sort
```

### `/opsx-sync`

用于把变更中的规格增量同步到主规格。

变更中的规格通常位于：

```text
openspec/changes/<change-name>/specs/
```

主规格位于：

```text
openspec/specs/
```

如果实现完成后变更包含新的能力规格，应该同步到主规格，让项目长期规格保持最新。

示例：

```text
/opsx-sync build-todo-app
```

### `/opsx-archive`

用于把已经完成的变更归档。

示例：

```text
/opsx-archive build-todo-app
```

它不会删除业务代码，也不会撤销实现结果。它主要做三件事：

- 检查 `proposal.md`、`design.md`、`tasks.md` 等 artifacts 是否完成
- 检查是否需要把变更规格同步到 `openspec/specs/`
- 把变更目录从 active changes 移到 archive

归档后目录会从：

```text
openspec/changes/build-todo-app/
```

移动到类似：

```text
openspec/changes/archive/2026-05-06-build-todo-app/
```

归档相当于 OpenSpec 流程里的“完成并关闭变更”。之后 `openspec list` 通常不会再把它显示为进行中的变更。

## 推荐工作流

一个完整功能通常按这个节奏走：

```text
/opsx-explore     先探索模糊需求，可选
  ↓
/opsx-propose     创建正式变更和计划
  ↓
/opsx-apply       根据任务实现代码
  ↓
/opsx-sync        同步规格，可选但推荐
  ↓
/opsx-archive     归档完成的变更
```

如果需求已经很明确，可以跳过 `/opsx-explore`，直接从 `/opsx-propose` 开始。

## 使用注意事项

- 空白项目里一定要明确技术栈，例如 React + TypeScript + Vite、Next.js、Node.js + Express 等。
- 不要把多个大功能塞进一个 change，优先拆成小而完整的变更。
- `/opsx-explore` 用来想清楚方案，`/opsx-apply` 才负责改代码。
- `/opsx-archive` 只是归档 OpenSpec 变更，不会删除已经实现的业务代码。
- 每次初始化或更新 Cursor 命令后，建议重启 Cursor。
- 如果 Cursor 中提示 `/opsx:apply`，但命令不存在，优先尝试 hyphen 风格：`/opsx-apply`。当前 Cursor 适配器生成的是 `.cursor/commands/opsx-<id>.md`。

## 实战示例：从 0 创建 Todo App

1. 初始化：

```shell
mkdir todo-app
cd todo-app
openspec init --tools cursor --force
```

2. 重启 Cursor，执行：

```text
/opsx-propose build-todo-app

从空白项目创建一个 React + TypeScript + Vite Todo 应用：
- 支持新增 Todo
- 支持完成 Todo
- 支持删除 Todo
- 支持全部/未完成/已完成过滤
- 使用 localStorage 保存数据
- 页面简洁可用
```

3. 检查生成的计划和任务：

```text
请检查 build-todo-app 这个 OpenSpec 变更，确认需求、设计和任务是否完整。
```

4. 实现：

```text
/opsx-apply build-todo-app
```

5. 实现完成后，同步规格：

```text
/opsx-sync build-todo-app
```

6. 归档：

```text
/opsx-archive build-todo-app
```

完成后，Todo App 的代码保留在项目中，OpenSpec 的变更记录会进入 `openspec/changes/archive/`，主规格会保留在 `openspec/specs/` 中。
