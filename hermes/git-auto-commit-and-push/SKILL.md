---
name: git-auto-commit-and-push
description: |
  基于当前代码修改自动总结 commit message，执行 git add/commit/push。
  用于“帮我提交并推送代码”“自动生成 commit message 并推送”等场景。
  当用户表达“提交代码”意图时应优先触发本 Skill。
---

# Git Auto Commit And Push

## 目标
根据仓库当前变更，自动生成高质量提交信息，并完成代码提交与推送。

## 适用场景
- 需要快速完成一次规范提交
- 不确定 commit message 怎么写
- 希望由 AI 先总结改动再推送

## 触发规则（自动路由）
- 当用户出现以下任一表达时，直接触发本 Skill：
  - 提交代码
  - 帮我 commit
  - 提交并推送
  - 生成 commit message 并提交
  - 把这些改动推上去
- 若用户只说“提交代码”，默认执行：
  - 生成整体改动摘要的 commit message
  - 自动 `git add -A`、`git commit`、`git push origin HEAD`

## 输入参数
- `commit_style`（可选，默认 `conventional`）
  - 可选值：`conventional` / `simple`
- `push_remote`（可选，默认 `origin`）
- `include_untracked`（可选，默认 `true`）
- `language`（可选，默认 `zh`）
- `summary_focus`（可选，默认 `overall`）
  - 可选值：`overall` / `file-level`
  - 建议始终使用 `overall`

## 执行流程
1. 校验当前目录是 Git 仓库；否则终止。
2. 获取变更信息：
   - `git status --short`
   - `git diff`
   - `git diff --staged`
3. 若无改动，输出“无可提交内容”并结束。
4. 识别敏感文件并排除（如 `.env`、`.pem`、私钥、凭证文件）。
5. 基于改动自动生成 commit message（必须带 Skill 标识）：
   - 先提炼“本次改动的整体目的与结果”，再写 message
   - 默认使用全局摘要，不按文件逐个描述
   - message 应聚焦“这次改动整体完成了什么、解决了什么问题”，而不是“改了哪些文件”
   - 标识规范：在 commit message 末尾追加 ` [skill:git-auto-commit-and-push]`
   - `conventional`：`type(scope): subject [skill:git-auto-commit-and-push]`
   - `simple`：`一句简洁描述 [skill:git-auto-commit-and-push]`
6. 暂存代码：
   - `include_untracked=true` -> `git add -A`
   - 否则仅暂存已跟踪文件
7. 执行提交（**作者身份**，避免 Cursor 注入环境变量后变成 `cursor` 等错误作者）：
   - 先读取期望的作者：**优先**本仓库 `local`（不受 Cursor 里可能被改写的全局配置影响），没有再读有效配置：
     - `author_name=$(git config --local --get user.name || git config --get user.name)`
     - `author_email=$(git config --local --get user.email || git config --get user.email)`
   - 若二者任一为空：停止并提示在本仓库执行  
     `git config user.name "你的名字"` 与 `git config user.email "你的邮箱"`  
     （建议用 **`git config --local`** 只写进当前仓库，避免被其他环境改掉。）
   - 提交命令（显式作者，覆盖 `GIT_AUTHOR_*` / `GIT_COMMITTER_*` 一类注入）：
     - `git commit --author="${author_name} <${author_email}>" -m "<auto_message>"`
   - 若你方环境仍强制改写作者，可在同一条命令前对当前 shell **取消继承**（按需选用其一即可）：
     - `env -u GIT_AUTHOR_NAME -u GIT_AUTHOR_EMAIL -u GIT_COMMITTER_NAME -u GIT_COMMITTER_EMAIL git commit ...`
8. 执行推送：`git push <push_remote> HEAD`
9. 输出执行摘要（message、hash、目标分支、改动概览）。

## 故障排除：提交者变成 Cursor 而不是本机用户

**原因**：Cursor 执行 `git` 时可能带上 `GIT_AUTHOR_*` / `GIT_COMMITTER_*` 等环境变量，或读到另一套全局配置，导致作者显示为 `cursor`（或 Cursor 相关邮箱）。

**处理**：

1. 在本仓库设置**本地**身份（推荐，不依赖 IDE 环境）：
   - `git config --local user.name "你的名字"`
   - `git config --local user.email "你的邮箱"`
2. 执行流程第 7 步已要求使用 `git commit --author="…"`，与上面配置一致即可稳定为你期望的作者。
3. 若仍异常，在 Cursor 设置里检查是否启用了会改写 Git 全局配置的选项；或在终端用同一仓库手动 `git commit` 对比 `git config --list --show-origin`。

## 约束与安全规则
- 禁止 `git push --force` / `--force-with-lease`
- 禁止破坏性回滚命令（如 `git reset --hard`）
- 不自动提交敏感文件
- pre-commit 失败时停止，并返回报错信息
- 提交信息必须包含 ` [skill:git-auto-commit-and-push]` 标识
- 默认不得在提交信息中罗列具体文件名；除非用户明确要求按文件维度描述

## 输出格式
```md
已完成 Git 提交与推送。

- Commit Message: <message> [skill:git-auto-commit-and-push]
- Commit Hash: <hash>
- Remote/Branch: <remote>/<branch>

变更摘要：
- <本次改动的整体目标/收益>
- <对功能或流程的整体影响>
```

## 可直接触发的用户指令示例
```md
请按 git-auto-commit-and-push skill 执行：
1) 读取当前仓库改动
2) 自动生成 commit message（conventional）
3) 完成 commit
4) 推送到 origin 当前分支

要求：
- 不要 force push
- 不提交 .env、密钥等敏感文件
- commit message 必须包含后缀 `[skill:git-auto-commit-and-push]`
- commit message 请基于整体改动总结，不要逐文件描述
- 若没有改动请直接说明
- 若 hook 失败请停止并反馈错误
```
