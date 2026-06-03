# Cline统一接管cline、claude、codex等多AI工具，并通过看板可视化管理

## 背景说明

codex、claude code等AI工具，配合deepseek、minimax、opus4.8、gpt5.5等各种模型，相信是大家日常工作中非常常用的。cline将这些全部整合起来并且可以通过看板来像notion那样拖拽管理，可以极大的提升我们的工作效率。本期视频为大家完整演示。

## 环境准备

安装[cline](https://docs.cline.bot/getting-started/installing-cline)

```shell
npm install -g cline
```

> Install Node.js 20+ (22 recommended).

确保要被接管的AI工具在终端可以使用（模型的配置是各个工具自己配置的，cline只负责整合工具）。

```shell
codex --version
claude --version
```

## 启动看板

在任意工作路径下，执行命令：

```
cline kanban
```

> 浏览器访问看板

## 使用演示

1. cline接入deepseek等国产模型非常方便，使用国产模型，完成中低难度的任务。
2. codex使用gpt5.5模型，完成中高难度的任务。
3. claude code接入opus4.8，完成高难度任务。

4种任务状态：

- Backlog
- In Progress
- Review
- Done

cline会fork一份参考在自己的工作目录下修改代码，用户确认之后才会进入用户的代码区。