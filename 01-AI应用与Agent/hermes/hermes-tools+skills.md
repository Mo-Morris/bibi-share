# **Hermes MCP 与 Skills 综合实战演示**

## 背景说明

OpenClaw不支持MCP，所有能力仅通过Skills的方式与外部对接。Hermes这块更加的开放，MCP与Skills均支持配置。大家千万不能有一个误区，认为MCP能做的，Skills也能做，所以Skills就可以完全替代MCP了。其实两者是完全可以各自独立使用，也可以配合使用，MCP的仍然有其存在的价值，可以非常方便的去对接各种服务。这也是Hermes为什么会独立集成MCP和Skills的原因。下面将Hermes中MCP与Skills的操作演示一起给同学们做分享。

## Hermes MCP 使用教程

编辑配置文件 `open ~/.hermes/config.yaml`，yaml的一级目录下添加如下配置：

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/Users/morrismo/Desktop/work/hermes-mcp-workspace"]
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: ghp_xx
```

进入hermes终端，执行`/tools`即可查看mcp的状态。
以github来举例：

```md
帮我创建一个名为hello-hermes-mcp的项目。
```

```md
为hello-hermes-mcp写一个issue，内容是“请介绍该项目的功能”
```

```md
提交一个commit，初始化一个README.md文件，内容为：这是一个通过hermes agent创建的github项目。
```

## Hermes Skills使用教程

### 安装公开的Skills

```shell
# 从所有站点查询skils
hermes skills search ppt
# 从指定站点查询skills
hermes skills search ppt --source clawhub 
# 找到合适的skills进行安装
hermes skills inspect <identifier> 
hermes skills install <identifier> 
```

使用skills提示词

```md
生成内容：如何保持高效的工作节奏
```

```md
将上述内容整理为PPT，并写到/Users/morrismo/Desktop/work/hermes-mcp-workspace
```

### 安装自定义的Skills

有些时候，访问公开的Skills有由于网络的限制无法访问，或者有些自己的定制Skills。  
直接将Skills放到Hermes的SKills配置目录`~/.hermes/skills`即可。

演示`git-auto-commit-and-push`，进入到前面创建的hello-hermes提交代码。

### 将Hermes的对话结果总结一个Skills

例如你把与Hermes的某次对话，觉得以后可以复用，可以在任务完成之后，提示Hermes总结为Skill。

```md
帮我整理一下今天会议纪要：

今天讨论了 OCR 模型训练问题。
目前线上 badcase 主要是字迹潦草。Morris
数据集类别不平衡。
需要增加 difficult case。Sam
下周准备重新训练。Tim
```

约定会议纪要的格式

```md
不要只是简单罗列。
我希望：
自动提炼问题
区分“现状 / 原因 / 方案 / 风险”
输出 action item
用更正式一点的项目风格
最后给出负责人和时间，如果我没有给出具体的负责人，请提醒我
```

再次约定会议纪要的格式

```md
生成会议纪要时：
* 自动识别技术风险
* 自动提取待办事项
* 自动按“背景 / 问题 / 决策 / Action”结构输出
* 如果会议内容比较混乱，要自动重组逻辑
* 输出要偏 SaaS / 技术项目管理风格
```

将经验沉淀为Skills

```
帮我把上述的会议纪要要求内容沉淀成 Skills，方便我下一次直接使用
```

再次给出会议纪要时，直接给出内容即可。

```md
帮我整理下面会议内容：
模型线上误识别率上涨。Tim
怀疑是新增数据污染。Sam
准备增加数据校验。Morris
需要本周完成回滚方案。Dove
```

## 小结

**定位**：Hermes 同时支持 MCP 与 Skills，二者并非「谁替代谁」。MCP 适合对接外部服务与工具链（GitHub、文件系统等），Skills 适合沉淀流程、格式约定与可复用的对话模板；可按场景单独使用，也可在同一任务里配合使用。

**MCP 要点**：在 `~/.hermes/config.yaml` 的 `mcp_servers` 下声明服务后，用 `hermes tools` 核对加载是否成功；示例中的 GitHub、filesystem 说明只要把 Token、路径配好，就可以在对话里直接驱动仓库与本地目录。

**Skills 要点**：公开 Skills 用 `hermes skills search`（可加 `--source`）查找并安装；自建或离线 Skills 放入 `~/.hermes/skills`。把高频对话（如会议纪要结构、输出风格）让 Hermes 总结成 Skills，下次一句指令即可复用，减少重复提示。

**实践建议**：新接入能力优先想清楚——是需要「连某个服务的 API/CLI」（倾向 MCP），还是需要「固定一套步骤或文风」（倾向 Skill）；二者都配齐后，用 `hermes tools` 与 `hermes skills` 定期环境与可用技能，避免「配了却没用上」。