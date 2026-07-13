# Register Codex Images as a Claude Science Tool

[简体中文](../images.md) | English

## Goal and boundaries

This integration wraps a local Codex image endpoint as a Claude Science MCP tool. It uses the local proxy that holds the Codex OAuth session, but it is not an official Claude Science or Codex connector.

```text
Claude Science sandbox
  → stdio MCP: submit jobs and retrieve results
  → /tmp/csswitch-codex-image-jobs
  → host-side watcher
  → http://127.0.0.1:<PORT>/v1/images/generations
  → output directory
```

The sandbox-side MCP never reads the CSSwitch configuration or OAuth credentials. The host-side watcher reads the local proxy key from the selected profile when it sends a request. It does not write that key to a job file or return it through MCP.

## Why the bridge is asynchronous

Image generation can exceed the timeout of a single Claude Science MCP call. A synchronous tool may time out before the image is ready. The asynchronous bridge splits the operation into three steps:

1. `generate_image` submits a job and immediately returns a `job_id`;
2. the host watcher performs the image request independently;
3. `get_image_result(job_id)` polls the state and returns the completed image.

## Files

- [Sandbox-side MCP](../../scripts/codex_image_mcp_jobs.py)
- [Host-side watcher](../../scripts/codex_image_job_bridge.py)
- [Claude Science MCP example](../../examples/local-mcp.example.json)
- [Claude Science sandbox example](../../examples/claude-science-sandbox-config.example.toml)
- [macOS LaunchAgent example](../../examples/com.example.codex-image-job-bridge.plist)

## Configuration

The sandbox process and host process must use the same job directory:

```text
/tmp/csswitch-codex-image-jobs
```

The host watcher supports these environment variables:

| Variable | Purpose | Default |
| --- | --- | --- |
| `CODEX_IMAGE_JOB_ROOT` | Shared job directory for the sandbox and host | `/tmp/csswitch-codex-image-jobs` |
| `CSSWITCH_CONFIG_PATH` | CSSwitch configuration file | `$HOME/.csswitch/config.json` |
| `CODEX_IMAGE_PROFILE_NAME` | Codex profile used to read the proxy key | Empty; selects the first loopback profile |
| `CODEX_IMAGE_PROXY_URL` | Image endpoint | `http://127.0.0.1:8317/v1/images/generations` |
| `CODEX_IMAGE_OUTPUT_DIR` | Temporary image directory accessible to MCP | `/tmp/csswitch-codex-image-jobs/output` |

Set `CODEX_IMAGE_PROFILE_NAME` explicitly in a normal deployment so that the watcher cannot choose the wrong profile when several local profiles exist.

The default output directory is inside the sandbox-authorized shared job root. Claude Science can read it without gaining access to `$HOME/Pictures` or the entire home directory. MCP returns the image data directly as Base64. Temporary PNG files exist only for local retrieval and diagnostics and are removed during expired-job cleanup.

For long-term storage, copy selected images from the temporary directory into a separate asset library. If the host alone manages that archive, Claude Science does not need access to it. Add a narrow read-only sandbox permission only when Claude Science must read the archived path in a later task.

## Deployment

### 1. Verify the Codex text path

Complete the [Codex integration](codex.md) first and confirm that the local proxy works. The image bridge does not perform OAuth login or start the proxy.

### 2. Prepare the LaunchAgent

Copy the LaunchAgent example and replace every `<...>` placeholder:

- the absolute path to Python 3;
- the absolute path to the watcher script in this repository;
- the absolute path to the CSSwitch configuration;
- the Codex profile name;
- the log directory.

Keep the image output directory at `/tmp/csswitch-codex-image-jobs/output` unless there is a specific reason to change it.

Install the LaunchAgent under the current user's `~/Library/LaunchAgents/` directory and load it with macOS `launchctl`. When the service starts, it creates the job root and its subdirectories with `0700` permissions.

### 3. Configure the Claude Science sandbox

Add the minimum read and write permissions for the MCP script and job directory to `config.toml` in the CSSwitch-isolated Science environment. Follow the [sandbox example](../../examples/claude-science-sandbox-config.example.toml):

- make the MCP script directory read-only;
- make `/tmp/csswitch-codex-image-jobs` readable and writable;
- do not expose the CSSwitch configuration directory to the sandbox.

### 4. Register the local MCP server

Merge the [MCP example](../../examples/local-mcp.example.json) into the local MCP configuration of the isolated Science environment. Replace the Python and script placeholders with absolute paths. Restart Claude Science through CSSwitch so that the new sandbox permissions and MCP configuration are loaded.

### 5. Call the tool

An instruction in Claude Science can use this form:

```text
Use the Codex Image tool to generate a 1024×1024 PNG: <scene description>.
Keep the returned job_id and continue calling get_image_result until the image or an explicit error is returned.
```

Tool sequence:

1. `image_bridge_status`;
2. `generate_image(prompt, model)`;
3. `get_image_result(job_id)`, reusing the same `job_id` while the job is still running.

## Known limitations

- The example model allowlist contains `gpt-image-1.5` and `gpt-image-2`; the proxy must actually expose the selected model.
- The example requests PNG output at `1024×1024`.
- Job results contain image Base64. Job JSON files and temporary PNGs in the shared directory are removed after 30 minutes.
- Image usage depends on the connected Codex account and current server-side policy. A five-hour usage window cannot be converted reliably into a fixed number of images.
- The bridge has been validated only with macOS file sharing and LaunchAgent behavior.

## Troubleshooting

| Symptom | Cause and action |
| --- | --- |
| `image_bridge_status` is unavailable | The watcher is not running, the two processes use different job roots, or the sandbox has not reloaded its permissions |
| Local HTTP access is denied | The sandbox must not call `127.0.0.1` directly; only the host watcher sends the HTTP request |
| Unix socket access is denied | A restricted sandbox may block AF_UNIX `connect()`; this bridge does not use UDS |
| The call times out after `generate_image` | Use the asynchronous implementation and poll with the returned `job_id` |
| The profile cannot be found | Set `CSSWITCH_CONFIG_PATH` and `CODEX_IMAGE_PROFILE_NAME` explicitly |
| The image cannot be saved | Check the host watcher's output-directory permissions; do not broaden Claude Science sandbox access to fix a host-side write error |
