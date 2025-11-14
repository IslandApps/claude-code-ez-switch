# Claude Code EZ Switch

**A simple alternative to Claude Code Router** - Easy GUI for adding and managing your Z.ai API keys with Claude Code.

## Features
- Simple graphical interface
- One-click configuration switching
- Saves API keys locally
- Real-time status display
- No command line required

## Requirements
- Python 3.7+
- Windows 10+ OR Linux
- Claude Code CLI

## Platform Support
- **Windows**: Full support with GUI styling and environment variable management
- **Linux**: Full support with shell configuration management (.bashrc, .zshrc, .profile, .bash_profile)

## Quick Start
```bash
git clone https://github.com/techcow2/claude-code-ez-switch.git
cd claude-code-ez-switch
python ezswitch.py
```

## Usage
1. Run `python ezswitch.py`
2. Select provider and enter API key
3. Click **Apply Configuration**
4. Restart Claude Code apps

### Linux Notes
- Environment variables are written to your shell configuration file
- Run `source ~/.bashrc` (or your shell config) or restart terminal after applying configuration

## License
MIT