[toc]

# Hermes  安装、升级、配置、可视化、卸载全链路实战教程

## 背景说明
Hermes  安装、升级、配置、可视化、卸载全链路实战教程
结合之前openclaw 3.24的升级事故（每次更新都发布了非常多的feature，服务出现故障是必然，我们要尽可能防范），强烈建议大家容器版和宿主机版的安装能力都要具备[[容器版Hermes安装教程](https://github.com/Mo-Morris/bibi-share/tree/main/hermes)]。容器为辅，宿主进版本为主，因为宿主机的能够执行主机上的操作更多，例如做表格、文档、操作浏览器等，都更加方便。  
当新版本来了之后，先升级容器版验证各项功能是否可用，然后再放心的升级宿主机版本。

## 安装和升级

不建议按照[官方文档](https://hermes-agent.nousresearch.com/docs/getting-started/quickstart)操作，官方文档仅供参考用。

前置条件，检查主机上是否安装了git环境，最好把梯子打开。

克隆源代码

```shell
git clone https://github.com/NousResearch/hermes-agent
```

查找最新的[release版本](https://github.com/NousResearch/hermes-agent/tags)

```shell
cd hermes-agent
git checkout v2026.4.23
```

安装hermes，

```shell
# 安装
./setup-hermes.sh
# 刷新系统配置
source ~/.bashrc
```

升级hermes

```shell
# 进入hermes源码
cd hermes-agent
# 切换到主分支
git checkout main
# 拉取最新代码
git pull
# 切换到指定tag，例如
git checkout v2026.5.9
# 覆盖安装
./setup-hermes.sh
# 刷新系统配置
source ~/.bashrc
```

## 配置

在第一步安装命令，会提示配置各项内容，执行如下命令可以对指定的配置做修改。

```shell
hermes model          # 选择模型供应商
hermes tools          # 选择开启哪些工具
hermes gateway setup  # 配置消息交流平台
hermes gateway start  # 启动gateway
hermes config set     # 修改指定配置
hermes setup          # 重新执行向导模式
```

## 可视化管理

参考GitHub项目 [https://github.com/EKKOLearnAI/hermes-web-ui](https://github.com/EKKOLearnAI/hermes-web-ui)

安装

```shell
npm install -g hermes-web-ui
hermes-web-ui start
```

> 安装后访问：[http://localhost:8648](http://localhost:8648)

webui的其他相关操作

```shell
# Start in background (daemon mode)
hermes-web-ui start	
# Start on custom port
hermes-web-ui start --port 9000	
# Stop background process
hermes-web-ui stop
# Restart background process
hermes-web-ui restart
# 检查运行状态
hermes-web-ui status
# 更新到新版本，并重启
hermes-web-ui update
# 查看版本
hermes-web-ui -v
```

## 卸载

停止gateway

```shell
hermes gateway stop
```

删除gateway注册的系统服务（这个操作可选，如果没有设置为开启启动，则不用执行）

```shell
# Linux: 
systemctl --user disable hermes-gateway
# macOS: 
launchctl remove ai.hermes.gateway
```

使用hermes封装的命令卸载

```shell
hermes uninstall
```

手动卸载

```shell
rm -f ~/.local/bin/hermes
rm -rf /path/to/hermes-agent
rm -rf ~/.hermes            # Optional — keep if you plan to reinstall
```

