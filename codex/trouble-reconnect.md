# Codex每次对话报错Reconnecting

## 背景说明

Codex凭借其出色的AI表现，已经有越来越多的人开始使用codex。本期视频为大家分享，使用Codex大家可能会遇到的一个重连问题。

## 原因分析

Codex需要梯子才能用，每次发起对话会创建一个子进程，子进程先尝试直连openai，如果发现不行，尝试走代理。就会多出这个5次Reconnecting。

## 解决办法

复制你的代理软件地址，例如我这里是：

```shell
export https_proxy=http://127.0.0.1:7890 http_proxy=http://127.0.0.1:7890 all_proxy=socks5://127.0.0.1:7890
```

将代理地址添加到环境变量，我这里是mac环境，编辑~/.zshrc。

> Linux为~/.bashrc，windows打开环境变量编辑配置。

```shell
export https_proxy=http://127.0.0.1:7890
export http_proxy=http://127.0.0.1:7890
export all_proxy=http://127.0.0.1:7890
```

打开[codex配置管理](https://developers.openai.com/codex/config-basic)，`open ~/.codex/config.toml`，增加如下配置：

```shell
[shell_environment_policy]
include_only = ["PATH", "HOME","https_proxy","http_proxy","all_proxy"]
```

退出codex，再重启即可。

## 更优雅的办法

在 `~/.codex`下面，新增.env文件，将上述内容加到环境变量。