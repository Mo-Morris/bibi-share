# Hermes Agent Computer Use使用教程

## 背景说明

通过集成[cua-dirver](https://github.com/trycua/cua)库，Hermes Agent已经支持操作Mac电脑了。本期视频详细讲解工作原理，以及操作电脑时的实战技巧。

[官方文档](https://hermes-agent.nousresearch.com/docs/user-guide/features/computer-use)

## 工作原理

cua-driver 能操作电脑，不是因为绕过 macOS，而是把 Accessibility API、Screen Recording、窗口/进程事件投递等系统能力组合起来，并封装成适合 Agent 使用的 `snapshot → element_index → action → verify` 工作流。AI 既可以读取 UI 树并调用控件动作，也可以借助截图做视觉定位和结果验证。因此 Hermes Agent 如果要做通用 computer use，必须接入支持图像理解的多模态模型；纯文本模型可以辅助规划和分析，但单独使用会明显受限。

## 安装 hermes computer use

升级hermes版本，版本大于 [v0.14.0 (v2026.5.16)](https://github.com/NousResearch/hermes-agent/releases)

```shell
# 安装 cua-driver
hermes computer-use install
# 验证
hermes computer-use status
```

触发了cua-driver会提示你授权，所以不用专门到个人&隐私去授权。

## 触发computer use的技巧总结

提示词技巧：computer-use-helper.skill，此外：

- 推荐通过聊天通道来管理computer use，不会导致光标，输入聚焦的位置发生变化。如果在终端执行computer use，会依次询问权限，选择**Add to permanent allowlist，这样后面不用把光标切换回来，保证computer use的稳定性。**
  - **Allow once**  
  只允许这一次按 cmd+l。下一次再按键、点击、输入等，还会继续问。
  - **Allow for this session**  
  本次会话里允许当前这类动作。对这里来说，会放行 key 动作，后续按键一般不再问；点击、输入、滚动等其他动作可能还会问。
  - **Add to permanent allowlist**  
  字面意思像“永久加入白名单”，但在这个 computer_use 场景里，源码实际效果更激进一点：**本次 Hermes 运行期间，computer_use 的后续 GUI 动作基本都自动通过**，包括 key、click、type、scroll 等。  
  它不是只永久放行 cmd+l 这一条，也不是真正写入永久配置。重启 Hermes 后通常会失效。
  - **Deny**  
  拒绝这次动作。agent 不会执行 cmd+l，通常会收到“denied by user”的工具错误，然后可能换别的方法、停止，或者继续请求你批准别的动作。

