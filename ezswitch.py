import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import sys
import threading
import json
from pathlib import Path
from PIL import Image, ImageTk

class ClaudeConfigSwitcher:
    def __init__(self, root):
        self.root = root
        self.root.title("Claude Code EZ Switch")
        self.root.geometry("600x900")
        self.root.resizable(False, False)
        
        # Path for storing API keys persistently
        self.config_dir = Path.home() / ".claude_ez_switch"
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Color scheme
        self.bg_color = "#1e1e1e"
        self.fg_color = "#ffffff"
        self.accent_color = "#007acc"
        self.button_bg = "#0e639c"
        self.button_hover = "#1177bb"
        self.entry_bg = "#2d2d2d"
        self.success_color = "#4caf50"
        self.error_color = "#f44336"
        self.close_button_bg = "#555555"
        self.close_button_hover = "#666666"
        self.refresh_button_bg = "#2d5f2d"
        self.refresh_button_hover = "#3d7f3d"
        
        self.root.configure(bg=self.bg_color)
        
        # Configure styles
        style.configure('Title.TLabel', background=self.bg_color, foreground=self.fg_color,
                       font=('Segoe UI', 22, 'bold'))
        style.configure('Subtitle.TLabel', background=self.bg_color, foreground=self.fg_color,
                       font=('Segoe UI', 13))
        style.configure('TLabel', background=self.bg_color, foreground=self.fg_color, 
                       font=('Segoe UI', 10))
        style.configure('TRadiobutton', background=self.bg_color, foreground=self.fg_color, 
                       font=('Segoe UI', 10))
        style.map('TRadiobutton', background=[('active', self.bg_color)])
        
        self.create_widgets()
        self.load_saved_api_keys()
        self.load_existing_api_keys()
        # Update UI to match loaded configuration
        self.on_config_change()
        self.on_claude_mode_change()
        self.check_current_status()
        
    def create_widgets(self):
        # Main container
        main_frame = tk.Frame(self.root, bg=self.bg_color, padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Content frame (everything except footer)
        content_frame = tk.Frame(main_frame, bg=self.bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Light image container with light background
        try:
            # Load and resize the light image
            light_image = Image.open("images/light.png")
            # Make it very small (32x32 pixels)
            light_image = light_image.resize((32, 32), Image.Resampling.LANCZOS)
            self.light_photo = ImageTk.PhotoImage(light_image)
            
            # Create a frame with light background for the image
            image_container = tk.Frame(content_frame, bg="#f0f0f0", relief=tk.RAISED, bd=1)
            image_container.pack(pady=(0, 15))
            
            # Add some padding inside the container
            inner_frame = tk.Frame(image_container, bg="#f0f0f0", padx=8, pady=8)
            inner_frame.pack()
            
            # Create the image label
            light_label = tk.Label(inner_frame, image=self.light_photo, bg="#f0f0f0")
            light_label.pack()
            
        except Exception as e:
            # If image loading fails, continue without it
            print(f"Could not load light image: {e}")
        
        # Title
        title_label = ttk.Label(content_frame, text="Claude Code EZ Switch",
                               style='Title.TLabel')
        title_label.pack(pady=(0, 5))
        
        subtitle_label = ttk.Label(content_frame,
                                   text="Switch between z.ai, Claude, and custom configurations",
                                   style='Subtitle.TLabel')
        subtitle_label.pack(pady=(0, 15))
        
        # Current Status Frame
        status_frame = tk.Frame(content_frame, bg=self.entry_bg, relief=tk.FLAT, bd=0)
        status_frame.pack(fill=tk.X, pady=(0, 20), padx=2)
        
        status_title = ttk.Label(status_frame, text="Current Status:",
                                font=('Segoe UI', 15, 'bold'))
        status_title.pack(anchor=tk.W, padx=15, pady=(15, 10))

        self.status_label = tk.Label(status_frame, text="Checking...",
                                     bg=self.entry_bg, fg=self.fg_color,
                                     font=('Segoe UI', 14, 'bold'), anchor=tk.W, justify=tk.LEFT)
        self.status_label.pack(anchor=tk.W, padx=15, pady=(0, 15), fill=tk.X)
        
        # Loading indicator (hidden by default)
        self.loading_frame = tk.Frame(status_frame, bg=self.entry_bg)
        self.loading_label = tk.Label(self.loading_frame, text="⟳ Applying configuration...",
                                     bg=self.entry_bg, fg=self.accent_color,
                                     font=('Segoe UI', 14, 'bold'), anchor=tk.W)
        self.loading_label.pack(side=tk.LEFT, padx=15)
        
        self.progress_bar = ttk.Progressbar(self.loading_frame, mode='indeterminate', length=200)
        self.progress_bar.pack(side=tk.LEFT, padx=10)
        
        # Configuration Selection
        config_label = ttk.Label(content_frame, text="Select Configuration:",
                                font=('Segoe UI', 11, 'bold'))
        config_label.pack(anchor=tk.W, pady=(0, 10))
        
        self.config_var = tk.StringVar(value="zai")
        
        # Configuration radio buttons container
        radio_container = tk.Frame(content_frame, bg=self.bg_color)
        radio_container.pack(fill=tk.X, pady=(0, 10))
        
        # Z.ai radio button
        zai_radio = ttk.Radiobutton(radio_container, text="Z.ai", 
                                   variable=self.config_var, value="zai",
                                   command=self.on_config_change)
        zai_radio.pack(anchor=tk.W, pady=(0, 5))
        
        # Claude radio button
        claude_radio = ttk.Radiobutton(radio_container, text="Anthropic",
                                      variable=self.config_var, value="claude",
                                      command=self.on_config_change)
        claude_radio.pack(anchor=tk.W, pady=(0, 5))

        # Moonshot.ai radio button
        moonshot_radio = ttk.Radiobutton(radio_container, text="Moonshot.ai",
                                        variable=self.config_var, value="moonshot",
                                        command=self.on_config_change)
        moonshot_radio.pack(anchor=tk.W, pady=(0, 5))

        # Custom radio button
        custom_radio = ttk.Radiobutton(radio_container, text="Custom", 
                                      variable=self.config_var, value="custom",
                                      command=self.on_config_change)
        custom_radio.pack(anchor=tk.W, pady=(0, 5))
        
        # Dynamic configuration container (where different configs will be shown)
        self.dynamic_config_container = tk.Frame(content_frame, bg=self.bg_color)
        self.dynamic_config_container.pack(fill=tk.BOTH, expand=False)
        
        # Create all configuration frames but don't pack them yet
        self.create_zai_frame()
        self.create_claude_frame()
        self.create_moonshot_frame()
        self.create_custom_frame()
        
        # Show initial configuration
        self.on_config_change()
        
        # Show/Hide Password Checkbutton
        self.show_password_var = tk.BooleanVar()
        show_password_check = tk.Checkbutton(content_frame, text="Show API Keys",
                                           variable=self.show_password_var,
                                           command=self.toggle_password_visibility,
                                           bg=self.bg_color, fg=self.fg_color,
                                           selectcolor=self.entry_bg,
                                           activebackground=self.bg_color,
                                           activeforeground=self.fg_color,
                                           font=('Segoe UI', 9))
        show_password_check.pack(anchor=tk.W, pady=(10, 0))

        # Show Environment Variables Checkbutton
        self.show_env_vars_var = tk.BooleanVar()
        show_env_vars_check = tk.Checkbutton(content_frame, text="Show Environment Variables",
                                           variable=self.show_env_vars_var,
                                           command=self.toggle_env_vars_visibility,
                                           bg=self.bg_color, fg=self.fg_color,
                                           selectcolor=self.entry_bg,
                                           activebackground=self.bg_color,
                                           activeforeground=self.fg_color,
                                           font=('Segoe UI', 9))
        show_env_vars_check.pack(anchor=tk.W, pady=(5, 0))
        
        # Buttons Frame using Grid for better layout
        button_container = tk.Frame(content_frame, bg=self.bg_color)
        button_container.pack(fill=tk.X, pady=(20, 0))
        
        # Configure grid weights for responsive layout
        button_container.grid_columnconfigure(0, weight=2)
        button_container.grid_columnconfigure(1, weight=1)
        button_container.grid_columnconfigure(2, weight=1)
        
        # Apply Configuration Button (spans 2 columns)
        self.apply_button = tk.Button(button_container, text="Apply Configuration", 
                                      bg=self.button_bg, fg=self.fg_color,
                                      font=('Segoe UI', 11, 'bold'), relief=tk.FLAT,
                                      cursor="hand2", bd=0, pady=12,
                                      command=self.apply_configuration)
        self.apply_button.grid(row=0, column=0, columnspan=2, sticky="ew", padx=(0, 5), pady=(0, 8))
        
        # Bind hover effects
        self.apply_button.bind('<Enter>', lambda e: self.apply_button.configure(bg=self.button_hover))
        self.apply_button.bind('<Leave>', lambda e: self.apply_button.configure(bg=self.button_bg))
        
        # Refresh Status Button
        self.refresh_button = tk.Button(button_container, text="Refresh", 
                                       bg=self.refresh_button_bg, fg=self.fg_color,
                                       font=('Segoe UI', 10, 'bold'), relief=tk.FLAT,
                                       cursor="hand2", bd=0, pady=12,
                                       command=self.check_current_status)
        self.refresh_button.grid(row=0, column=2, sticky="ew", padx=(5, 0), pady=(0, 8))
        
        # Bind hover effects
        self.refresh_button.bind('<Enter>', lambda e: self.refresh_button.configure(bg=self.refresh_button_hover))
        self.refresh_button.bind('<Leave>', lambda e: self.refresh_button.configure(bg=self.refresh_button_bg))
        
        # Close Button (spans all columns)
        self.close_button = tk.Button(button_container, text="Close Application", 
                                     bg=self.close_button_bg, fg=self.fg_color,
                                     font=('Segoe UI', 10), relief=tk.FLAT,
                                     cursor="hand2", bd=0, pady=10,
                                     command=self.close_application)
        self.close_button.grid(row=1, column=0, columnspan=3, sticky="ew")
        
        # Bind hover effects
        self.close_button.bind('<Enter>', lambda e: self.close_button.configure(bg=self.close_button_hover))
        self.close_button.bind('<Leave>', lambda e: self.close_button.configure(bg=self.close_button_bg))
        
        # Footer
        footer_frame = tk.Frame(main_frame, bg=self.bg_color)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(20, 10))
        
        footer_text = "Claude Code EZ Switch is open source under the MIT license"
        footer_label = tk.Label(footer_frame, text=footer_text,
                              bg=self.bg_color, fg="#888888",
                              font=('Segoe UI', 8))
        footer_label.pack()
        
        # GitHub link
        github_link = tk.Label(footer_frame, text="Source Code",
                              bg=self.bg_color, fg=self.accent_color,
                              font=('Segoe UI', 8, 'underline'), cursor="hand2")
        github_link.pack()
        github_link.bind("<Button-1>", lambda e: self.open_github_link())
    
    def create_zai_frame(self):
        """Create Z.ai configuration frame"""
        self.zai_frame = tk.LabelFrame(self.dynamic_config_container, text="", bg=self.entry_bg,
                                 fg=self.fg_color, relief=tk.FLAT, bd=2)

        zai_key_label = ttk.Label(self.zai_frame, text="Z.ai API Key:")
        zai_key_label.pack(anchor=tk.W, padx=15, pady=(10, 2))

        self.zai_key_entry = tk.Entry(self.zai_frame, bg=self.entry_bg, fg=self.fg_color,
                                      insertbackground=self.fg_color, relief=tk.FLAT,
                                      font=('Segoe UI', 10), bd=0, show="*")
        self.zai_key_entry.pack(fill=tk.X, padx=15, pady=(0, 2), ipady=8)

        # Add border to entry
        entry_border = tk.Frame(self.zai_frame, bg=self.accent_color, height=2)
        entry_border.pack(fill=tk.X, padx=15, pady=(0, 10))

        # Environment variables display (hidden by default)
        self.zai_env_frame = tk.Frame(self.zai_frame, bg=self.entry_bg)
        self.zai_env_vars_text = tk.Text(self.zai_env_frame, bg=self.entry_bg, fg="#cccccc",
                                         font=('Consolas', 10), height=12, wrap=tk.WORD,
                                         relief=tk.FLAT, bd=0, state=tk.DISABLED)
        self.zai_env_vars_text.pack(fill=tk.X, padx=15, pady=(0, 10))

        # Populate environment variables text
        zai_env_vars = [
            "ANTHROPIC_AUTH_TOKEN=<your-zai-api-key> (User level)",
            "ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic (User level)",
            "ANTHROPIC_DEFAULT_OPUS_MODEL=GLM-4.6 (User level)",
            "ANTHROPIC_DEFAULT_SONNET_MODEL=GLM-4.6 (User level)",
            "ANTHROPIC_DEFAULT_HAIKU_MODEL=GLM-4.5-Air (User level)",
            "",
            "(Note: All variables set at User level - no admin rights required)"
        ]
        self.zai_env_vars_text.configure(state=tk.NORMAL)
        self.zai_env_vars_text.insert('1.0', '\n'.join(zai_env_vars))
        self.zai_env_vars_text.configure(state=tk.DISABLED)
    
    def create_claude_frame(self):
        """Create Claude configuration frame"""
        self.claude_frame = tk.LabelFrame(self.dynamic_config_container, text="", bg=self.entry_bg,
                                    fg=self.fg_color, relief=tk.FLAT, bd=2)

        self.claude_mode_var = tk.StringVar(value="subscription")

        subscription_radio = ttk.Radiobutton(self.claude_frame, text="Use Claude Subscription (Pro/Team/Enterprise)",
                                           variable=self.claude_mode_var, value="subscription",
                                           command=self.on_claude_mode_change)
        subscription_radio.pack(anchor=tk.W, padx=15, pady=(10, 5))

        api_radio = ttk.Radiobutton(self.claude_frame, text="Use Claude API Key",
                                   variable=self.claude_mode_var, value="api",
                                   command=self.on_claude_mode_change)
        api_radio.pack(anchor=tk.W, padx=15, pady=(0, 5))

        claude_key_label = ttk.Label(self.claude_frame, text="Claude API Key:")
        claude_key_label.pack(anchor=tk.W, padx=15, pady=(5, 2))

        self.claude_key_entry = tk.Entry(self.claude_frame, bg=self.entry_bg, fg=self.fg_color,
                                         insertbackground=self.fg_color, relief=tk.FLAT,
                                         font=('Segoe UI', 10), bd=0, show="*", state=tk.DISABLED,
                                         disabledbackground=self.entry_bg, disabledforeground="#888888")
        self.claude_key_entry.pack(fill=tk.X, padx=15, pady=(0, 2), ipady=8)

        # Add border to entry
        claude_entry_border = tk.Frame(self.claude_frame, bg=self.accent_color, height=2)
        claude_entry_border.pack(fill=tk.X, padx=15, pady=(0, 10))

        # Environment variables display (hidden by default)
        self.claude_env_frame = tk.Frame(self.claude_frame, bg=self.entry_bg)
        self.claude_env_vars_text = tk.Text(self.claude_env_frame, bg=self.entry_bg, fg="#cccccc",
                                           font=('Consolas', 10), height=4, wrap=tk.WORD,
                                           relief=tk.FLAT, bd=0, state=tk.DISABLED)
        self.claude_env_vars_text.pack(fill=tk.X, padx=15, pady=(0, 10))

        # Populate environment variables text
        subscription_env_vars = [
            "ANTHROPIC_AUTH_TOKEN=<removed>",
            "ANTHROPIC_BASE_URL=<removed>",
            "",
            "(Note: No environment variables are used with Claude Subscription)"
        ]
        self.claude_env_vars_text.configure(state=tk.NORMAL)
        self.claude_env_vars_text.insert('1.0', '\n'.join(subscription_env_vars))
        self.claude_env_vars_text.configure(state=tk.DISABLED)
    
    def create_custom_frame(self):
        """Create Custom configuration frame"""
        self.custom_frame = tk.LabelFrame(self.dynamic_config_container, text="", bg=self.entry_bg,
                                    fg=self.fg_color, relief=tk.FLAT, bd=2)

        custom_url_label = ttk.Label(self.custom_frame, text="Custom Base URL:")
        custom_url_label.pack(anchor=tk.W, padx=15, pady=(10, 2))

        self.custom_url_entry = tk.Entry(self.custom_frame, bg=self.entry_bg, fg=self.fg_color,
                                         insertbackground=self.fg_color, relief=tk.FLAT,
                                         font=('Segoe UI', 10), bd=0)
        self.custom_url_entry.pack(fill=tk.X, padx=15, pady=(0, 2), ipady=8)

        # Add border to entry
        custom_url_border = tk.Frame(self.custom_frame, bg=self.accent_color, height=2)
        custom_url_border.pack(fill=tk.X, padx=15, pady=(0, 5))

        custom_key_label = ttk.Label(self.custom_frame, text="Custom API Key:")
        custom_key_label.pack(anchor=tk.W, padx=15, pady=(5, 2))

        self.custom_key_entry = tk.Entry(self.custom_frame, bg=self.entry_bg, fg=self.fg_color,
                                         insertbackground=self.fg_color, relief=tk.FLAT,
                                         font=('Segoe UI', 10), bd=0, show="*")
        self.custom_key_entry.pack(fill=tk.X, padx=15, pady=(0, 2), ipady=8)

        # Add border to entry
        custom_key_border = tk.Frame(self.custom_frame, bg=self.accent_color, height=2)
        custom_key_border.pack(fill=tk.X, padx=15, pady=(0, 10))

        # Environment variables display (hidden by default)
        self.custom_env_frame = tk.Frame(self.custom_frame, bg=self.entry_bg)
        self.custom_env_vars_text = tk.Text(self.custom_env_frame, bg=self.entry_bg, fg="#cccccc",
                                           font=('Consolas', 10), height=4, wrap=tk.WORD,
                                           relief=tk.FLAT, bd=0, state=tk.DISABLED)
        self.custom_env_vars_text.pack(fill=tk.X, padx=15, pady=(0, 10))

        # Populate environment variables text
        custom_env_vars = [
            "ANTHROPIC_AUTH_TOKEN=<your-custom-api-key> (User level)",
            "ANTHROPIC_BASE_URL=<your-custom-base-url> (User level)",
            "",
            "(Note: Only basic auth token and base URL are set at User level)"
        ]
        self.custom_env_vars_text.configure(state=tk.NORMAL)
        self.custom_env_vars_text.insert('1.0', '\n'.join(custom_env_vars))
        self.custom_env_vars_text.configure(state=tk.DISABLED)

        # Bind events to save API keys when they change
        self.zai_key_entry.bind('<KeyRelease>', lambda e: self.save_api_keys())
        self.claude_key_entry.bind('<KeyRelease>', lambda e: self.save_api_keys())
        self.moonshot_key_entry.bind('<KeyRelease>', lambda e: self.save_api_keys())
        self.custom_key_entry.bind('<KeyRelease>', lambda e: self.save_api_keys())
        self.custom_url_entry.bind('<KeyRelease>', lambda e: self.save_api_keys())

    def create_moonshot_frame(self):
        """Create Moonshot.ai configuration frame"""
        self.moonshot_frame = tk.LabelFrame(self.dynamic_config_container, text="", bg=self.entry_bg,
                                       fg=self.fg_color, relief=tk.FLAT, bd=2)

        moonshot_key_label = ttk.Label(self.moonshot_frame, text="Moonshot.ai API Key:")
        moonshot_key_label.pack(anchor=tk.W, padx=15, pady=(10, 2))

        self.moonshot_key_entry = tk.Entry(self.moonshot_frame, bg=self.entry_bg, fg=self.fg_color,
                                          insertbackground=self.fg_color, relief=tk.FLAT,
                                          font=('Segoe UI', 10), bd=0, show="*")
        self.moonshot_key_entry.pack(fill=tk.X, padx=15, pady=(0, 2), ipady=8)

        # Add border to entry
        moonshot_key_border = tk.Frame(self.moonshot_frame, bg=self.accent_color, height=2)
        moonshot_key_border.pack(fill=tk.X, padx=15, pady=(0, 10))

        # Environment variables display (hidden by default)
        self.moonshot_env_frame = tk.Frame(self.moonshot_frame, bg=self.entry_bg)
        self.moonshot_env_vars_text = tk.Text(self.moonshot_env_frame, bg=self.entry_bg, fg="#cccccc",
                                             font=('Consolas', 10), height=4, wrap=tk.WORD,
                                             relief=tk.FLAT, bd=0, state=tk.DISABLED)
        self.moonshot_env_vars_text.pack(fill=tk.X, padx=15, pady=(0, 10))

        # Populate environment variables text
        moonshot_env_vars = [
            "ANTHROPIC_AUTH_TOKEN=<your-moonshot-api-key> (User level)",
            "ANTHROPIC_BASE_URL=https://api.moonshot.ai/anthropic (User level)",
            "",
            "(Note: Moonshot.ai API endpoint with your API key at User level)"
        ]
        self.moonshot_env_vars_text.configure(state=tk.NORMAL)
        self.moonshot_env_vars_text.insert('1.0', '\n'.join(moonshot_env_vars))
        self.moonshot_env_vars_text.configure(state=tk.DISABLED)
    
    def load_existing_api_keys(self):
        """Load existing API keys from environment variables and pre-fill them"""
        try:
            # Only check user-level environment variables via PowerShell (not current process)
            result = subprocess.run(
                ['powershell', '-Command',
                 "[System.Environment]::GetEnvironmentVariable('ANTHROPIC_AUTH_TOKEN', 'User')"],
                capture_output=True, text=True, timeout=5
            )
            user_auth_token = result.stdout.strip()
            
            result = subprocess.run(
                ['powershell', '-Command',
                 "[System.Environment]::GetEnvironmentVariable('ANTHROPIC_BASE_URL', 'User')"],
                capture_output=True, text=True, timeout=5
            )
            user_base_url = result.stdout.strip()
            
            # Only update fields if they're empty AND if the environment variables are explicitly set
            # Don't pre-fill anything if using subscription (no environment variables)
            
            # Pre-fill z.ai key only if it's set and base_url explicitly points to z.ai
            if user_auth_token and user_base_url and 'z.ai' in user_base_url:
                if not self.zai_key_entry.get().strip():
                    self.zai_key_entry.delete(0, tk.END)
                    self.zai_key_entry.insert(0, user_auth_token)
            
            # Pre-fill custom configuration only if both auth token and base URL are set and it's not z.ai
            elif user_auth_token and user_base_url and user_base_url.strip() and 'z.ai' not in user_base_url:
                if not self.custom_url_entry.get().strip():
                    self.custom_url_entry.delete(0, tk.END)
                    self.custom_url_entry.insert(0, user_base_url)
                
                if not self.custom_key_entry.get().strip():
                    self.custom_key_entry.delete(0, tk.END)
                    self.custom_key_entry.insert(0, user_auth_token)
            
            # Pre-fill Claude API key only if auth token is set but base URL is explicitly empty/null
            elif user_auth_token and not user_base_url:
                if not self.claude_key_entry.get().strip():
                    self.claude_key_entry.configure(state=tk.NORMAL)
                    self.claude_key_entry.delete(0, tk.END)
                    self.claude_key_entry.insert(0, user_auth_token)
                    self.claude_key_entry.configure(state=tk.DISABLED)
                
        except Exception as e:
            # Silently fail if we can't load keys
            pass
    
    def load_saved_api_keys(self):
        """Load API keys from the persistent storage file"""
        try:
            saved_keys = {}
            
            # Check if new config file exists
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    saved_keys = json.load(f)
            else:
                # Check if old config file exists and migrate it
                old_config_file = Path.home() / ".claude_code_ez_switch_config.json"
                if old_config_file.exists():
                    with open(old_config_file, 'r') as f:
                        saved_keys = json.load(f)
                    # Save to new location
                    with open(self.config_file, 'w') as f:
                        json.dump(saved_keys, f, indent=2)
                    # Remove old file
                    old_config_file.unlink()
            
            # Load z.ai key
            if 'zai_key' in saved_keys:
                self.zai_key_entry.delete(0, tk.END)
                self.zai_key_entry.insert(0, saved_keys['zai_key'])
            
            # Load Claude key
            if 'claude_key' in saved_keys:
                self.claude_key_entry.configure(state=tk.NORMAL)
                self.claude_key_entry.delete(0, tk.END)
                self.claude_key_entry.insert(0, saved_keys['claude_key'])
                self.claude_key_entry.configure(state=tk.DISABLED)

            # Load Moonshot.ai key
            if 'moonshot_key' in saved_keys:
                self.moonshot_key_entry.delete(0, tk.END)
                self.moonshot_key_entry.insert(0, saved_keys['moonshot_key'])

            # Load custom config
            if 'custom_url' in saved_keys:
                self.custom_url_entry.delete(0, tk.END)
                self.custom_url_entry.insert(0, saved_keys['custom_url'])
            
            if 'custom_key' in saved_keys:
                self.custom_key_entry.delete(0, tk.END)
                self.custom_key_entry.insert(0, saved_keys['custom_key'])
            
            # Load Claude mode
            if 'claude_mode' in saved_keys:
                self.claude_mode_var.set(saved_keys['claude_mode'])
                self.on_claude_mode_change()
            
            # Load selected config
            if 'selected_config' in saved_keys:
                self.config_var.set(saved_keys['selected_config'])
        except Exception as e:
            # Silently fail if we can't load saved keys
            pass
    
    def save_api_keys(self):
        """Save current API keys to persistent storage"""
        try:
            saved_keys = {}
            
            # Save z.ai key if not empty
            zai_key = self.zai_key_entry.get().strip()
            if zai_key:
                saved_keys['zai_key'] = zai_key
            
            # Save Claude key if not empty
            claude_key = self.claude_key_entry.get().strip()
            if claude_key:
                saved_keys['claude_key'] = claude_key

            # Save Moonshot.ai key if not empty
            moonshot_key = self.moonshot_key_entry.get().strip()
            if moonshot_key:
                saved_keys['moonshot_key'] = moonshot_key

            # Save custom config if not empty
            custom_url = self.custom_url_entry.get().strip()
            if custom_url:
                saved_keys['custom_url'] = custom_url
            
            custom_key = self.custom_key_entry.get().strip()
            if custom_key:
                saved_keys['custom_key'] = custom_key
            
            # Save Claude mode
            saved_keys['claude_mode'] = self.claude_mode_var.get()
            
            # Save selected config
            saved_keys['selected_config'] = self.config_var.get()
            
            # Write to file
            with open(self.config_file, 'w') as f:
                json.dump(saved_keys, f, indent=2)
        except Exception as e:
            # Silently fail if we can't save keys
            pass
    
    def open_github_link(self):
        """Open the GitHub repository link"""
        import webbrowser
        webbrowser.open("https://github.com/techcow2/claude-code-ez-switch")
    
    def on_config_change(self):
        """Handle configuration radio button change - switch visible frame"""
        # Hide all frames first
        self.zai_frame.pack_forget()
        self.custom_frame.pack_forget()
        self.claude_frame.pack_forget()
        self.moonshot_frame.pack_forget()

        # Show the selected frame
        if self.config_var.get() == "zai":
            self.zai_frame.pack(fill=tk.X, pady=(0, 10))
        elif self.config_var.get() == "custom":
            self.custom_frame.pack(fill=tk.X, pady=(0, 10))
        elif self.config_var.get() == "claude":
            self.claude_frame.pack(fill=tk.X, pady=(0, 10))
        elif self.config_var.get() == "moonshot":
            self.moonshot_frame.pack(fill=tk.X, pady=(0, 10))
    
    def on_claude_mode_change(self):
        """Handle Claude mode radio button change"""
        if self.claude_mode_var.get() == "api":
            self.claude_key_entry.configure(state=tk.NORMAL)
            # Update environment variables display for API mode
            api_env_vars = [
                "ANTHROPIC_AUTH_TOKEN=<your-claude-api-key>",
                "ANTHROPIC_BASE_URL=<removed>",
                "",
                "(Note: Only API key is set, base URL is removed)"
            ]
            self.claude_env_vars_text.configure(state=tk.NORMAL)
            self.claude_env_vars_text.delete('1.0', tk.END)
            self.claude_env_vars_text.insert('1.0', '\n'.join(api_env_vars))
            self.claude_env_vars_text.configure(state=tk.DISABLED)
        else:
            self.claude_key_entry.configure(state=tk.DISABLED)
            # Update environment variables display for subscription mode
            subscription_env_vars = [
                "ANTHROPIC_AUTH_TOKEN=<removed>",
                "ANTHROPIC_BASE_URL=<removed>",
                "",
                "(Note: No environment variables are used with Claude Subscription)"
            ]
            self.claude_env_vars_text.configure(state=tk.NORMAL)
            self.claude_env_vars_text.delete('1.0', tk.END)
            self.claude_env_vars_text.insert('1.0', '\n'.join(subscription_env_vars))
            self.claude_env_vars_text.configure(state=tk.DISABLED)
    
    def toggle_password_visibility(self):
        """Toggle password visibility in entry fields"""
        if self.show_password_var.get():
            self.zai_key_entry.configure(show="")
            self.custom_key_entry.configure(show="")
            self.claude_key_entry.configure(show="")
            self.moonshot_key_entry.configure(show="")
        else:
            self.zai_key_entry.configure(show="*")
            self.custom_key_entry.configure(show="*")
            self.claude_key_entry.configure(show="*")
            self.moonshot_key_entry.configure(show="*")

    def toggle_env_vars_visibility(self):
        """Toggle environment variables display visibility"""
        if self.show_env_vars_var.get():
            # Show all environment variable frames
            self.zai_env_frame.pack(fill=tk.X, pady=(0, 10))
            self.claude_env_frame.pack(fill=tk.X, pady=(0, 10))
            self.custom_env_frame.pack(fill=tk.X, pady=(0, 10))
            self.moonshot_env_frame.pack(fill=tk.X, pady=(0, 10))
        else:
            # Hide all environment variable frames
            self.zai_env_frame.pack_forget()
            self.claude_env_frame.pack_forget()
            self.custom_env_frame.pack_forget()
            self.moonshot_env_frame.pack_forget()
    
    def close_application(self):
        """Properly close the application"""
        self.root.destroy()
    
    def show_loading(self):
        """Show loading spinner"""
        self.loading_frame.pack(fill=tk.X, pady=(5, 5))
        self.progress_bar.start(10)
        self.apply_button.configure(state=tk.DISABLED)
        self.refresh_button.configure(state=tk.DISABLED)
        self.root.update_idletasks()
    
    def hide_loading(self):
        """Hide loading spinner"""
        self.progress_bar.stop()
        self.loading_frame.pack_forget()
        self.apply_button.configure(state=tk.NORMAL)
        self.refresh_button.configure(state=tk.NORMAL)
        self.root.update_idletasks()
    
    def check_current_status(self):
        """Check current environment variable configuration"""
        try:
            # Only check persistent user environment variables (not current process)
            result = subprocess.run(
                ['powershell', '-Command',
                 "[System.Environment]::GetEnvironmentVariable('ANTHROPIC_AUTH_TOKEN', 'User')"],
                capture_output=True, text=True, timeout=5
            )
            user_auth_token = result.stdout.strip()
            
            result = subprocess.run(
                ['powershell', '-Command',
                 "[System.Environment]::GetEnvironmentVariable('ANTHROPIC_BASE_URL', 'User')"],
                capture_output=True, text=True, timeout=5
            )
            user_base_url = result.stdout.strip()
            
            if user_base_url and 'z.ai' in user_base_url:
                status_text = "✓ Currently using z.ai API"
                self.status_label.configure(text=status_text, fg=self.success_color)
            elif user_base_url and 'moonshot.ai' in user_base_url:
                status_text = "✓ Currently using Moonshot.ai API"
                self.status_label.configure(text=status_text, fg=self.success_color)
            elif user_base_url and user_auth_token:
                status_text = f"✓ Currently using Custom Base URL\n"
                status_text += f"Base URL: {user_base_url}"
                self.status_label.configure(text=status_text, fg=self.success_color)
            elif user_auth_token and not user_base_url:
                status_text = "✓ Currently using Claude API Key"
                self.status_label.configure(text=status_text, fg=self.success_color)
            else:
                status_text = "✓ Currently using Claude Subscription\n(No environment variables set)"
                self.status_label.configure(text=status_text, fg=self.success_color)
                
        except Exception as e:
            self.status_label.configure(
                text=f"⚠ Could not determine current status\nError: {str(e)}",
                fg=self.error_color
            )
    
    def run_powershell_command(self, command):
        """Run a PowerShell command and return success status"""
        try:
            result = subprocess.run(
                ['powershell', '-Command', command],
                capture_output=True, text=True, timeout=30, check=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, f"Command failed: {e.stderr}"
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)
    
    def apply_configuration_thread(self):
        """Thread worker for applying configuration"""
        try:
            if self.config_var.get() == "zai":
                # Apply z.ai configuration
                zai_key = self.zai_key_entry.get().strip()
                
                if not zai_key:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Please enter your z.ai API key"))
                    self.root.after(0, self.hide_loading)
                    return
                
                # Set z.ai environment variables (all at User level to avoid admin requirements)
                commands = [
                    f"[System.Environment]::SetEnvironmentVariable('ANTHROPIC_AUTH_TOKEN', '{zai_key}', 'User')",
                    f"[System.Environment]::SetEnvironmentVariable('ANTHROPIC_BASE_URL', 'https://api.z.ai/api/anthropic', 'User')",
                    "[System.Environment]::SetEnvironmentVariable('ANTHROPIC_DEFAULT_OPUS_MODEL', 'GLM-4.6', 'User')",
                    "[System.Environment]::SetEnvironmentVariable('ANTHROPIC_DEFAULT_SONNET_MODEL', 'GLM-4.6', 'User')",
                    "[System.Environment]::SetEnvironmentVariable('ANTHROPIC_DEFAULT_HAIKU_MODEL', 'GLM-4.5-Air', 'User')"
                ]
                
                for cmd in commands:
                    success, output = self.run_powershell_command(cmd)
                    if not success:
                        self.root.after(0, lambda msg=output: messagebox.showerror("Error", f"Failed to set environment variable:\n{msg}"))
                        self.root.after(0, self.hide_loading)
                        return
                
                self.root.after(0, lambda: messagebox.showinfo("Success",
                                   "Z.ai configuration applied successfully!\n\n"
                                   "IMPORTANT: You must close and reopen VS Code or any application using Claude Code for changes to take effect.\n"
                                   "If using terminal only, close and reopen the terminal."))
            
            elif self.config_var.get() == "custom":
                # Apply custom configuration
                custom_url = self.custom_url_entry.get().strip()
                custom_key = self.custom_key_entry.get().strip()
                
                if not custom_url:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Please enter a custom base URL"))
                    self.root.after(0, self.hide_loading)
                    return
                
                if not custom_key:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Please enter your custom API key"))
                    self.root.after(0, self.hide_loading)
                    return
                
                # Set custom environment variables
                commands = [
                    f"[System.Environment]::SetEnvironmentVariable('ANTHROPIC_AUTH_TOKEN', '{custom_key}', 'User')",
                    f"[System.Environment]::SetEnvironmentVariable('ANTHROPIC_BASE_URL', '{custom_url}', 'User')"
                ]
                
                for cmd in commands:
                    success, output = self.run_powershell_command(cmd)
                    if not success:
                        self.root.after(0, lambda msg=output: messagebox.showerror("Error", f"Failed to set environment variable:\n{msg}"))
                        self.root.after(0, self.hide_loading)
                        return
                
                self.root.after(0, lambda: messagebox.showinfo("Success",
                                   "Custom configuration applied successfully!\n\n"
                                   "IMPORTANT: You must close and reopen VS Code or any application using Claude Code for changes to take effect.\n"
                                   "If using terminal only, close and reopen the terminal."))

            elif self.config_var.get() == "moonshot":
                # Apply Moonshot.ai configuration
                moonshot_key = self.moonshot_key_entry.get().strip()

                if not moonshot_key:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Please enter your Moonshot.ai API key"))
                    self.root.after(0, self.hide_loading)
                    return

                # Set Moonshot.ai environment variables
                commands = [
                    f"[System.Environment]::SetEnvironmentVariable('ANTHROPIC_AUTH_TOKEN', '{moonshot_key}', 'User')",
                    "[System.Environment]::SetEnvironmentVariable('ANTHROPIC_BASE_URL', 'https://api.moonshot.ai/anthropic', 'User')"
                ]

                for cmd in commands:
                    success, output = self.run_powershell_command(cmd)
                    if not success:
                        self.root.after(0, lambda msg=output: messagebox.showerror("Error", f"Failed to set environment variable:\n{msg}"))
                        self.root.after(0, self.hide_loading)
                        return

                self.root.after(0, lambda: messagebox.showinfo("Success",
                                   "Moonshot.ai configuration applied successfully!\n\n"
                                   "IMPORTANT: You must close and reopen VS Code or any application using Claude Code for changes to take effect.\n"
                                   "If using terminal only, close and reopen the terminal."))

            else:
                # Apply Claude configuration
                if self.claude_mode_var.get() == "subscription":
                    # Remove all environment variables to use subscription
                    commands = [
                        "[System.Environment]::SetEnvironmentVariable('ANTHROPIC_AUTH_TOKEN', $null, 'User')",
                        "[System.Environment]::SetEnvironmentVariable('ANTHROPIC_BASE_URL', $null, 'User')"
                    ]
                    
                    for cmd in commands:
                        success, output = self.run_powershell_command(cmd)
                        if not success:
                            self.root.after(0, lambda msg=output: messagebox.showerror("Error", f"Failed to remove environment variable:\n{msg}"))
                            self.root.after(0, self.hide_loading)
                            return
                    
                    self.root.after(0, lambda: messagebox.showinfo("Success",
                                       "Claude Subscription configuration applied successfully!\n\n"
                                       "IMPORTANT: You must close and reopen VS Code or any application using Claude Code for changes to take effect.\n"
                                       "If using terminal only, close and reopen the terminal."))
                    
                else:
                    # Use Claude API key
                    claude_key = self.claude_key_entry.get().strip()
                    
                    if not claude_key:
                        self.root.after(0, lambda: messagebox.showerror("Error", "Please enter your Claude API key"))
                        self.root.after(0, self.hide_loading)
                        return
                    
                    # Set Claude API key, remove base URL
                    commands = [
                        f"[System.Environment]::SetEnvironmentVariable('ANTHROPIC_AUTH_TOKEN', '{claude_key}', 'User')",
                        "[System.Environment]::SetEnvironmentVariable('ANTHROPIC_BASE_URL', $null, 'User')"
                    ]
                    
                    for cmd in commands:
                        success, output = self.run_powershell_command(cmd)
                        if not success:
                            self.root.after(0, lambda msg=output: messagebox.showerror("Error", f"Failed to set environment variable:\n{msg}"))
                            self.root.after(0, self.hide_loading)
                            return
                    
                    self.root.after(0, lambda: messagebox.showinfo("Success",
                                       "Claude API Key configuration applied successfully!\n\n"
                                       "IMPORTANT: You must close and reopen VS Code or any application using Claude Code for changes to take effect.\n"
                                       "If using terminal only, close and reopen the terminal."))
            
            # Save API keys after applying configuration
            self.save_api_keys()
            
            # Refresh status after applying
            self.root.after(0, self.hide_loading)
            self.root.after(500, self.check_current_status)
            
        except Exception as e:
            self.root.after(0, lambda msg=str(e): messagebox.showerror("Error", f"An unexpected error occurred:\n{msg}"))
            self.root.after(0, self.hide_loading)
    
    def apply_configuration(self):
        """Apply the selected configuration using threading to prevent UI freeze"""
        # Show loading indicator
        self.show_loading()
        
        # Start configuration application in a separate thread
        config_thread = threading.Thread(target=self.apply_configuration_thread, daemon=True)
        config_thread.start()

def main():
    """Main entry point"""
    # Check if running on Windows
    if sys.platform != 'win32':
        print("This application is designed for Windows only.")
        sys.exit(1)
    
    root = tk.Tk()
    app = ClaudeConfigSwitcher(root)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()
