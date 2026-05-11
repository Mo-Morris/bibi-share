# Superpowers 项目源码分析与 Codex 最佳实践

## 一句话理解

Superpowers 不是一个传统意义上的代码库 SDK，而是一套给 coding agent 使用的软件开发方法论插件。它把“先澄清需求、再写设计、再拆计划、再 TDD 实现、再审查、再收尾”的流程做成一组可组合的 skills，并通过不同 harness 的插件机制在会话开始时注入 bootstrap，让 agent 在合适的时机自动触发对应流程。

源码里的核心并不在 `package.json`，而在 `skills/`、`hooks/`、`.codex-plugin/`、`.opencode/` 和各 harness 的适配文档里。

## 源码结构

### 插件声明

`/.codex-plugin/plugin.json` 是 Codex 插件入口。里面声明：

- 插件名：`superpowers`
- 当前版本：`5.1.0`
- skills 路径：`./skills/`
- 插件定位：planning、TDD、debugging、code review、workflow
- Codex App 展示信息：名称、描述、图标、分类、默认 prompt

这说明在 Codex 中安装 Superpowers 后，真正被发现和执行的是 `skills/` 下的每个 `SKILL.md`。

### 会话启动引导

`hooks/session-start` 会读取 `skills/using-superpowers/SKILL.md`，把它包装成 `<EXTREMELY_IMPORTANT>` 上下文注入到会话里。这个 skill 是整个系统的“启动规约”：

- 任何任务开始前都要判断是否有 skill 适用
- 只要有 1% 可能适用，就要调用或遵循对应 skill
- 用户显式指令优先级最高，其次是 Superpowers skills，再其次是默认系统提示
- Claude Code、Gemini、Copilot、Codex 等环境需要做工具名映射

这也是为什么 Superpowers 不是“你想起来才用”的资料库，而是一个强约束工作流。

### Codex 工具映射

`skills/using-superpowers/references/codex-tools.md` 说明了 Claude Code skill 文档里的工具，在 Codex 中应该怎么对应：

| Skill 里写的工具 | Codex 中的等价能力 |
|---|---|
| `Task` | `spawn_agent` |
| 多个 `Task` 并行 | 多个 `spawn_agent` |
| 等待 subagent 返回 | `wait_agent` |
| 关闭 subagent | `close_agent` |
| `TodoWrite` | `update_plan` |
| `Skill` | Codex 原生 skills 机制，直接遵循加载到的 skill |
| `Read` / `Write` / `Edit` / `Bash` | Codex 的文件和 shell 工具 |

如果要完整使用 `subagent-driven-development` 或 `dispatching-parallel-agents`，Codex 配置需要打开多 agent 能力：

```toml
[features]
multi_agent = true
```

### 核心 skills

`skills/brainstorming/SKILL.md`

用于任何创造性工作、功能设计、行为修改之前。它强制要求先理解项目上下文、逐个问题澄清、提出 2-3 个方案、让用户确认设计，再写入 `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`。没有用户批准设计前，不允许写代码。

`skills/writing-plans/SKILL.md`

把已批准的 spec 拆成可执行计划，保存到 `docs/superpowers/plans/YYYY-MM-DD-<feature>.md`。计划要求非常具体：精确文件路径、测试代码、实现代码、运行命令、预期输出、提交步骤。它假设执行者有工程能力但没有上下文，所以计划必须足够完整。

`skills/test-driven-development/SKILL.md`

实现功能或修 bug 时使用，核心规则是“没有先失败的测试，就不能写生产代码”。流程是 RED -> GREEN -> REFACTOR：先写最小失败测试，确认它因正确原因失败，再写最小实现，确认通过，然后才重构。

`skills/subagent-driven-development/SKILL.md`

按计划执行多任务时使用。控制 agent 读取计划并拆出任务，每个任务派一个新 subagent 实现，然后再派 spec reviewer 和 code quality reviewer 做两级审查。它适合有明确计划、任务相对独立、且 Codex 开启多 agent 的场景。

`skills/executing-plans/SKILL.md`

同样用于执行计划，但更适合不用 subagent 或任务耦合更强的场景。它强调按计划批量执行并在检查点验证。

`skills/verification-before-completion/SKILL.md`

