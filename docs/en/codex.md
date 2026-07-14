# Connect Codex OAuth Text Models to Claude Science

[简体中文](../codex.md) | English

## Overview

Claude Science does not read Codex OAuth credentials directly. The integration has two routing layers:

```text
Codex OAuth
  → local OpenAI-compatible proxy
  → CSSwitch Codex profile
  → Claude Science
```

The verified proxy implementation for this repository is [CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI). In the tested setup, CSSwitch manages it as a per-user local service. After Codex OAuth authentication, it listens on:

```text
http://127.0.0.1:8317/v1
```

Text models use that OpenAI-compatible root. Image requests use:

```text
http://127.0.0.1:8317/v1/images/generations
```

Port `8317` is the verified value for this setup, not a mandatory CLIProxyAPI default. Another loopback port can be used if the CSSwitch profile and the image watcher are updated together. Follow the upstream CLIProxyAPI documentation for installation, OAuth authentication, and upgrades.

## Prerequisites

- CSSwitch can launch an isolated Claude Science environment successfully;
- CLIProxyAPI, or an equivalent local Codex OAuth proxy, is running;
- the proxy provides a local Base URL, a key for local proxy access, and `/v1/models` or an equivalent model list;
- the proxy listens only on a loopback address and is not exposed through `0.0.0.0` or the local network.

The local proxy access key is not the Codex OAuth token. Do not copy the OAuth token into a CSSwitch profile or repository file.

## CSSwitch profile

Create a custom OpenAI-compatible profile in the CSSwitch `0.5.0` desktop panel. If the proxy supports the Responses API, prefer CSSwitch's Custom OpenAI Responses provider. Otherwise select OpenAI Chat Completions according to the proxy implementation. Do not edit `~/.csswitch/config.json` directly: a 0.5 saved profile also carries template, category, ID, and ordering metadata.

Example values:

| Field | Example |
| --- | --- |
| Template / API format | `custom-openai-responses` / `openai_responses` |
| Profile name | `Codex (ChatGPT OAuth)` |
| Base URL | `http://127.0.0.1:8317/v1`, or the actual loopback port |
| API key | The access key generated for the local proxy |
| Model | A Codex model ID listed by the local proxy |

See the [redacted profile field reference](../../examples/csswitch-profile.example.json). It is not an importable `config.json`: fill the values in the 0.5 panel and save them there. Its placeholders are not runnable values.

## Single-model profiles

The most portable setup assigns one Codex model to each CSSwitch profile:

```text
Codex - Model A
Codex - Model B
Codex - Model C
```

Switch models by activating a different CSSwitch profile and using one-click start again. This approach does not modify CSSwitch's internal model router and is the least sensitive to CSSwitch upgrades.

## Three-model switching in this local 0.5 deployment

In this machine's verified CSSwitch `0.5.0` deployment, the Codex Responses profile uses the internal `__CSSWITCH_CODEX_56_SLOTS__` marker. A local compatibility route maps the canonical Claude Science slots to the actual Codex model IDs. It does not require adding a `model_slot_mapping`-style field to the profile.

Verified example mapping:

| Claude Science slot | Display name | Actual model ID |
| --- | --- | --- |
| Opus | GPT-5.6 Sol | `gpt-5.6-sol` |
| Sonnet | GPT-5.6 Terra | `gpt-5.6-terra` |
| Haiku | GPT-5.6 Luna | `gpt-5.6-luna` |

The mapping must apply only to the Codex profile. It must not affect DeepSeek or the official Claude profile. The currently verified behavior is:

```text
claude-opus-4-8   → GPT-5.6 Sol   → gpt-5.6-sol
claude-sonnet-5   → GPT-5.6 Terra → gpt-5.6-terra
claude-haiku-4-5  → GPT-5.6 Luna  → gpt-5.6-luna
```

This is not a public, freely configurable slot-mapping feature in the CSSwitch 0.5 desktop UI. The local gateway is modified for other compatibility fixes, and this marker depends on local compatibility resources, so it is host-specific. This repository does not distribute an application patch or automatic patcher. On another machine, start with single-model profiles; use this mapping only after a backup and only when that 0.5 installation is known to include the same compatible route.

## Verification

1. Activate the Codex profile in CSSwitch.
2. Launch Claude Science through one-click start.
3. Run a short conversation without tools.
4. Test a low-risk tool such as file reading.
5. For three-slot routing, select each slot and verify the actual model ID from the local proxy log or usage data.

A display label only proves that catalog mapping is visible. It does not prove which upstream model handled the request. Final verification must use the model ID received by the proxy.
