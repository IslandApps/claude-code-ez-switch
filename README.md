# Claude Code EZ Switch

**A simple alternative to Claude Code Router** - Easy GUI for switching between Claude Code API providers (Z.ai, Anthropic, Moonshot.ai, Custom).

## Features
- Simple graphical interface
- One-click configuration switching
- Saves API keys locally
- Real-time status display
- No command line required

## Requirements
- Python 3.7+
- Windows 10+ OR Ubuntu 18.04+
- Claude Code CLI

## Platform Support
- **Windows**: Full support with GUI styling and environment variable management
- **Ubuntu**: Full support with shell configuration management (.bashrc)
- **Other Linux distributions**: Should work with minor modifications

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

### Ubuntu/Linux Notes
- Environment variables are written to `~/.bashrc`
- You may need to run `source ~/.bashrc` or restart your terminal after applying configuration
- The app supports multiple shell configurations (.bashrc, .profile, .zshrc, .bash_profile)

## License
MIT