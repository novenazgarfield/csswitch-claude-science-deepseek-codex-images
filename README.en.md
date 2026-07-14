# CSSwitch × Claude Science: DeepSeek, Codex, and Codex Images Integration Guide

[简体中文](README.md) | English

This repository documents a community integration for macOS with three goals:

1. connect DeepSeek to Claude Science through [CSSwitch](https://github.com/SuperJJ007/CSSwitch);
2. expose a local CLIProxyAPI Codex OAuth proxy to CSSwitch as an OpenAI-compatible provider;
3. register Codex image models as Claude Science tools through an asynchronous local bridge.

This project is not an official extension of CSSwitch, Claude Science, Anthropic, or OpenAI. It does not include source code or binaries from those projects, account credentials, or API keys.

## Documentation

| Goal | Guide |
| --- | --- |
| Configure DeepSeek | [DeepSeek integration](docs/en/deepseek.md) |
| Configure Codex OAuth text models | [Codex integration](docs/en/codex.md) |
| Add Codex Images to Claude Science | [Codex Images tool bridge](docs/en/images.md) |
| Understand the architecture and sandbox boundaries | [Architecture](docs/en/architecture.md) |

## End-to-end architecture

```text
Claude Science (launched by CSSwitch)
  │
  ├─ DeepSeek profile
  │    └─ DeepSeek Anthropic-compatible API
  │
  └─ Codex profile
       └─ Local CLIProxyAPI (OpenAI-compatible)
            └─ Codex OAuth

Claude Science Codex Image tool
  └─ stdio MCP → file job queue → host watcher
       └─ local Codex proxy → image model
```

CSSwitch is the entry point for Claude Science. After selecting a profile, launch the isolated Claude Science environment with CSSwitch's one-click start action. Launching Claude Science directly follows the official service path and does not apply the currently selected third-party CSSwitch profile.

## Repository layout

```text
docs/       Three integration guides and architecture documentation
examples/   Credential-free CSSwitch, sandbox, MCP, and LaunchAgent examples
scripts/    Sandbox-side and host-side components of the asynchronous image bridge
```

All configuration examples use placeholders or environment variables and must be adjusted for the target installation.

## Scope

- Primary platform: macOS. The image bridge uses a per-user LaunchAgent example.
- DeepSeek: connected through its Anthropic-compatible endpoint.
- Codex text models: the verified implementation uses local [CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI) on the example address `127.0.0.1:8317`.
- Codex Images: an experimental local integration that uses job submission and result polling to avoid one-shot MCP timeouts.
- Multi-slot model routing inside Claude Science is version-dependent. This repository documents the design and a verified mapping, but does not modify or redistribute CSSwitch application files.

## CSSwitch 0.5 and deployment boundaries

The reproducible core of this repository remains the DeepSeek profile, the Codex OAuth profile, and the asynchronous image bridge. The SSH bridge and external Skill installer added in CSSwitch `0.5.x` are optional and do not change those three base paths.

- The SSH bridge reuses existing host SSH configuration. It must not be presented as a reason to start an SSH service, expose ports, or copy private keys.
- In third-party model mode, the CSSwitch local Skill installer is a limited public-GitHub-Skill import/removal path. It is not equivalent to the official Claude catalog, account import, or Skill publishing workflow.
- Official-account connectors, online catalog features, and some native Skills can be unavailable or behave differently in third-party model mode. Documentation should distinguish official Claude from a CSSwitch third-party profile.
- Do not put machine-specific gateway patches, private-network allow rules, search API credentials, browser profiles, cookies, or OAuth state into general deployment instructions. When a local MCP is needed, prefer stdio, register it with least privilege, restart Science from CSSwitch, and then verify it.
- After every CSSwitch or Claude Science upgrade, back up first, then test one ordinary conversation, one low-risk tool call, and one real target connector call. Saving a profile alone is not a deployment test.

See the [architecture guide](docs/en/architecture.md) for the detailed layering and upgrade rules.

## Relationship to CSSwitch

This project depends on CSSwitch for isolated startup and model routing. CSSwitch is an independent project and its upstream repository currently uses the MIT License. This project is not affiliated with or endorsed by CSSwitch. Read the upstream [CSSwitch README and license](https://github.com/SuperJJ007/CSSwitch) before use.
