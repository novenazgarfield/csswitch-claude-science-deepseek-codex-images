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

The Codex text routing in this guide was rechecked with **CSSwitch v0.6.0**. v0.6 uses the Rust gateway and no longer depends on the legacy Python proxy.

Three-slot switching has two explicit boundaries:

- **Stock CSSwitch v0.6:** use one explicit Codex model ID. This is the most portable option.
- **Customized v0.6 Rust gateway:** map Claude's three fixed menu slots to Sol / Terra / Luna. This repository records the verified mapping and its safety boundary, but does not distribute a modified app, binary, or automatic patcher.

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

In the verified customized v0.6 gateway, the Codex Profile uses the internal marker `__CSSWITCH_CODEX_56_SLOTS__` instead of a fixed model ID. The gateway returns the three display slots to Claude Science and rewrites requests to the corresponding Codex model IDs; unknown or legacy menu IDs safely fall back to Terra.

Use this marker only with a custom build that contains the corresponding Rust-gateway change. Putting it in a stock CSSwitch v0.6 Profile does not enable three-slot routing. Never commit a real proxy key, OAuth token, complete proxy configuration, user path, organization ID, or proxy log; retain only placeholders, loopback addresses, and model IDs. Prefer an upstream Profile-level slot-mapping feature if one becomes available.

## Verification

1. Activate the Codex profile in CSSwitch.
2. Launch Claude Science through one-click start.
3. Run a short conversation without tools.
4. Test a low-risk tool such as file reading.
5. For three-slot routing, select each slot and verify the actual model ID from the local proxy log or usage data.

A display label only proves that catalog mapping is visible. It does not prove which upstream model handled the request. Final verification must use the model ID received by the proxy.
