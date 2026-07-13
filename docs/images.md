# 将 Codex Images 注册为 Claude Science 工具

## 目标与边界

该方案把本机 Codex 图像 endpoint 包装为 Claude Science 的本地 MCP 工具。它使用 Codex OAuth 所在的本机代理，但不是 Claude Science 或 Codex 的官方连接器。

```text
Claude Science 沙箱
  → stdio MCP：提交任务、查询结果
  → /tmp/csswitch-codex-image-jobs
  → 宿主机 watcher
  → http://127.0.0.1:<PORT>/v1/images/generations
  → 输出目录
```

沙箱端不读取 CSSwitch 配置或 OAuth 凭据。宿主机 watcher 在发起请求时读取本地 Profile 的代理 Key，并且不会把 Key 写入任务文件或返回给 MCP。

## 为什么使用异步任务

图片生成可能超过 Claude Science 单次 MCP 调用的等待时间。同步工具容易在图像实际完成前超时。异步桥将流程拆成：

1. `generate_image` 提交任务并立即返回 `job_id`；
2. 宿主机 watcher 独立执行图像请求；
3. `get_image_result(job_id)` 轮询状态并在完成后返回图片。

## 文件说明

- [沙箱端 MCP](../scripts/codex_image_mcp_jobs.py)
- [宿主机 watcher](../scripts/codex_image_job_bridge.py)
- [Claude Science MCP 样例](../examples/local-mcp.example.json)
- [Claude Science 沙箱样例](../examples/claude-science-sandbox-config.example.toml)
- [macOS LaunchAgent 样例](../examples/com.example.codex-image-job-bridge.plist)

## 配置参数

沙箱端和宿主机端必须使用同一个任务目录：

```text
/tmp/csswitch-codex-image-jobs
```

宿主机 watcher 支持以下环境变量：

| 变量 | 用途 | 默认值 |
| --- | --- | --- |
| `CODEX_IMAGE_JOB_ROOT` | 沙箱与宿主机共享任务目录 | `/tmp/csswitch-codex-image-jobs` |
| `CSSWITCH_CONFIG_PATH` | CSSwitch 配置文件位置 | `$HOME/.csswitch/config.json` |
| `CODEX_IMAGE_PROFILE_NAME` | 读取代理 Key 的 Codex Profile 名称 | 空；匹配第一个本地回环 Profile |
| `CODEX_IMAGE_PROXY_URL` | 图像 endpoint | `http://127.0.0.1:8317/v1/images/generations` |
| `CODEX_IMAGE_OUTPUT_DIR` | MCP 可访问的临时图片目录 | `/tmp/csswitch-codex-image-jobs/output` |

正式部署时建议显式填写 `CODEX_IMAGE_PROFILE_NAME`，避免存在多个本地 Profile 时选错配置。

默认输出目录位于已授权的共享任务根目录内，因此 Claude Science 可以读取，且不需要为 `$HOME/Pictures` 或整个用户目录增加沙箱权限。MCP 会直接返回图片 Base64；临时 PNG 只用于本地留存和排错，并在任务过期清理时一并删除。

如需长期归档，可以把图片从临时目录复制到独立素材库。若仅由宿主机管理归档，Claude Science 不需要获得素材库的权限；只有需要让 Claude Science 后续直接读取该路径时，才应单独添加最小只读权限。

## 部署顺序

### 1. 确认 Codex 文本链路

先完成 [Codex 接入](codex.md)，确认本机代理可用。图像桥不负责 OAuth 登录或启动代理。

### 2. 准备 LaunchAgent

复制 LaunchAgent 样例，并替换所有 `<...>` 占位符：

- Python 3 的绝对路径；
- 仓库内 watcher 的绝对路径；
- CSSwitch 配置的绝对路径；
- Codex Profile 名称；
- 日志目录。图片输出目录建议保持为 `/tmp/csswitch-codex-image-jobs/output`。

LaunchAgent 安装到当前用户的 `~/Library/LaunchAgents/` 后，使用 macOS `launchctl` 加载。后台服务正常启动后，会自动创建权限为 `0700` 的任务目录及子目录。

### 3. 配置 Claude Science 沙箱

在 CSSwitch 隔离 Science 的 `config.toml` 中，为 MCP 脚本和任务目录增加最小读写权限。参考 [沙箱样例](../examples/claude-science-sandbox-config.example.toml)：

- MCP 脚本目录只读；
- `/tmp/csswitch-codex-image-jobs` 可读写；
- 不给沙箱开放 CSSwitch 配置目录。

### 4. 注册本地 MCP

将 [MCP 样例](../examples/local-mcp.example.json) 合并到隔离 Science 的本地 MCP 配置，替换 Python 与脚本绝对路径。随后从 CSSwitch 重新启动 Claude Science，使沙箱权限和 MCP 配置生效。

### 5. 调用

Claude Science 中可以使用类似指令：

```text
使用 Codex Image 工具生成一张 1024×1024 PNG：<画面描述>。
提交任务后保留 job_id，并持续调用 get_image_result，直到返回图片或明确错误。
```

工具调用顺序：

1. `image_bridge_status`；
2. `generate_image(prompt, model)`；
3. `get_image_result(job_id)`，未完成时使用同一 `job_id` 再次查询。

## 已知限制

- 示例模型白名单为 `gpt-image-1.5` 与 `gpt-image-2`；代理端必须实际提供对应模型。
- 示例固定请求 PNG、`1024×1024`。
- 任务结果包含图片 Base64；任务 JSON 与共享目录中的临时 PNG 在 30 分钟后由 watcher 清理。
- 图像用量由所连接的 Codex 账户和服务端策略决定，不能从五小时窗口可靠换算出固定图片张数。
- 该方案仅针对 macOS 文件共享与 LaunchAgent 进行验证。

## 常见故障

| 现象 | 原因与处理 |
| --- | --- |
| `image_bridge_status` 不可用 | watcher 未启动、任务目录不一致，或沙箱未重新加载权限 |
| 本地 HTTP 被拒绝 | 不应让沙箱直接请求 `127.0.0.1`；请求必须由宿主机 watcher 发起 |
| Unix socket 被拒绝 | 受限沙箱可能禁止 AF_UNIX `connect()`；本方案不使用 UDS |
| `generate_image` 后超时 | 应使用异步版本，并用返回的 `job_id` 轮询 |
| 找不到 Profile | 显式设置 `CSSWITCH_CONFIG_PATH` 与 `CODEX_IMAGE_PROFILE_NAME` |
| 图片写入失败 | 检查 watcher 对输出目录的权限；不要扩大 Claude Science 沙箱权限来解决宿主机写入问题 |
