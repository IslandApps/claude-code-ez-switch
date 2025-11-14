# Claude Code EZ Switch

A simple GUI application for managing Claude Code API configurations - easily switch between Claude subscription and Z.ai API keys.

## Features
- **Easy GUI Interface**: No command line required
- **One-Click Switching**: Toggle between Z.ai and Claude subscription
- **Secure Local Storage**: API keys saved locally in `~/.claude_ez_switch/`
- **Real-time Status**: Visual feedback for configuration changes
- **Cross-Platform**: Windows and Linux support with platform-specific optimizations

## Requirements
- Python 3.7+
- Windows 10+ or Linux
- Claude Code CLI

## Platform Support
- **Windows**: Full support with registry-based environment variable management
- **Linux**: Full support with shell configuration management (.bashrc, .zshrc, .profile)

## Quick Start
```bash
git clone https://github.com/techcow2/claude-code-ez-switch.git
cd claude-code-ez-switch
python ezswitch.py
```

## Usage
1. Launch the app with `python ezswitch.py`
2. Select **Z.ai** or **Claude Subscription**
3. Enter your Z.ai API key (if applicable)
4. Click **Apply Configuration**
5. Restart your Claude Code applications

### Linux Notes
- After applying configuration, run `source ~/.bashrc` (or your shell config) or restart terminal

## How It Works
- **Z.ai Mode**: Sets `ANTHROPIC_AUTH_TOKEN` and `ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic`
- **Claude Mode**: Removes custom environment variables to use default Claude subscription
- Configuration stored in `~/.claude_ez_switch/config.json`
- Updates both system environment variables and Claude Code settings

## License
MIT