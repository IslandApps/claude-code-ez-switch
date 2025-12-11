<div align="center">
  <img src="https://raw.githubusercontent.com/techcow2/claude-code-ez-switch/refs/heads/master/screenshot/ccez.png" alt="Claude Code EZ Switch">
</div>

<br>

A simple GUI application for managing Claude Code API configurations - easily switch between Claude subscription, Z.ai API, and custom endpoints.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [Model Selection Guide](#model-selection-guide)
- [How It Works](#how-it-works)
- [License](#license)

## Installation

### Option 1: Windows Executable (Recommended)
1. Download the latest `.exe` from the [Releases page](https://github.com/techcow2/claude-code-ez-switch/releases)
2. Run the executable - no installation required!

### Option 2: Python Source
```bash
git clone https://github.com/techcow2/claude-code-ez-switch.git
cd claude-code-ez-switch
python ezswitch.py
```

## Usage

1. Launch the application
2. Select **Z.ai**, **Claude Subscription**, or **Custom**
3. Enter your API key and base URL (if applicable)
4. For Z.ai users: Choose your preferred GLM models (GLM-4.6, GLM-4.5, GLM-4.5-Air) for each tier
5. Click **Apply Configuration**
6. **Just restart Claude Code** - no terminal restart needed!

### Pro Tips
- Use the **"Show Claude Settings"** checkbox to see your current configuration
- Check **"Show API Keys"** to view sensitive values in the settings display
- Mix and match GLM models based on your needs (see guide below)
- Settings are applied instantly to `~/.claude/settings.json`

## Features

- **Easy GUI Interface**: No command line required
- **One-Click Switching**: Toggle between Z.ai, Claude subscription, and custom APIs
- **Advanced Model Selection**: Choose specific GLM models for each Claude tier
- **Secure Local Storage**: API keys saved locally in `~/.claude_ez_switch/`
- **Real-time Status**: Visual feedback for configuration changes
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Settings-Only**: Modifies only Claude Code settings.json, never system environment

## Model Selection Guide

When using Z.ai, you can choose from three GLM models:

- **GLM-4.6**: Most capable, best for complex reasoning and coding tasks
- **GLM-4.5**: Balanced performance, good for everyday tasks
- **GLM-4.5-Air**: Fastest response time, ideal for quick queries

**Strategy**: Use GLM-4.6 for Opus (complex tasks), GLM-4.5 for Sonnet (general use), and GLM-4.5-Air for Haiku (quick responses).

## How It Works

The app only modifies `~/.claude/settings.json` - no system environment variables or shell files are touched.

### Z.ai Mode
Configures:
- `ANTHROPIC_AUTH_TOKEN`: Your Z.ai API key
- `ANTHROPIC_BASE_URL`: `https://api.z.ai/api/anthropic`
- `ANTHROPIC_DEFAULT_OPUS_MODEL`: Your selected GLM model for Opus
- `ANTHROPIC_DEFAULT_SONNET_MODEL`: Your selected GLM model for Sonnet
- `ANTHROPIC_DEFAULT_HAIKU_MODEL`: Your selected GLM model for Haiku
- `API_TIMEOUT_MS`: `3000000` (50-minute timeout)

### Claude Mode
Clears all custom settings to use your default Claude subscription.

### Custom Mode
Configures any API endpoint with your custom base URL and auth token.

## License

MIT
