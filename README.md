# CSSwitch × Claude Science：DeepSeek、Codex 与 Codex Images 接入指南

简体中文 | [English](README.en.md)

本项目整理了一套面向 macOS 的社区配置方案，目标包含三部分：

1. 通过 [CSSwitch](https://github.com/SuperJJ007/CSSwitch) 将 DeepSeek 接入 Claude Science；
2. 将本地 CLIProxyAPI Codex OAuth 代理作为 OpenAI-compatible provider 接入 CSSwitch；
3. 通过异步本地任务桥，将 Codex 图像模型注册为 Claude Science 工具。

本项目不是 CSSwitch、Claude Science、Anthropic 或 OpenAI 的官方扩展，不包含这些项目的源码、二进制文件、账号凭据或 API Key。

> **版本基线（重要）**：本文档与样例在 **CSSwitch v0.3.6**（旧 Python proxy 架构）下验证。它们不能原样用于 v0.4.0 及以上版本（包括 v0.4.4）：新版 Rust gateway 会替换本项目三槽 Codex 路由所依赖的已安装代理补丁。详见[架构说明](docs/architecture.md)与[Codex 接入](docs/codex.md)。

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
docs/       三条接入教程和架构说明
examples/   不含凭据的 CSSwitch、沙箱、MCP、LaunchAgent 样例
scripts/    异步图像任务桥的沙箱端与宿主机端
```

所有配置样例均使用占位符或环境变量，可按实际部署路径替换。

## 支持范围

- 主要平台：macOS；图像桥使用用户级 LaunchAgent 示例。
- DeepSeek：使用 Anthropic-compatible endpoint。
- Codex 文本模型：已验证实现为本机 [CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI)，默认示例端口为 `127.0.0.1:8317`。
- Codex Images：实验性本地集成，通过提交任务与轮询结果规避 MCP 单次调用超时。
- Claude Science 内的多槽模型映射仅在 CSSwitch v0.3.6 的旧 Python proxy 架构下验证；它依赖已安装应用中的版本相关补丁，不能直接升级到 v0.4.0+ / v0.4.4。仓库只记录设计与验证边界，不分发应用文件或自动补丁。

## CSSwitch 0.5 与部署边界

本仓库的可复现核心仍是 DeepSeek Profile、Codex OAuth Profile 和异步图像桥。CSSwitch `0.5.x` 增加的 SSH bridge 与外部 Skill 安装器可以按需使用，但不改变这三条基础链路。

- SSH bridge 是可选项：它复用宿主机现有 SSH 配置，不应通过本文要求开启 SSH 服务、暴露端口或复制私钥。
- 第三方模型模式下，CSSwitch 的本地 Skill installer 可作为公开 GitHub Skill 的有限导入/卸载工具；它不是 Claude 官方 catalog、账号导入或 Skill 发布机制的等价替代。
- 官方账号绑定 connector、在线 catalog 与部分原生 Skill 在第三方模型模式下可能不可用或行为不同。部署说明必须明确区分「官方 Claude」与「CSSwitch 第三方 Profile」。
- 不把机器专属的 gateway 补丁、私网放行规则、搜索 API、浏览器 profile、Cookie 或 OAuth 数据写入通用部署步骤。若需要本地 MCP，优先使用 stdio，最小权限注册，并在 CSSwitch 重启 Science 后再验证。
- 每次 CSSwitch 或 Claude Science 升级后，先备份，再做一条普通对话、一次低风险工具调用和一次实际目标 connector 调用；不要仅凭 Profile 保存成功判断部署可用。

更完整的分层与升级准则见 [架构说明](docs/architecture.md)。

## 与 CSSwitch 的关系

本项目依赖 CSSwitch 提供的隔离启动和模型路由能力。CSSwitch 是独立项目，其上游仓库当前采用 MIT 许可。本项目与 CSSwitch 不存在隶属或背书关系，使用前应同时阅读 [CSSwitch README 与许可证](https://github.com/SuperJJ007/CSSwitch)。
