# 架构说明

简体中文 | [English](en/architecture.md)

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

## 可复现核心与机器专属扩展

发布部署方案时应把两类内容分开：前者可以在另一台 macOS 上按文档复现；后者依赖本机版本、账号、网络或浏览器状态，只能作为排错案例或可选设计说明。

| 分类 | 可以纳入通用部署步骤 | 应保持为本机可选项 |
| --- | --- | --- |
| 模型路由 | DeepSeek Anthropic-compatible Profile；回环地址上的 Codex OAuth proxy | Claude Science 内三槽映射；对已安装 CSSwitch 文件的补丁 |
| 工具 | 本仓库的 stdio 图像 MCP、文件任务队列和单个 watcher | 官方账号 connector 的兼容修复、搜索 API、浏览器 profile 与 Cookie |
| 网络与 SSH | CSSwitch 的隔离启动；回环监听；最小文件权限 | SSH bridge（按需启用）；任何端口暴露、私网放行或全域名 allowlist |

CSSwitch `0.5.x` 的 SSH bridge 可复用宿主机既有 SSH 配置，但不需要也不应开启 SSH 服务或暴露端口。其本地外部 Skill installer 可处理部分公开 GitHub Skill 的导入/卸载；第三方模型模式下，它不等价于 Claude 官方 catalog、账号导入或 Skill 发布流程。

## 图像任务状态

```text
submit/<job_id>.json
  → working/<job_id>.json
  → jobs/<job_id>.json
       state = running | succeeded | failed
```

文件在目录间通过原子移动领取，避免多个 watcher 同时处理同一任务。正常部署只应运行一个 watcher。

## 版本边界

- 本仓库的完整方案以 **CSSwitch v0.3.6** 为验证基线，尤其是 Codex 的 Sol / Terra / Luna 三槽映射；该实现依赖旧版应用内的 Python proxy 补丁。
- CSSwitch v0.4.0 起改用 Rust gateway。直接升级到 v0.4.4 会替换上述 Python proxy；`__CSSWITCH_CODEX_56_SLOTS__` 这类内部标记没有等价的新版映射，三槽 Codex 文本链路会失效。
- v0.4.4 会复用持久化的 Claude Science 数据目录，因此图像 MCP、桥接脚本和沙箱权限预计仍会保留；但其依赖的 Codex 文本 Profile 必须先重新配置并验证，不能据此宣称整套方案兼容。
- 单模型 Codex Profile 只依赖公开的 OpenAI-compatible 配置，维护成本较低；使用 v0.4.0+ 时应先采用这一方式并独立验证。
- 图像 MCP 与 watcher 是本项目自有代码，不是 CSSwitch 的内置能力。
- 升级前先备份；升级后必须验证普通对话、低风险工具调用和一个真实目标 connector。Profile 保存成功或 MCP 进程启动，并不能单独证明完整链路可用。
- 遇到远程 connector 失败时，先定位 endpoint、gateway 与运行时三个层次；不要以禁用 connector、放开全部 Claude 域名或允许全部私网作为通用修复。

具体操作分别见 [DeepSeek 接入](deepseek.md)、[Codex 接入](codex.md)和 [Codex Images 工具桥](images.md)。
