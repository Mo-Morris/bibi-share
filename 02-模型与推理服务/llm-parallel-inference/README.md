# 大模型并行推理

[知识首页](../../README.md) / [模型与推理服务](../README.md)

从大模型结构和显存占用讲起，通过切蛋糕的例子和手绘图，理解 TP、PP、DP、EP、CP 五种并行方式，再看它们怎样组合。

## 图文教程

[一口气看懂大模型并行推理：TP、PP、DP、EP 和 CP](./parallel-inference.md)

正文依次讲解张量并行、流水线并行、数据并行、专家并行和上下文并行，并穿插 TP + PP、TP + PP + DP、DP + EP、TP + PP + CP 的组合示例。

已于 2026-11-21 发布到 [知乎](https://zhuanlan.zhihu.com/p/2107523849315148135)。

## 配套资料

| 资料 | 说明 |
| --- | --- |
| [正文配图](./images/) | 图文教程中的 9 张原图，按正文中的相对链接加载 |
| [可编辑画布](./diagrams/parallel-inference.excalidraw) | 完整 Excalidraw 场景，含 17 张内嵌图片，可下载后导入编辑 |
| [视频字幕](./subtitles/parallel-inference.srt) | 保留最终成片时间轴的 SRT，共 646 条字幕 |
| [发布文案](./publishing-notes.txt) | 视频标题、简介和 Tag |
| 封面 | [4:3 横版](./covers/cover-4x3.png)、[3:4 竖版](./covers/cover-3x4.png)、[16:9 横版](./covers/cover-16x9.png) |

字幕和画布保留视频中的讲解记录；术语及实现边界的补充说明见图文教程。
