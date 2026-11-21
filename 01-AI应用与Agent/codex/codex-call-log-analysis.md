# Codex 调用日志分析报告

分析对象：`/Users/morrismo/Downloads/codex一直call接口.csv`  
日志范围：2026-06-22 09:37:37.219 至 09:47:07.711  
相关项目：`/Users/morrismo/Desktop/labs/oh-my-pi`

## 一句话结论

这份日志体现的不是 oh-my-pi 项目自身在定时调用 API，而是 Codex Desktop 在 oh-my-pi 项目上下文里发起了多个对话回合，其中最主要的调用量来自自动/个性化建议任务：

```text
Generate 0 to 3 hyperpersonalized suggestions for what this user can do with Codex in this local project
```

这类任务会把项目当作一个“小型代码审计对象”来探索：先看 git 历史和分支状态，再看文档、项目结构、最近重构涉及的源码，最后找测试缺口并生成建议。

## 总体统计


| 指标                         | 数值                  |
| -------------------------- | ------------------- |
| CSV 行数                     | 91                  |
| 有效 Codex turn 请求           | 89                  |
| 使用模型                       | `deepseek-v4-flash` |
| `finish_reason=tool_calls` | 82                  |
| `finish_reason=stop`       | 7                   |
| 总工具调用数                     | 117                 |
| 多工具并发/批量响应次数               | 20                  |
| 单次响应最多工具调用数                | 4                   |
| prompt tokens 总量           | 2,974,330           |
| completion tokens 总量       | 33,161              |
| cached prompt tokens 总量    | 2,583,680           |
| reasoning tokens 总量        | 19,874              |
| 最大单次 prompt tokens         | 58,188              |
| 最大请求体长度                    | 151,264 字符          |
| 最大 HTTP `content-length`   | 239,655             |
| 记录到的 `response_cost` 合计    | 0.071210384         |
| `max_retries`              | 全部为 0               |
| `attempted_retries`        | 日志中未记录实际重试          |


一个重要观察：大量请求的 `finish_reason` 是 `tool_calls`，说明模型并不是在“重复返回答案”，而是在不断要求 Codex 执行工具。链路是：

```text
模型请求工具调用
-> Codex 执行 shell 命令
-> 工具结果追加进上下文
-> 再次请求模型
-> 模型继续请求工具
-> 直到最后 stop
```

## Turn 分组

同一个用户动作或后台动作，在 Codex 里会被标记为一个 `turn_id`。一个 turn 下面可能有多次 `/v1/chat/completions` 请求。


| turn_id                                | 请求数 | 持续时间     | prompt tokens | completion tokens | 工具调用 | 任务特征            |
| -------------------------------------- | --- | -------- | ------------- | ----------------- | ---- | --------------- |
| `019eeeb1-cc4b-7373-8b69-21f20f594d68` | 1   | 0s       | 13,974        | 42                | 0    | 用户输入 `hi`       |
| `019eeeb1-cc93-7ec1-93ab-5112dc610bf6` | 1   | 0s       | 13,076        | 98                | 0    | 生成 UI 标题        |
| `019eeeb2-10a5-7331-a941-ed282e9f79a8` | 14  | 38.841s  | 541,371       | 6,015             | 36   | 用户提问：`分析该项目的原理` |
| `019eeeb2-1132-7c30-97b5-390d0d6b6740` | 1   | 0s       | 17,329        | 69                | 0    | 生成 UI 标题        |
| `019eeeb2-168f-7df3-b382-c5b408e4ba2e` | 28  | 108.572s | 825,484       | 7,938             | 27   | 自动个性化建议         |
| `019eeeb4-da48-7cb1-9a10-a7d9a994ceee` | 9   | 62.342s  | 265,708       | 5,975             | 20   | 自动个性化建议         |
| `019eeeb7-5055-7c90-8fb0-2f917d9f9840` | 35  | 175.928s | 1,297,388     | 13,024            | 34   | 自动个性化建议，最大的一组   |


最值得注意的是：用户真正的项目分析请求确实触发了 14 次模型请求，但更大的消耗来自后面三组自动建议任务，总共 72 次请求、81 次工具调用。

## 工具调用类型


| 类型        | 次数  | 说明                                             |
| --------- | --- | ---------------------------------------------- |
| 读文件/读片段   | 53  | `head`、`cat`、`sed`、`wc`                        |
| git 历史/状态 | 25  | `git log`、`git show`、`git branch`、`git status` |
| 列目录/文件    | 18  | `ls`                                           |
| 搜索/查找     | 17  | `rg`、`grep`、`find`                             |
| 其他 shell  | 2   | 例如 `which omp`                                 |
| 项目命令      | 1   | `bun check`                                    |
| 计划工具      | 1   | `update_plan`                                  |


