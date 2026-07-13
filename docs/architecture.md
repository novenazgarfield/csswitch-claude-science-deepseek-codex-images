# 架构说明

## 三个独立层次

本项目处理三个相关但彼此独立的问题：

| 层次 | 解决的问题 | 核心组件 |
| --- | --- | --- |
| DeepSeek 接入 | 让 Claude Science 的文本推理走 DeepSeek | CSSwitch 内置 DeepSeek Profile |
| Codex 接入 | 让 Claude Science 的文本推理走 Codex OAuth | 本机 CLIProxyAPI + CSSwitch 自定义 OpenAI Profile |
| Codex Images | 让 Claude Science 把图像生成作为工具调用 | stdio MCP + 文件任务队列 + 宿主机 watcher |

DeepSeek 不依赖 Codex 代理；Codex 文本模型不依赖图像桥；图像桥则要求 Codex OAuth 代理已经正常工作。

## CSSwitch 的职责

CSSwitch 负责：

- 在隔离环境中启动 Claude Science；
- 保存和切换第三方 provider Profile；
- 将 Claude Science 的 Anthropic 请求透传或转换到所选 provider；
- 让第三方模型模式与官方 Claude Science 环境保持隔离。

正确入口为：

```text
选择 CSSwitch Profile → 设为当前 → CSSwitch 一键开始 → Claude Science
```

直接启动 Claude Science 会进入官方链路，不会自动使用 CSSwitch 当前 Profile。

## 凭据边界

```text
DeepSeek API Key
  └─ CSSwitch 本机配置

Codex OAuth token
  └─ 本机 CLIProxyAPI 自己的认证存储

本地代理访问 Key
  ├─ CSSwitch Codex Profile
  └─ 宿主机图像 watcher 按需读取

Claude Science 沙箱
  └─ 不读取以上任何配置或 token
```

图像任务文件只包含任务 ID、提示词、模型名、状态和生成结果。任务目录权限应为 `0700`，结果应定期清理。

## 图像任务状态

```text
submit/<job_id>.json
  → working/<job_id>.json
  → jobs/<job_id>.json
       state = running | succeeded | failed
```

文件在目录间通过原子移动领取，避免多个 watcher 同时处理同一任务。正常部署只应运行一个 watcher。

## 版本边界

- CSSwitch 的 Profile、目录结构和内部 gateway 可能随版本变化；部署时应以当前上游文档为准。
- 单模型 Codex Profile 只依赖公开的 OpenAI-compatible 配置，维护成本较低。
- Claude Science 三槽切换依赖额外模型映射能力，属于版本相关扩展；升级 CSSwitch 后必须重新验证。
- 图像 MCP 与 watcher 是本项目自有代码，不是 CSSwitch 的内置能力。

具体操作分别见 [DeepSeek 接入](deepseek.md)、[Codex 接入](codex.md)和 [Codex Images 工具桥](images.md)。
