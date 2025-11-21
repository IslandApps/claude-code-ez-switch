# Claude Code EZ Switch

A simple GUI application for managing Claude Code API configurations - easily switch between Claude subscription, Z.ai API, and custom endpoints.

## New Feature: Advanced Model Selection for Z.ai

Now you can choose specific GLM models for each Claude tier when using Z.ai:
- **GLM-4.6**: Most capable, best for complex reasoning and coding tasks
- **GLM-4.5**: Balanced performance, good for most everyday tasks
- **GLM-4.5-Air**: Fastest response time, ideal for quick queries and simple tasks

Mix and match models based on your needs - use GLM-4.6 for Opus (complex tasks) and GLM-4.5-Air for Haiku (quick responses)!

## Screenshot

<img src="https://raw.githubusercontent.com/techcow2/claude-code-ez-switch/refs/heads/master/screenshot/screenshot.png" alt="Claude Code EZ Switch Screenshot" width="450">

## Recent Updates

### Windows Dependency Fix (11/20/25)
Fixed a critical error that was preventing the app from opening on Windows due to an unnecessary dependency that was present. The application now launches properly on all Windows systems.

---

## Important Update - Settings.json Only

**Claude Code EZ Switch now works completely differently!**

The app no longer modifies your system environment variables or shell configuration files. Instead, it only updates Claude Code's internal settings file (`~/.claude/settings.json`).

### Benefits of This Change:
- **No System Pollution**: Your terminal and other applications are unaffected
- **Faster Switching**: No need to restart terminals or source shell files
- **Cleaner Operation**: Only affects Claude Code, nothing else
- **Better Security**: Configuration is isolated to Claude Code only

### What Changed:
- **Before**: Modified system environment variables and shell files (.bashrc, .zshrc, etc.)
- **Now**: Only updates `~/.claude/settings.json`

### Current Usage:
1. Apply configuration in the app
2. **Just restart Claude Code** (VS Code extension or CLI)
3. No terminal restart or shell sourcing needed!

---

## Features
- **Easy GUI Interface**: No command line required
- **One-Click Switching**: Toggle between Z.ai, Claude subscription, and custom APIs
- **Advanced Model Selection**: Choose specific GLM models for each Claude tier (Opus, Sonnet, Haiku)
- **Secure Local Storage**: API keys saved locally in `~/.claude_ez_switch/`
- **Real-time Status**: Visual feedback for configuration changes
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Settings-Only**: Modifies only Claude Code settings.json, never system environment

## Requirements
- Python 3.7+
- Windows, Linux, or macOS
- Claude Code CLI

## Platform Support
- **Windows**: Full support
- **Linux**: Full support
- **macOS**: Full support

## Quick Start
```bash
git clone https://github.com/techcow2/claude-code-ez-switch.git
cd claude-code-ez-switch
python ezswitch.py
```

## Usage
1. Launch the app with `python ezswitch.py`
2. Select **Z.ai**, **Claude Subscription**, or **Custom**
3. Enter your API key and base URL (if applicable)
4. **For Z.ai users**: Choose your preferred GLM models for each tier (Opus, Sonnet, Haiku)
5. Click **Apply Configuration**
6. **Just restart Claude Code** - no terminal restart needed!

### Pro Tips:
- Use the **"Show Claude Settings"** checkbox to see your current configuration
- Check **"Show API Keys"** to view sensitive values in the settings display
- **Model Selection**: Mix and match GLM models based on your needs - use GLM-4.6 for complex tasks, GLM-4.5-Air for faster responses
- Settings are applied instantly to `~/.claude/settings.json`

### Model Selection Guide:
- **GLM-4.6**: Most capable, best for complex reasoning and coding tasks
- **GLM-4.5**: Balanced performance, good for most everyday tasks
- **GLM-4.5-Air**: Fastest response time, ideal for quick queries and simple tasks

## How It Works

### Z.ai Mode
Configures these settings in `~/.claude/settings.json`:
- `ANTHROPIC_AUTH_TOKEN`: Your Z.ai API key
- `ANTHROPIC_BASE_URL`: `https://api.z.ai/api/anthropic`
- `ANTHROPIC_DEFAULT_*_MODEL`: Your selected GLM model for each tier
- `API_TIMEOUT_MS`: `3000000` (50-minute timeout)

#### Model Selection Feature
Choose the perfect GLM model for each Claude tier:
- **Available Models**: GLM-4.6, GLM-4.5, GLM-4.5-Air
- **Opus Model**: Select which GLM model to use for Claude Opus requests
- **Sonnet Model**: Select which GLM model to use for Claude Sonnet requests
- **Haiku Model**: Select which GLM model to use for Claude Haiku requests
- **Flexible Configuration**: Mix and match models based on your needs (e.g., GLM-4.6 for Opus, GLM-4.5-Air for Haiku)

### Claude Mode
- Clears all custom settings to use your default Claude subscription
- Removes ANTHROPIC_* variables from settings.json

### Custom Mode
- Configures any API endpoint with your custom base URL and auth token
- Sets `ANTHROPIC_AUTH_TOKEN` and `ANTHROPIC_BASE_URL` to your values

### Technical Details
- App configuration stored in `~/.claude_ez_switch/config.json`
- **Only** modifies `~/.claude/settings.json`
- **Never** touches system environment variables or shell files
- Settings apply instantly - just restart Claude Code

## License
MIT