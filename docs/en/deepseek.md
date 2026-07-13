# Connect DeepSeek to Claude Science

[简体中文](../deepseek.md) | English

## When to use this setup

DeepSeek provides an Anthropic-compatible endpoint that CSSwitch can expose to Claude Science as a native Anthropic-format provider. This path does not require an extra protocol bridge and is suitable for everyday text, coding, and tool-use workloads.

## Prerequisites

- a macOS Apple Silicon system;
- Claude Science installed;
- CSSwitch installed;
- a valid DeepSeek API key.

## CSSwitch configuration

Create a profile in CSSwitch and select its built-in DeepSeek provider. The essential fields are:

| Field | Value |
| --- | --- |
| Profile name | `DeepSeek`, or another descriptive name |
| API format | Anthropic-compatible |
| Base URL | `https://api.deepseek.com/anthropic` |
| API key | A key created in the DeepSeek console |
| Model | A model ID currently available to the DeepSeek account |

Do not copy a model ID from this guide as a permanent value. Use a model that is currently available to the relevant DeepSeek account and CSSwitch version. If the account provides separate speed-oriented and capability-oriented models, store them as separate profiles.

## Launching and switching

1. Set the DeepSeek profile as the active profile in CSSwitch.
2. Confirm that profile validation succeeds.
3. Use CSSwitch's one-click start action.
4. Start a short conversation in the launched Claude Science environment and verify both text output and tool use.

To switch providers, return to CSSwitch, activate another profile, and restart the corresponding Claude Science session through CSSwitch. Launching Claude Science directly does not apply the DeepSeek profile.

## Model names in Claude Science

Claude Science internally uses Claude-style model slots. CSSwitch may display the real provider model name for a slot or route a slot to the model selected by the profile. The slot label alone is therefore not sufficient to identify the upstream provider; the active CSSwitch profile determines the actual provider.

## Minimal troubleshooting

| Symptom | Check |
| --- | --- |
| Claude Science still asks for an official Claude login | Confirm that Claude Science was launched through CSSwitch rather than directly |
| Profile validation fails | Confirm that the Base URL ends in `/anthropic` and that the API key is valid |
| Model not found | Confirm that the model ID is available to the current DeepSeek account and region |
| Tool calls fail | Start with a short conversation, then inspect a redacted CSSwitch error log |

Remove API keys, email addresses, private URLs, conversation content, and local paths before sharing logs.
