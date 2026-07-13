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

## Version baseline

The complete integration in this document, including Sol / Terra / Luna three-slot switching, was verified with **CSSwitch v0.3.6** and its legacy Python proxy. CSSwitch moved to a Rust gateway in v0.4.0; upgrading to v0.4.4 replaces the installed Python-proxy patch used for slot mapping and does not recognize this setup's internal slot marker. Do not carry an existing three-slot configuration directly to v0.4.0+.

For v0.4.0+, first use an explicit single Codex model ID in the profile and revalidate the text path yourself. Three-slot routing needs an equivalent Rust-gateway mapping before it can be restored.

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

Create a custom OpenAI-compatible profile in CSSwitch. If the proxy supports the Responses API, prefer CSSwitch's Custom OpenAI Responses provider. Otherwise select OpenAI Chat Completions according to the proxy implementation.

Example values:

| Field | Example |
| --- | --- |
| Profile name | `Codex (ChatGPT OAuth)` |
| Base URL | `http://127.0.0.1:8317/v1`, or the actual loopback port |
| API key | The access key generated for the local proxy |
| Model | A Codex model ID listed by the local proxy |

See the [redacted profile example](../../examples/csswitch-profile.example.json). Placeholders in that file are not runnable values.

## Single-model profiles

The most portable setup assigns one Codex model to each CSSwitch profile:

```text
Codex - Model A
Codex - Model B
Codex - Model C
```

Switch models by activating a different CSSwitch profile and using one-click start again. This approach does not modify CSSwitch's internal model router and is the least sensitive to CSSwitch upgrades.

## Switching three models inside Claude Science

Switching three Codex models directly from the Opus, Sonnet, and Haiku selector in Claude Science requires the CSSwitch routing layer to map each canonical Claude slot to an actual model ID.

Verified example mapping:

| Claude Science slot | Display name | Actual model ID |
| --- | --- | --- |
| Opus | GPT-5.6 Sol | `gpt-5.6-sol` |
| Sonnet | GPT-5.6 Terra | `gpt-5.6-terra` |
| Haiku | GPT-5.6 Luna | `gpt-5.6-luna` |

The mapping must apply only to the Codex profile. It must not affect DeepSeek or the official Claude profile. A generic configuration shape would be:

```json
{
  "model_slot_mapping": {
    "opus":   { "display": "GPT-5.6 Sol",   "model": "gpt-5.6-sol" },
    "sonnet": { "display": "GPT-5.6 Terra", "model": "gpt-5.6-terra" },
    "haiku":  { "display": "GPT-5.6 Luna",  "model": "gpt-5.6-luna" }
  }
}
```

This mapping was verified as a version-specific patch to the installed Python proxy in CSSwitch v0.3.6; it is not a portable CSSwitch configuration field. CSSwitch v0.4.0+ (including v0.4.4) uses a Rust gateway and cannot reuse that patch or its internal slot marker. This repository documents the mapping design and validation boundary without distributing application files or an automatic patcher. Prefer an upstream profile-level slot-mapping feature if one becomes available.

## Verification

1. Activate the Codex profile in CSSwitch.
2. Launch Claude Science through one-click start.
3. Run a short conversation without tools.
4. Test a low-risk tool such as file reading.
5. For three-slot routing, select each slot and verify the actual model ID from the local proxy log or usage data.

A display label only proves that catalog mapping is visible. It does not prove which upstream model handled the request. Final verification must use the model ID received by the proxy.