在声明“完成、修好、测试通过”前使用。它要求先识别能证明结论的命令，实际运行，读取完整输出和退出码，再给出结论。不能用“应该可以”“看起来没问题”替代证据。

`skills/using-git-worktrees/SKILL.md` 和 `skills/finishing-a-development-branch/SKILL.md`

负责隔离工作区与收尾流程。Codex App 环境比较特殊，通常运行在宿主管理的 detached HEAD worktree 中，所以源码里专门加入了环境检测逻辑：

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)
```

- `GIT_DIR != GIT_COMMON` 表示已经在 linked worktree 中
- `BRANCH` 为空表示 detached HEAD
- Codex App 中常见情况是“外部管理 worktree + detached HEAD”，此时 agent 应跳过手动创建分支，完成提交后让用户用 App 的 Create branch / Hand off to local 流程处理

## 这个项目该如何用

### 作为普通用户使用

最推荐的方式是在你的 coding harness 里安装插件，而不是手动复制 skill 文件。

Codex CLI：

```text
/plugins
```

搜索 `superpowers`，选择安装。

Codex App：

1. 打开 Codex App 侧边栏的 Plugins
2. 在 Coding 分类里找到 `Superpowers`
3. 点击 `+` 安装
4. 新会话中直接描述你要构建或修复的东西

安装后，你不需要手动说“请使用 brainstorming”。正常描述需求即可，例如：

```text
我想给这个项目加一个导入 CSV 的功能
```

理想情况下，agent 会先触发 brainstorming，问清楚需求和约束，再给出设计，而不是直接改代码。

### 正常开发流

一个完整 Superpowers 工作流通常是：

1. `brainstorming`：把模糊想法变成明确设计
2. 用户确认设计
3. 写入 `docs/superpowers/specs/...-design.md`
4. `writing-plans`：把设计拆成可执行计划
5. 用户选择执行方式
6. `subagent-driven-development` 或 `executing-plans`：按计划实现
7. `test-driven-development`：每个行为先测试再实现
8. `requesting-code-review`：阶段性审查
9. `verification-before-completion`：用新鲜证据确认结果
10. `finishing-a-development-branch`：提交、分支、PR 或交接

这个流程的重点不是“多写文档”，而是降低 agent 的随意性。它把最容易失控的地方都变成检查点：需求、方案、计划、测试、审查、完成声明。

### 什么时候不适合直接开 PR

这个仓库的贡献门槛非常高。`AGENTS.md` 和 `.github/PULL_REQUEST_TEMPLATE.md` 明确要求：

- PR 前必须读完整 PR 模板
- 必须搜索 open 和 closed PR，确认不是重复
- 必须证明这是一个真实发生的问题，不是理论优化
- 必须确认改动属于 core，而不是某个项目、团队、工具或第三方服务的专用需求
- 必须让 human partner 审查完整 diff 后才能提交
- 修改 skill 内容需要 eval、压力测试和前后对比结果

所以不要把这个仓库当成“随便找 issue 让 agent 修一修”的练手项目。对 Superpowers core 的改动，最好只处理你自己真实遇到、能复现、能解释失败模式的问题。

## 在 Codex 中使用 Superpowers 的最佳实践

### 1. 把 Superpowers 当成流程约束，不是提示词素材

不要只复制 skill 内容到 prompt 里。正确姿势是安装插件，让 Codex 在会话中发现 skills，并在任务开始时遵循 `using-superpowers`。

当你发起一个需求时，尽量描述目标、背景、成功标准，而不是直接指定实现：

```text
我在使用导入功能时遇到一个问题：当 CSV 有空列名时，页面没有错误提示，只是静默失败。请帮我修复。
```

比下面这种更适合 Superpowers：

```text
改一下 parser，加个 if。
```

前者能触发更好的 debugging / brainstorming / TDD 流程。

### 2. 新功能先设计，bug 先复现

新功能：

- 让 Codex 先读项目结构
- 让它问清楚范围和成功标准
- 等它给出设计并获得你确认后再实现

Bug：

- 先给具体失败现象、报错、输入、期望输出
- 要求 Codex 找到最小复现
- 先写失败测试，再修复

好的 bug prompt：

```text
用户导入这个 CSV 时，点击提交后没有任何提示，控制台报 TypeError: Cannot read properties of undefined。期望是页面显示“CSV header is required”。请先定位根因并用 TDD 修复。
```

### 3. 在 Codex App 中注意 worktree 和分支限制

Codex App 经常把任务放在它自己管理的 worktree 里，而且可能是 detached HEAD。此时 agent 可能可以：

- 读写文件
- 运行测试
- `git add`
- `git commit`

但不一定可以：

- `git checkout -b`
- `git push`
- `gh pr create`

因此在 Codex App 中，最佳流程是让 agent 完成代码、测试和提交，然后用 Codex App 原生按钮创建分支、推送或开 PR。收尾时可以让 agent 给出：

- 建议分支名
- commit message
- PR 标题和描述
- 测试结果摘要
- 需要你人工确认的风险

### 4. 多 agent 能力只在合适时开启

如果你想完整使用 `subagent-driven-development`，需要在 Codex 配置中启用：

```toml
[features]
multi_agent = true
```

适合用 subagent 的情况：

- 已经有明确 implementation plan
- 任务之间相对独立
- 每个任务能用清晰文件边界描述
- 需要实现、spec review、code quality review 分离

不适合强行 subagent 的情况：

- 需求还没澄清
- bug 根因还不明确
- 任务高度耦合
- 改动非常小，单会话直接 TDD 更快

### 5. 要求 Codex 给证据，不要接受“应该可以”

Superpowers 的一个核心价值是反制 agent 的过早自信。你可以直接要求：

```text
完成前请使用 verification-before-completion：列出你运行的命令、退出码、关键输出和仍未验证的部分。
```

一个可靠的完成报告应该包含：

- 改了哪些文件
- 运行了哪些测试或检查
- 测试是否真的通过
- 哪些部分没有验证，为什么
- 是否有风险或后续建议

不要接受：

- “应该修好了”
- “看起来没问题”
- “我没有运行测试，但改动很小”
- “测试之前通过过”

### 6. 修改 Superpowers 本身要格外保守

如果你在 Codex 里改这个仓库本身，建议先明确问自己：

- 我解决的是一个真实发生的问题吗？
- 是否有 issue、日志、session transcript 或复现步骤？
- 这是否属于 core，而不是单个团队或工具的配置？
- 是否会影响 agent 行为？
- 如果改 skill 内容，我有没有 eval 和压力测试？
- 是否搜索过 open 和 closed PR？
- 人类是否已经审查完整 diff？

对这个仓库，很多“看起来更规范”的改动反而会被拒。例如把 skill 文案改得更符合某个外部文档、移除强硬语气、统一术语、批量格式化，都可能破坏它经过测试的行为塑形效果。

### 7. 推荐 prompt 模板

新功能：

```text
我想实现 [目标]。请结合当前源码先使用 Superpowers 的 brainstorming 流程：读取相关文件，问我必要问题，提出 2-3 个方案，等我确认设计后再写 spec 和 plan。不要先写代码。
```

Bug 修复：

```text
我遇到的真实问题是：[现象/报错/输入/期望]。请先系统性定位根因，写一个能复现问题的失败测试，确认失败后再做最小修复。完成前请运行验证命令并汇报证据。
```

执行已有计划：

```text
请执行 docs/superpowers/plans/[plan].md。若适合，请使用 subagent-driven-development；否则使用 executing-plans。每个任务按 TDD 做，任务完成后做 spec 和 code quality 检查。
```

准备 PR：

```text
请先读取 .github/PULL_REQUEST_TEMPLATE.md，并搜索 open/closed PR 是否有重复。然后检查当前 diff 是否只解决一个真实问题。不要开 PR，先把完整 diff、测试证据和 PR 模板草稿给我审查。
```

### 8. 最佳协作方式

把 Codex 当成执行力很强、但需要流程约束的工程搭档：

- 需求阶段：让它问问题，不要急着让它写代码
- 设计阶段：让它给备选方案和取舍
- 计划阶段：要求精确文件、测试、命令、预期输出
- 实现阶段：坚持 TDD 和小步提交
- 审查阶段：让 reviewer 关注 bug、回归、遗漏测试
- 收尾阶段：只相信刚运行过的验证证据

Superpowers 最适合的不是“更快地糊代码”，而是让 agent 在长任务里不飘、不编、不跳步骤。它把好的工程习惯变成会话里的硬约束，这正是它在 Codex 中最有价值的地方。
