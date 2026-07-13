# 将 DeepSeek 接入 Claude Science

## 适用场景

DeepSeek 提供 Anthropic-compatible endpoint，可由 CSSwitch 作为原生 Anthropic 格式 provider 接入 Claude Science。该路径不需要额外协议桥，适合作为日常文本、代码与工具调用模型。

## 前置条件

- macOS Apple Silicon；
- 已安装 Claude Science；
- 已安装 CSSwitch；
- 一个有效的 DeepSeek API Key。

## CSSwitch 配置

在 CSSwitch 中新建 Profile，并选择内置的 DeepSeek provider。核心参数如下：

| 字段 | 值 |
| --- | --- |
| Profile 名称 | `DeepSeek`，或其他便于识别的名称 |
| API 格式 | Anthropic-compatible |
| Base URL | `https://api.deepseek.com/anthropic` |
| API Key | DeepSeek 控制台创建的 Key |
| Model | DeepSeek 账户当前可用的模型 ID |

模型 ID 不应从本文硬编码复制，应以 DeepSeek 账户和 CSSwitch 当时显示的可用模型为准。若同一账户提供速度优先与能力优先的模型，可分别保存为两个 Profile。

## 启动与切换

1. 在 CSSwitch 中将 DeepSeek Profile 设为当前配置。
2. 确认 Profile 验证通过。
3. 点击 CSSwitch 的「一键开始」。
4. 在启动的 Claude Science 中创建一条短对话，确认文本回复与工具调用正常。

切换到其他 provider 时，应先回到 CSSwitch 切换 Profile，再由 CSSwitch 重新启动对应的 Claude Science 会话。直接打开 Claude Science 不会应用 DeepSeek Profile。

## 模型显示名

Claude Science 内部仍使用 Claude 风格的模型槽位。CSSwitch 可以将槽位显示为真实模型名或将请求映射到 Profile 指定的 DeepSeek 模型。因此，界面中的槽位名称不是判断上游 provider 的唯一依据；实际 provider 由 CSSwitch 当前 Profile 决定。

## 最小排查

| 现象 | 检查项 |
| --- | --- |
| 启动后仍要求官方 Claude 登录 | 是否直接启动了 Claude Science，而不是从 CSSwitch 一键开始 |
| Profile 验证失败 | Base URL 是否以 `/anthropic` 结尾；API Key 是否有效 |
| 模型不存在 | 模型 ID 是否属于当前 DeepSeek 账户和区域 |
| 工具调用异常 | 先用短对话验证；再检查 CSSwitch 日志中的脱敏错误信息 |

提交日志前必须移除 API Key、邮箱、私有 URL、对话内容和本机路径。
