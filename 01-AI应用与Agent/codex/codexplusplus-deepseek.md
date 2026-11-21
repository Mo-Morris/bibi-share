# CodexPlusPlus + CC Switch接入DeepSeek到Codex

国内用户，直接使用Codex的痛点：

- 没有ChatGPT账号，虽然可以使用api key方式绕开登录，但是无法使用插件
- API路由无法切换，只能使用官方模型
- 无法接入DeepSeek等需要转换协议的模型
Codex++可以完美解决上述3个问题，并且带来了一系列的附加功能，但是如果要接入DeepSeek等国产模型，还需要用到CC Switch。

## 安装&配置

Codex
[https://chatgpt.com/zh-Hans-CN/codex/](https://chatgpt.com/zh-Hans-CN/codex/)

Codex++
[https://github.com/BigPizzaV3/CodexPlusPlus](https://github.com/BigPizzaV3/CodexPlusPlus)

CC Switch
[https://github.com/farion1231/cc-switch](https://github.com/farion1231/cc-switch)

## 使用

1. cc switch接入deepseek供应商
2. 启动codex++

## 使用注意

codex在不断的探索项目，发送很多定时心跳，会导致token消耗巨大。