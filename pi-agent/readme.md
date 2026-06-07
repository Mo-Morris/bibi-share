# pi agent 最佳实践

[pi agent](https://pi.dev/docs/latest) 是一个轻量的命令行工具，也是小龙虾底层使用的 *harnesse* agent 工具。

它只提供最基础的模型交互的能力，至于其他的harnesse agent的能力（例如Agent记忆、接入交流通道、多Agent这些），都是通过自定义拓展的方式来开发的。

非常适合想定制 *harnesse* agent 的朋友，如果你想要的是一个直接能用的 *harnesse* agent，这个pi agent也许不是很适合你，直接用openclaw、hermes会更好。

它支持自定义 TypeScript extensions、skills、prompt templates、themes 和 pi packages 来扩展能力，非常适合用来搭建定制化的 harnesse agent。

## 安装和使用

```shell
npm install -g --ignore-scripts @earendil-works/pi-coding-agent
```

然后在需要使用 AI 的项目下执行 `pi` 即可开始使用。首次使用时，先执行 `/login` 设置模型。

## 拓展功能实战

下面用一个具体项目把这些扩展方式串起来。

这个示例是一个「代码变更影响评估」的演示（为了方便演示，这是一个小范围的特定功能，也可以参考该方案，实现一些通用功能，例如Agent记忆、接入交流通道、多Agent等等）。

实现的效果是：代码提交前通常不只关心“改了什么”，还要判断影响到哪些模块、哪些地方需要人工复核。

用 extension 把这些本地信号整理成稳定的上下文，再用 skill 和 prompt template 约束 agent 的输出方式，同时覆盖 pi agent 的几种扩展方式：

- 用 `TypeScript extension` 给 agent 增加一个构造变更上下文的工具。
- 用 `custom provider` 接入团队内部的模型网关。
- 用 `skill` 固化项目内的工作习惯。
- 用 `prompt template` 做一个可复用命令。
- 用 `theme` 统一这套工具的交互外观。
- 用 `pi package` 把这些配置打包给团队复用。

### TypeScript extensions

[https://pi.dev/docs/latest/extensions#quick-start](https://pi.dev/docs/latest/extensions#quick-start)

先写一个 extension：暴露 `change_context` 工具，让 agent 一次拿到结构化的变更上下文。工具会读取几类本地信号，并返回一份 JSON：

```ts
// extensions/change-context.ts
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { execSync } from "node:child_process";
import { Type } from "typebox";

function run(command: string, cwd: string) {
  try {
    return execSync(command, {
      cwd,
      encoding: "utf8",
      maxBuffer: 1024 * 1024,
    }).trim();
  } catch (error) {
    return "";
  }
}

export default function (pi: ExtensionAPI) {
  pi.registerTool({
    name: "change_context",
    label: "Change Context",
    description: "Collect git diff, changed files, config changes, and generated-file hints for the current workspace.",
    parameters: Type.Object({
      stagedOnly: Type.Optional(Type.Boolean({ default: false })),
    }),
    async execute(_toolCallId, params, _signal, _onUpdate, ctx) {
      const diffCommand = params.stagedOnly
        ? "git diff --cached -- ."
        : "git diff -- .";

      const changedFilesCommand = params.stagedOnly
        ? "git diff --cached --name-only -- ."
        : "git diff --name-only -- .";

      const diff = run(diffCommand, ctx.cwd);
      const changedFiles = run(changedFilesCommand, ctx.cwd)
        .split("\n")
        .map((file) => file.trim())
        .filter(Boolean);

      const configHints = changedFiles.filter((file) =>
        /(^|\/)(\.github\/workflows\/|\.?[^/]*config[^/]*|[^/]*rc(\..*)?|Makefile|Dockerfile|compose\.ya?ml)$|\.ya?ml$|\.toml$|\.ini$|\.env(\..*)?$/.test(file)
      );

      const largeFiles = changedFiles.filter((file) =>
        /\.(lock|snap|svg|json)$/.test(file)
      );

      const context = {
        mode: params.stagedOnly ? "staged" : "unstaged",
        summary: run(`git diff${params.stagedOnly ? " --cached" : ""} --stat -- .`, ctx.cwd),
        changedFiles,
        configHints,
        largeFiles,
        diff,
      };

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(context, null, 2),
          },
        ],
        details: {
          files: changedFiles.length,
          bytes: Buffer.byteLength(diff, "utf8"),
          configHints: configHints.length,
          largeFiles: largeFiles.length,
        },
      };
    },
  });
}
```

把这些探查逻辑放进 extension 后，agent 拿到的是一份固定结构的上下文，而不是零散的命令输出。`changedFiles` 保留完整变更文件列表，`configHints` 只标记疑似配置改动，`largeFiles` 用来提示可能需要人工复核的生成物。

extension 也可以监听 pi 的生命周期事件。例如下面这个片段会在 session 启动时提示 extension 已加载，并在调用 `bash` 工具前拦截危险命令：

```ts
// extensions/safety-events.ts
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.on("session_start", async (_event, ctx) => {
    ctx.ui.notify("Extension loaded!", "info");
  });

  pi.on("tool_call", async (event, ctx) => {
    if (event.toolName === "bash" && event.input.command?.includes("rm")) {
      const ok = await ctx.ui.confirm("Dangerous!", "Allow rm -rf?");
      if (!ok) return { block: true, reason: "Blocked by user" };
    }
  });

  // Register a command
  pi.registerCommand("hello", {
    description: "Say hello",
    handler: async (args, ctx) => {
      ctx.ui.notify(`Hello ${args || "world"}!`, "info");
    },
  });
}
```

TypeScript extension 的“触发”可以分成两层：

1. extension 文件被加载。
2. extension 里注册的能力被使用。

第一层发生在 pi 启动或 reload 时。只要 extension 放在 pi 会发现的位置，或者通过参数显式加载，文件里的 `export default function (pi) { ... }` 就会执行：

```text
~/.pi/agent/extensions/*.ts       # 全局生效
.pi/extensions/*.ts              # 当前项目生效
pi -e ./extensions/change-context.ts   # 临时加载
```

如果 extension 放在自动发现目录里，修改后可以用 `/reload` 重新加载。

第二层取决于 extension 注册了什么：

- `pi.registerTool()` 注册的是工具。工具不会靠文件名自动执行，而是 agent 在需要时根据用户问题、系统提示和工具描述决定是否调用。例如用户执行 `/assess-change`，prompt template 要求先调用 `change_context`，agent 才会触发这个工具。
- `pi.registerCommand()` 注册的是命令。命令通过 `/命令名` 触发，例如 `/hello`。
- `pi.on("tool_call", handler)`、`pi.on("session_start", handler)` 这类事件监听，会在对应生命周期事件发生时触发。
- `pi.registerProvider()` 注册的是模型供应商。它在 extension 加载时完成注册，之后通过模型列表、模型选择或 `pi --list-models` 体现。

所以，对于上面的 `change_context` 示例，正确的触发链路是：

```text
pi 启动
  -> 加载 extensions/change-context.ts
  -> 执行 pi.registerTool({ name: "change_context", ... })
  -> 用户发起变更影响评估请求
  -> agent 判断需要读取结构化变更上下文
  -> 调用 change_context.execute()
```

### custom providers

[https://pi.dev/docs/latest/custom-provider](https://pi.dev/docs/latest/custom-provider)

除了给 agent 增加工具，也可以把团队内部的模型网关注册成 provider。配置完成后，pi 仍然使用原有的模型选择和登录流程，请求会走指定的内部 endpoint。

下面是一个 OpenAI-compatible 网关的例子：

```ts
// extensions/litellm.ts
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerProvider("LiteLLM", {
    name: "LiteLLM",
    baseUrl: "http://127.0.0.1:4000/v1",
    apiKey: "$LiteLLM_API_KEY",
    api: "openai-completions",
    models: [
      {
        id: "deepseek-v4-flash",
        name: "deepseek-v4-flash",
        reasoning: true,
        input: ["text"],
        cost: {
          input: 0,
          output: 0,
          cacheRead: 0,
          cacheWrite: 0
        },
        contextWindow: 1048576,
        maxTokens: 393216,
        compat: {
          supportsDeveloperRole: false,
          maxTokensField: "max_tokens"
        }
      }
    ]
  });
}
```

配置 custom provider 时，需要特别注意以下几点：

- `apiKey` 可以使用环境变量，比如 `$LiteLLM_API_KEY`，这样不会把密钥写进仓库。
- 大部分 OpenAI-compatible 网关可以先用 `api: "openai-completions"`。
- `models` 里要把模型能力写清楚，例如是否支持 reasoning、支持哪些输入类型、上下文长度和最大输出 token。
- 如果网关对 OpenAI 协议有细节差异，可以通过 `compat` 做适配。

配置完成后，可以先用下面的方式确认 provider 是否被正确加载：

```shell
LiteLLM_API_KEY=xxx pi --list-models
```

如果模型列表里能看到 `litellm` 下的模型，再进入 `pi` 选择对应模型使用。

编写好的 model provider 本质上是一个 extension 文件。根据使用范围，可以放在不同位置：

- 只在当前项目生效：放到项目的 `.pi/extensions/` 目录，例如 `.pi/extensions/litellm.ts`。
- 在所有项目里生效：放到全局目录 `~/.pi/agent/extensions/`，例如 `~/.pi/agent/extensions/litellm.ts`。
- 只是临时测试：通过 `pi -e ./extensions/litellm.ts` 加载指定 extension。

### skills

[https://pi.dev/docs/latest/skills](https://pi.dev/docs/latest/skills)

skill 是一组按需加载的能力说明，可以保存某类任务的工作流、注意事项、辅助脚本和参考资料。Pi 启动时会先扫描 skill 的名称和描述；当用户请求匹配时，agent 再读取完整的 `SKILL.md`。

skill 可以放在几个位置：

- 项目内生效：`.pi/skills/`
- 全局生效：`~/.pi/agent/skills/` 或 `~/.agents/skills/`
- 作为 pi package 分发：放在 package 的 `skills/` 目录
- 临时加载：通过 `pi --skill <path>` 指定

新增一个 `change-assessment` skill，用来约束 agent 评估代码变更时的口径。推荐使用目录结构，每个 skill 一个目录，目录里放必需的 `SKILL.md`：

```text
skills/
  change-assessment/
    SKILL.md
```

`SKILL.md` 顶部需要 frontmatter，其中 `name` 和 `description` 是必需字段。`description` 要写清楚“这个 skill 做什么、什么时候使用”，因为它决定 agent 是否会按需加载这个 skill。

```md
---
name: change-assessment
description: Assess workspace changes with impact, risks, and review notes. Use when the user asks to review current changes, prepare PR notes, or identify risky files.
---

# Change Assessment

## 使用场景

当用户要求评估代码变更、准备 PR 描述、提交前自查、判断复核重点时使用这个 skill。

## 工作流程

1. 先调用 `change_context` 获取结构化变更上下文。默认评估未暂存改动；如果用户只关心已暂存内容，调用时传入 `stagedOnly: true`。
2. 先看 `changedFiles` 判断影响范围；再结合 `configHints` 和 `largeFiles` 找出需要重点复核的文件；最后看 `diff`，总结具体行为变化。
3. 对 `largeFiles` 里的 lockfile、快照、生成物保持谨慎，说明它们是否需要人工复核。
4. 不输出命令清单；这里只做影响评估和复核建议。
5. 不要夸大影响范围，不要总结上下文中没有体现的内容。
6. 如果 `changedFiles` 为空，直接说明当前没有可评估的代码改动。

## 输出格式

```text
## 改了什么

## 影响范围

## 风险点

## 建议复核
```

```

这个 skill 本身不扫描工作区，它定义的是“变更影响评估”这类任务的处理流程：什么时候调用 `change_context`，以及如何解释工具返回的结构化上下文。如果需要强制使用这个 skill，可以在 pi 里执行：

```text
/skill:change-assessment
```

也可以带上额外参数：

```text
/skill:change-assessment 只评估已暂存改动，并生成 PR 描述
```

这类规则适合放在 skill 里长期维护。对于这个例子，`change_context` extension 负责提供上下文，`change-assessment` skill 负责规定评估方式。

### prompt templates

[https://pi.dev/docs/latest/prompt-templates](https://pi.dev/docs/latest/prompt-templates)
添加之后，提示词文件名可以作为命令使用。

再加一个 prompt template，把常用动作固定成一个命令。

```md
---
description: 评估当前工作区的代码变更
---

请使用 /skill:change-assessment 评估当前工作区的代码变更。

如果可以使用工具，请先调用 change_context 获取结构化上下文。
输出格式：

## 改了什么

## 影响范围

## 风险点

## 建议复核
```

添加之后，可以直接通过这个命令触发：

```text
/assess-change
```

这个命令在开发中可以高频使用：写 PR 描述、同步进度、提交前自查，都能用同一套格式。

- 项目内生效：`.pi/prompts/`
- 全局生效：`~/.pi/agent/prompts/` 或 `~/.agents/prompts/`

### themes

[https://pi.dev/docs/latest/themes](https://pi.dev/docs/latest/themes)

在这个实战里，theme 用来统一「变更影响评估助手」的交互外观。它不参与上下文读取、模型调用或评估逻辑，只负责终端里的颜色和视觉样式。

通常只需要改少量关键样式，不必从头维护整套主题。

theme 配置文件是 JSON 文件，可以放在几个位置：

- 项目内生效：`.pi/themes/*.json`
- 全局生效：`~/.pi/agent/themes/*.json`
- 作为 pi package 分发：放在 package 的 `themes/` 目录
- 通过 settings 加载：在 settings 的 `themes` 数组里写入文件或目录
- 临时加载：通过 `pi --theme <path>` 指定

当前示例采用 pi package 的组织方式，文件可以放在：

```text
my-pi-package/
  themes/
    custom-theme.json
```

加载后可以在 `/settings` 里选择主题，也可以在 `settings.json` 中指定：

```json
{
  "theme": "custom-theme"
}
```

theme 不改变 agent 的推理能力。真实主题需要按文档补齐所有颜色 token。下面这版把「变更影响评估助手」做成偏专业工具感的暗色主题：底色克制，主色用于可操作状态，差异、风险和思考强度用不同色相拉开层级。

```json
{
  "$schema": "https://raw.githubusercontent.com/earendil-works/pi/main/packages/coding-agent/src/modes/interactive/theme/theme-schema.json",
  "name": "custom-theme",
  "vars": {
    "ink": "#0b0f14",
    "panel": "#111827",
    "panelSoft": "#17202e",
    "primary": "#7dd3fc",
    "primaryStrong": "#38bdf8",
    "mint": "#34d399",
    "amber": "#fbbf24",
    "rose": "#fb7185",
    "violet": "#a78bfa",
    "muted": "#64748b",
    "subtle": "#334155",
    "textSoft": "#cbd5e1"
  },
  "colors": {
    "accent": "primary",
    "border": "subtle",
    "borderAccent": "primaryStrong",
    "borderMuted": "subtle",
    "success": "mint",
    "error": "rose",
    "warning": "amber",
    "muted": "muted",
    "dim": "#475569",
    "text": "#e5e7eb",
    "thinkingText": "textSoft",
    "selectedBg": "panelSoft",
    "userMessageBg": "panel",
    "userMessageText": "#f8fafc",
    "customMessageBg": "panel",
    "customMessageText": "#e2e8f0",
    "customMessageLabel": "primary",
    "toolPendingBg": "#101827",
    "toolSuccessBg": "#0f241d",
    "toolErrorBg": "#2a1218",
    "toolTitle": "primaryStrong",
    "toolOutput": "textSoft",
    "mdHeading": "amber",
    "mdLink": "primary",
    "mdLinkUrl": "muted",
    "mdCode": "mint",
    "mdCodeBlock": "#dbeafe",
    "mdCodeBlockBorder": "subtle",
    "mdQuote": "textSoft",
    "mdQuoteBorder": "primary",
    "mdHr": "subtle",
    "mdListBullet": "primaryStrong",
    "toolDiffAdded": "mint",
    "toolDiffRemoved": "rose",
    "toolDiffContext": "muted",
    "syntaxComment": "muted",
    "syntaxKeyword": "violet",
    "syntaxFunction": "primaryStrong",
    "syntaxVariable": "amber",
    "syntaxString": "mint",
    "syntaxNumber": "#f472b6",
    "syntaxType": "#60a5fa",
    "syntaxOperator": "primary",
    "syntaxPunctuation": "muted",
    "thinkingOff": "muted",
    "thinkingMinimal": "primary",
    "thinkingLow": "#67e8f9",
    "thinkingMedium": "mint",
    "thinkingHigh": "amber",
    "thinkingXhigh": "rose",
    "bashMode": "amber"
  }
}
```

这版主题适合代码评估类 agent：蓝色负责导航和工具标题，绿色表示成功和新增，玫红表示错误和删除，琥珀色只留给风险、标题和高强度思考，整体不会变成一片霓虹。

示例不展示完整的 50 多个颜色 token。实际使用时，可以先复制官方主题模板，再按上面的色板替换关键颜色。

把 theme 放进 package 之后，团队安装 package 时会一起拿到这套样式。

### pi packages

[https://pi.dev/docs/latest/packages](https://pi.dev/docs/latest/packages)
pi package 可以把前面的扩展统一打包，放到 Git 仓库里分发给团队使用。

支持多种方式安装

```shell
pi install npm:@foo/bar@1.0.0
pi install git:github.com/user/repo@v1
pi install https://github.com/user/repo  # raw URLs work too
pi install /absolute/path/to/package
pi install ./relative/path/to/package
# 移除
pi remove npm:@foo/bar
pi list                     # show installed packages from settings
```

`package.json`

```json
{
  "name": "my-package",
  "keywords": ["pi-package"],
  "pi": {
    "extensions": ["./extensions"],
    "skills": ["./skills"],
    "prompts": ["./prompts"],
    "themes": ["./themes"]
  }
}
```

把这个仓库分发给团队后，团队成员就能使用同一套命令、工具和输出规范。后续可以继续扩展，例如：

- 让 prompt template 支持“只评估 staged changes”，并把参数传给 `change_context`。
- 在 prompt template 里增加“请生成 PR title”。
- 在 skill 里补充团队特定的发布检查项、灰度策略和回滚要求。
- 在 extension 里读取 `CODEOWNERS` 或模块元数据，自动提示需要关注的负责人或目录边界。
- 再写一个 extension 读取最近一次 CI 结果，把风险判断和复核重点补充得更具体。

可以先用 prompt template 固定入口，再用 skill 固定行为规范，最后用 extension 接入项目上下文。这样组织后，工具、流程和分发方式都能分别维护。