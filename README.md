# Claude Code EZ Switch

A Windows desktop application written in Python, that allows you to easily switch between different Claude Code API configurations, including Z.ai, Anthropic Claude, Moonshot.ai, and custom endpoints.

![Claude Code EZ Switch](https://img.shields.io/badge/Platform-Windows-blue?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.7%2B-yellow?style=flat-square)

## 🚀 Features

- **Easy Configuration Switching**: Seamlessly switch between Z.ai, Anthropic Claude, Moonshot.ai, and custom API endpoints
- **Enhanced Moonshot.ai Compatibility**: Full support for Kimi model family with endpoint verification
- **Persistent Storage**: Securely saves your API keys locally for convenience
- **Real-time Status Display**: Shows your current configuration at a glance
- **Modern Dark Theme**: Clean, professional interface with dark mode styling
- **Password Visibility Toggle**: Show/hide API keys for security
- **Automatic Detection**: Detects and pre-fills existing environment variables
- **Threading Support**: Non-blocking UI with loading indicators

## 📋 Requirements

- Python 3.7+
- Windows 10 or above
- Claude Code CLI

## 🛠️ Installation

```bash
git clone https://github.com/techcow2/claude-code-ez-switch.git
cd claude-code-ez-switch
python ezswitch.py
```

## 🎯 How to Use

### Quick Start

1. Run `python ezswitch.py`
2. Select your configuration (Z.ai, Anthropic, Moonshot.ai, or Custom) and enter your API key/URL
3. Click **Apply Configuration**
4. Close and reopen all Claude Code applications (VS Code, terminals, etc.) for changes to take effect
5. If switching to Anthropic, run `/login` in the CLI to re-authenticate

### Detailed Configuration

#### **Z.ai Configuration**
- Select "Z.ai" radio button
- Enter your Z.ai API key
- Click "Apply Configuration"

#### **Anthropic Claude Configuration**
- Select "Anthropic" radio button
- Choose between:
  - **Subscription Mode**: Use your Claude Pro/Team/Enterprise subscription
  - **API Key Mode**: Enter your Claude API key
- Click "Apply Configuration"

#### **Moonshot.ai Configuration**
- Select "Moonshot.ai" radio button
- Enter your Moonshot.ai API key
- Click "Apply Configuration"
- **📝 Note**: Moonshot.ai uses the Kimi model family (kimi-v1, kimi-v1.5, kimi-v1.5-long) which are compatible with Claude Code
- Ensure your Moonshot.ai account has API access enabled
- Verify your API key has sufficient credits for usage

#### **Custom Configuration**
- Select "Custom" radio button
- Enter your custom base URL (e.g., `https://your-api-endpoint.com`)
- Enter your custom API key
- Click "Apply Configuration"

## 🔧 Configuration Details

The application manages the following Windows environment variables:

- `ANTHROPIC_AUTH_TOKEN`: Your API authentication token
- `ANTHROPIC_BASE_URL`: The API base URL (if applicable)

### Configuration Examples:

**Z.ai**:
- `ANTHROPIC_AUTH_TOKEN`: Your Z.ai API key
- `ANTHROPIC_BASE_URL`: `https://api.z.ai/api/anthropic`

**Moonshot.ai**:
- `ANTHROPIC_AUTH_TOKEN`: Your Moonshot.ai API key
- `ANTHROPIC_BASE_URL`: `https://api.moonshot.ai/anthropic`
- **🔍 Endpoint Verification**: Test your Moonshot.ai endpoint with:
  ```bash
  curl -H "Authorization: Bearer YOUR_API_KEY" https://api.moonshot.ai/anthropic/v1/models
  ```
- **⚡ Rate Limits**: Moonshot.ai has different rate limits for free vs paid accounts
- **🌐 Alternative Endpoints**: If the main endpoint is unavailable, try:
  - Primary: `https://api.moonshot.ai/anthropic`
  - Alternative: `https://api.moonshot.cn/anthropic`

**Claude API**:
- `ANTHROPIC_AUTH_TOKEN`: Your Claude API key
- `ANTHROPIC_BASE_URL`: Not set (uses default)

**Custom**:
- `ANTHROPIC_AUTH_TOKEN`: Your custom API key
- `ANTHROPIC_BASE_URL`: Your custom endpoint URL

## 🐛 Troubleshooting

### Common Issues:

1. **"This application is designed for Windows only"**
   - This app only works on Windows due to PowerShell environment variable management

2. **Configuration not taking effect**
   - **CRITICAL**: Close ALL applications using Claude Code before reopening them
   - Environment variables are only loaded when applications start, not dynamically
   - Both Claude Code CLI and VS Code extension use the same environment variables

3. **Authentication issues when switching to Anthropic**
   - Run `claude code /login` in the CLI after switching to Anthropic configuration
   - This is required because switching from other endpoints clears your authentication session

4. **API keys not saving**
   - Ensure write permissions to your user home directory
   - Check config directory at `%USERPROFILE%\.claude_ez_switch\`
   - Config file should be at `%USERPROFILE%\.claude_ez_switch\config.json`

5. **PowerShell command failures**
   - Run as Administrator if you encounter permission issues
   - Ensure PowerShell execution policy allows running scripts

6. **Moonshot.ai specific issues**
   - **"Invalid API key" error**: Verify your Moonshot.ai API key is correct and has proper permissions
   - **"Endpoint not found" error**: Check if Moonshot.ai has changed their API endpoint URL
   - **Slow response times**: Moonshot.ai may have higher latency compared to other providers
   - **Model not available**: Ensure you're using a supported model (kimi-v1, kimi-v1.5, kimi-v1.5-long)
   - **Rate limiting**: Check your account limits at https://platform.moonshot.ai/account/limits
   - **Regional restrictions**: Some Moonshot.ai features may be restricted based on your geographic location

## 📝 Development

### Project Structure:
```
claude-code-ez-switch/
├── ezswitch.py              # Main application file
├── README.md                # This documentation
└── .git/                    # Git repository
```

## 📄 License

[MIT License](https://github.com/techcow2/claude-code-ez-switch/blob/master/LICENSE)