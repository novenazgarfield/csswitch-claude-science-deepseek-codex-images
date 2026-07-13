# Architecture

[简体中文](../architecture.md) | English

## Three independent layers

This project addresses three related but independent integration problems:

| Layer | Goal | Core components |
| --- | --- | --- |
| DeepSeek integration | Route Claude Science text inference to DeepSeek | CSSwitch built-in DeepSeek profile |
| Codex integration | Route Claude Science text inference through Codex OAuth | Local CLIProxyAPI + CSSwitch custom OpenAI profile |
| Codex Images | Expose image generation as a Claude Science tool | stdio MCP + file job queue + host watcher |

DeepSeek does not depend on the Codex proxy. Codex text models do not depend on the image bridge. The image bridge does require a working Codex OAuth proxy.

## CSSwitch responsibilities

CSSwitch is responsible for:

- launching Claude Science in an isolated environment;
- storing and switching third-party provider profiles;
- forwarding or converting Claude Science Anthropic requests to the selected provider;
- keeping third-party model mode separate from the official Claude Science environment.

The expected launch path is:

```text
Select CSSwitch profile → set active → CSSwitch one-click start → Claude Science
```

Launching Claude Science directly follows the official service path and does not automatically use the active CSSwitch profile.

## Credential boundaries

```text
DeepSeek API key
  └─ local CSSwitch configuration

Codex OAuth token
  └─ local CLIProxyAPI authentication storage

Local proxy access key
  ├─ CSSwitch Codex profile
  └─ read on demand by the host image watcher

Claude Science sandbox
  └─ cannot read any of the configuration or token stores above
```

Image job files contain only a job ID, prompt, model name, state, and generated result. The job directory should use `0700` permissions, and expired results should be removed regularly.

## Image job states

```text
submit/<job_id>.json
  → working/<job_id>.json
  → jobs/<job_id>.json
       state = running | succeeded | failed
```

A watcher claims work by atomically moving each file between directories. This prevents two watcher processes from handling the same job. A normal deployment should run exactly one watcher.

## Version boundaries

- CSSwitch profile fields, directory layout, and internal gateway can change between versions. Use the current upstream documentation when deploying.
- A single-model Codex profile relies only on public OpenAI-compatible configuration and has a lower maintenance cost.
- Switching three Codex models through Claude Science slots requires an additional mapping layer and is version-dependent. Revalidate it after every CSSwitch upgrade.
- The image MCP and host watcher belong to this project and are not built-in CSSwitch components.

See [DeepSeek integration](deepseek.md), [Codex integration](codex.md), and the [Codex Images tool bridge](images.md) for setup instructions.