工具名分布：


| 工具             | 次数  |
| -------------- | --- |
| `exec_command` | 116 |
| `update_plan`  | 1   |


这说明探索基本都发生在 shell 层，而不是通过浏览器或外部 connector。

## 有特色的探索路径

### 1. 先用 git 历史判断“你最近在干什么”

典型命令：

```bash
git log --oneline -20
git log --format="%H %ai %s" --all -30
git branch -a | head -30
git log --oneline --all --since="2 days ago" --format="%H %ai %an %s" | head -30
git status
```

这一步的作用是给项目建立近期工作画像。日志中后续建议会围绕最近提交展开，例如：

```text
refactor(coding-agent): standardized evaluation kernel and executor architecture
refactor(coding-agent): consolidated parallel API logic
refactor(coding-agent): established shared subprocess infrastructure
```

模型并不是随机浏览文件，而是沿着最近重构记录继续追源码和测试。

### 2. 追最近提交的 stat，锁定重构热点

典型命令：

```bash
git show --stat a94cadf72 | head -40
git show --stat 92bae8ab9
git show --stat 175097350
git log --oneline -1
git log --oneline HEAD~10..HEAD | head -20
```

这类命令帮助模型识别“刚发生过大改动的模块”。在这份日志里，探索重点逐渐收敛到：

- `packages/coding-agent/src/eval/`
- `packages/coding-agent/src/subprocess/`
- `packages/ai/src/`
- `packages/coding-agent/CHANGELOG.md`

### 3. 把用户已有中文文档也纳入上下文

典型命令：

```bash
head -50 特点分析.md
head -30 特点分析2.md
head -30 docs/omp-best-practices.zh.md
tail -100 特点分析2.md
```

这是一个很有特色的点：Codex 不只看代码，也会看用户自己写的中文分析文件。它据此推断用户可能正在做：

- oh-my-pi 原理分析
- 中文最佳实践文档
- 把已有分析转成可落地教程

所以后续自动建议里出现了“完善中文 best practices guide”“让 docs 可发现”等方向。

### 4. 追到测试覆盖缺口

在最大的自动建议 turn 里，探索从 git 历史一路追到测试目录：

```bash
find packages/coding-agent/src/eval -type f -name "*.ts" | sort
ls packages/coding-agent/src/eval/js/
rg -l "kernel-base|executor-base" packages/coding-agent/src/eval/__tests__/ 2>/dev/null
rg -l "worker-client|worker-runtime" packages/coding-agent/src/eval/__tests__/ packages/coding-agent/test/ 2>/dev/null
wc -l packages/coding-agent/src/eval/js/executor.ts packages/coding-agent/src/eval/executor-base.ts
head -20 packages/coding-agent/src/eval/js/executor.ts
```

这解释了为什么最后的建议不是泛泛地“优化项目”，而是非常具体：

- 给新的 `kernel-base` / `executor-base` 加单测
- 给 `worker-client` / `worker-runtime` 加单测

这是典型的“从最近重构 -> 找核心抽象 -> 搜测试覆盖 -> 生成可执行建议”的路径。

### 5. 请求上下文持续膨胀

最大的一组 turn：`019eeeb7-5055-7c90-8fb0-2f917d9f9840`


| 序号  | 时间           | prompt tokens | messages | tool messages | finish       |
| --- | ------------ | ------------- | -------- | ------------- | ------------ |
| 0   | 09:44:11.783 | 16,908        | 3        | 0             | `tool_calls` |
| 1   | 09:44:14.224 | 17,464        | 5        | 1             | `tool_calls` |
| 2   | 09:44:15.971 | 19,191        | 7        | 2             | `tool_calls` |
| 3   | 09:44:18.982 | 20,121        | 9        | 3             | `tool_calls` |
| 4   | 09:44:22.153 | 22,010        | 11       | 4             | `tool_calls` |
| 30  | 09:46:32.517 | 52,689        | 63       | 30            | `tool_calls` |
| 31  | 09:46:46.460 | 54,809        | 65       | 31            | `tool_calls` |
| 32  | 09:46:49.250 | 55,089        | 67       | 32            | `tool_calls` |
| 33  | 09:46:54.854 | 55,904        | 69       | 33            | `tool_calls` |
| 34  | 09:47:07.711 | 58,188        | 71       | 34            | `stop`       |


这个增长非常典型：每执行一次工具，工具输出就进入下一次模型请求的 messages，导致 prompt tokens 和请求体不断变大。

