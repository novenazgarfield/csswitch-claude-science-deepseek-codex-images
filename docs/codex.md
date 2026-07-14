# 将 Codex OAuth 文本模型接入 Claude Science

简体中文 | [English](en/codex.md)

## 方案概览

Claude Science 不直接读取 Codex OAuth。接入分为两层：

```text
Codex OAuth
  → 本机 OpenAI-compatible 代理
  → CSSwitch Codex Profile
  → Claude Science
```

本项目已验证的代理实现是 [CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI)。在已验证环境中，它由 CSSwitch 配置为用户级本地服务，完成 Codex OAuth 登录后监听：

```text
http://127.0.0.1:8317/v1
```

文本模型通过该 OpenAI-compatible root 接入 CSSwitch，图像请求使用：

```text
http://127.0.0.1:8317/v1/images/generations
```

端口 `8317` 是本项目的已验证配置，不是 CLIProxyAPI 的通用强制值。其他部署可改用自己的回环端口，并同步修改 CSSwitch Profile 与图像 watcher。CLIProxyAPI 的安装、OAuth 登录和更新应以其上游文档为准。

## 前置条件

- CSSwitch 已能正常启动隔离的 Claude Science；
- CLIProxyAPI 或等价的本机 Codex OAuth 代理处于运行状态；
- 代理提供本地 Base URL、访问该本地代理所需的 Key，以及 `/v1/models` 或兼容模型列表；
- 代理没有监听 `0.0.0.0` 或对局域网开放。

这里所说的本地代理 Key 只用于访问本机代理，不等同于 Codex OAuth token。OAuth token 不应复制到 CSSwitch Profile 或仓库文件中。

## CSSwitch Profile

在 CSSwitch `0.5.0` 桌面面板中创建自定义 OpenAI-compatible Profile。若代理支持 Responses API，优先选择 CSSwitch 的 Custom OpenAI Responses；否则按代理实际实现选择 OpenAI Chat Completions。不要直接编辑 `~/.csswitch/config.json`：0.5 保存的 Profile 还会带上模板、分类、ID 和排序等元数据。

示例：

| 字段 | 示例 |
| --- | --- |
| 模板 / API 格式 | `custom-openai-responses` / `openai_responses` |
| Profile 名称 | `Codex (ChatGPT OAuth)` |
| Base URL | `http://127.0.0.1:8317/v1`，或实际使用的回环端口 |
| API Key | 本地代理生成的访问 Key |
| Model | 本地代理列出的 Codex 模型 ID |

可参考 [脱敏 Profile 字段参考](../examples/csswitch-profile.example.json)。它不是可导入的完整 `config.json`；应在 0.5 面板中填写并保存，示例中的占位符不能直接用于运行。

## 单模型模式

最容易复现的方式是每个 CSSwitch Profile 固定一个 Codex 模型：

```text
Codex - Model A
Codex - Model B
Codex - Model C
```

切换模型时在 CSSwitch 中切换 Profile，然后再次使用「一键开始」。这种方式不需要修改 CSSwitch 的内部模型路由，版本兼容性最好。

## 本机 0.5 部署中的 Claude Science 三槽切换

这台机器已验证的 CSSwitch `0.5.0` 部署会在 Codex Responses Profile 使用内部标记 `__CSSWITCH_CODEX_56_SLOTS__`，由本机兼容路由把 Claude Science 的 canonical slot 映射到实际 Codex 模型 ID。它不要求把 `model_slot_mapping` 之类的字段写入 Profile。

已验证过的映射示例：

| Claude Science 槽位 | 显示名 | 实际模型 ID |
| --- | --- | --- |
| Opus | GPT-5.6 Sol | `gpt-5.6-sol` |
| Sonnet | GPT-5.6 Terra | `gpt-5.6-terra` |
| Haiku | GPT-5.6 Luna | `gpt-5.6-luna` |

该映射只应对该 Codex Profile 生效，不能影响 DeepSeek 或官方 Claude Profile。当前校验过的行为是：

```text
claude-opus-4-8   → GPT-5.6 Sol   → gpt-5.6-sol
claude-sonnet-5   → GPT-5.6 Terra → gpt-5.6-terra
claude-haiku-4-5  → GPT-5.6 Luna  → gpt-5.6-luna
```

这不是 CSSwitch 0.5 桌面 UI 中公开、可任意配置的槽位映射功能。本机网关因其他兼容性修复而处于修改状态，且该标记依赖本机兼容资源；因此它属于机器专属扩展。仓库不分发 App 补丁或自动修改脚本。另一台机器应先使用单模型 Profile；只有在其 0.5 安装明确具备相同兼容路由、且先完成备份后，才可采用这一映射。

## 验证

1. 在 CSSwitch 中启用 Codex Profile。
2. 使用「一键开始」启动 Claude Science。
3. 先进行一条不调用工具的短对话。
4. 再测试文件读取或其他低风险工具。
5. 使用三槽映射时，分别切换三个槽位并从本地代理日志或用量信息确认实际模型 ID。

界面显示名只能证明 catalog 映射生效，不能单独证明上游实际模型；最终验证应以代理收到的实际请求为准。
