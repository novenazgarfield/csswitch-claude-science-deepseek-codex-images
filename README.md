# CSSwitch × Claude Science：DeepSeek、Codex 与 Codex Images 接入指南

本项目整理了一套面向 macOS 的社区配置方案，目标包含三部分：

1. 通过 [CSSwitch](https://github.com/SuperJJ007/CSSwitch) 将 DeepSeek 接入 Claude Science；
2. 将本地 CLIProxyAPI Codex OAuth 代理作为 OpenAI-compatible provider 接入 CSSwitch；
3. 通过异步本地任务桥，将 Codex 图像模型注册为 Claude Science 工具。

本项目不是 CSSwitch、Claude Science、Anthropic 或 OpenAI 的官方扩展，不包含这些项目的源码、二进制文件、账号凭据或 API Key。

## 文档入口

| 目标 | 文档 |
| --- | --- |
| 配置 DeepSeek | [DeepSeek 接入](docs/deepseek.md) |
| 配置 Codex OAuth 文本模型 | [Codex 接入](docs/codex.md) |
| 将 Codex Images 接入 Claude Science | [Codex Images 工具桥](docs/images.md) |
| 理解整体链路与沙箱边界 | [架构说明](docs/architecture.md) |

## 整体链路

```text
Claude Science（由 CSSwitch 启动）
  │
  ├─ DeepSeek Profile
  │    └─ DeepSeek Anthropic-compatible API
  │
  └─ Codex Profile
       └─ 本机 CLIProxyAPI（OpenAI-compatible）
            └─ Codex OAuth

Claude Science Codex Image 工具
  └─ stdio MCP → 文件任务队列 → 宿主机 watcher
       └─ 本机 Codex 代理 → 图像模型
```

CSSwitch 是 Claude Science 的启动入口。Profile 选定后，应通过 CSSwitch 的「一键开始」启动隔离的 Claude Science；直接启动 Claude Science 会进入官方链路，无法应用 CSSwitch 当前选择的第三方模型配置。

## 仓库内容

```text
docs/       三条接入教程、架构说明和发布边界
examples/   不含凭据的 CSSwitch、沙箱、MCP、LaunchAgent 样例
scripts/    异步图像任务桥的沙箱端与宿主机端
```

所有配置样例均使用占位符或环境变量，可按实际部署路径替换。

## 支持范围

- 主要平台：macOS；图像桥使用用户级 LaunchAgent 示例。
- DeepSeek：使用 Anthropic-compatible endpoint。
- Codex 文本模型：已验证实现为本机 [CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI)，默认示例端口为 `127.0.0.1:8317`。
- Codex Images：实验性本地集成，通过提交任务与轮询结果规避 MCP 单次调用超时。
- Claude Science 内的多槽模型映射属于版本相关扩展；仓库说明其设计与已验证映射，但不修改或重新分发 CSSwitch 应用文件。

## 与 CSSwitch 的关系

本项目依赖 CSSwitch 提供的隔离启动和模型路由能力。CSSwitch 是独立项目，其上游仓库当前采用 MIT 许可。本项目与 CSSwitch 不存在隶属或背书关系，使用前应同时阅读 [CSSwitch README 与许可证](https://github.com/SuperJJ007/CSSwitch)。
