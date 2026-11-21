# Hermes Kanban多Agent实战演示

## 背景说明

之前给大家分享了多Agent实战，内容比较基础，主要是想给大家分享多Agent如何管理，接入飞书，以及Agent配置等相关操作。但是多Agent之间并没有完全协作起来，本期内容给大家分享Hermes的看板模式，真正让多Agent协作起来。

## 理解Kanban状态

[官方文档](https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban-tutorial)

## 触发任务执行规则

每隔 `kanban.dispatch_interval_seconds` 跑一次，默认 60 秒。
如果想更快响应，可以把间隔调小，例如 10 秒：

```shell
hermes config set kanban.dispatch_interval_seconds 10
```

网页里如果有 Nudge dispatcher 按钮，它本质上就是跳过等待，手动触发一次 dispatch。等价于命令：

```shell
hermes kanban dispatch --max 1 --json
```

`hermes kanban specify <id>`已经移除了，不支持这个操作。

## 任务规划（命令行使用） 

设置工作路径

```shell
export WORKSPACE=dir:/Users/morrismo/Desktop/work/hermes-kanban-lab
```

创建第一个任务，任务内容是开发API接口：

```shell
hermes kanban create "parent api design" \
    --workspace $WORKSPACE \
    --assignee sunwukong --tenant fruit-supermarket --priority 2 \
    --body "用fastapi实现一个API接口，接口返回一个水果列表，包含水果的名称，单价，产地，项目依赖的包放到requirements.txt" \
    --json | jq -r .id
```

设置父级任务ID

```shell
export PARENT_ID=t_6cec0ebf
```

创建第二个任务，任务内容是开发前端页面：

```shell
hermes kanban create "child web design" \
    --workspace $WORKSPACE \
    --assignee default --tenant fruit-supermarket --priority 2 \
    --body "实现一个简单的网页展示，调用后端的接口，将数据在前端页面中展示出来" --parent $PARENT_ID \
    --json | jq -r .id
```

创建第三个任务，任务内容是编写测试用例：

```shell
hermes kanban create "child test design" \
    --workspace $WORKSPACE \
    --assignee zhubajie --tenant fruit-supermarket --priority 2 \
    --body "编写API接口的测试用例" --parent $PARENT_ID \
    --json | jq -r .id
```

创建第四个任务，等二，三任务都执行完毕之后，编写一个项目说明。

```shell
hermes kanban create "grandchild docs design" \
    --workspace $WORKSPACE \
    --assignee default --tenant fruit-supermarket --priority 2 \
    --body "编写项目说明，如何在本地运行该项目" --parent t_2ba62d6d  --parent t_bd2b09fe \
    --json | jq -r .id
```

