import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import sys
import threading
import json
from pathlib import Path
import platform

# Platform detection and module imports
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"
IS_MACOS = platform.system() == "Darwin"

# Try to import Windows-specific modules
try:
    import win32gui
    import win32con
    from ctypes import windll, c_int, byref
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

# Font management for Poppins
class FontManager:
    def __init__(self):
        self.primary_font = "Poppins"
        # Platform-specific font preferences
        if IS_LINUX:
            self.fallback_fonts = ["Ubuntu", "DejaVu Sans", "Liberation Sans", "Noto Sans", "Cantarell", "Arial", "Helvetica", "sans-serif"]
        elif IS_MACOS:
            self.fallback_fonts = ["SF Pro", "San Francisco", "Helvetica Neue", "Arial", "Helvetica", "sans-serif"]
        else:
            self.fallback_fonts = ["Segoe UI", "Arial", "Helvetica", "sans-serif"]
        self.available_font = None
        self._font_detection_attempted = False
        self.scaling_factor = 1.0

    def get_available_font(self):
        """Get the best available font, preferring Poppins"""
        if self.available_font:
            return self.available_font

        if self._font_detection_attempted:
            return "TkDefaultFont"

        try:
            import tkinter.font as tkfont

            # Check if root window exists
            try:
                root = tk._default_root
                if root is None:
                    # No root window yet, return fallback
                    self.available_font = "TkDefaultFont"
                    return self.available_font
            except:
                pass

            # Get list of available font families
            available_fonts = tkfont.families()

            # Check if Poppins is available
            if self.primary_font in available_fonts:
                self.available_font = self.primary_font
                return self.available_font

            # Check fallback fonts in order of preference
            for font in self.fallback_fonts:
                if font in available_fonts:
                    self.available_font = font
                    return self.available_font

        except Exception:
            pass
        finally:
            self._font_detection_attempted = True

        # Ultimate fallback
        self.available_font = "TkDefaultFont"
        return self.available_font

    def get_font(self, size=10, weight="normal", slant="roman"):
        """Get a font tuple with the best available font and platform-appropriate scaling"""
        # Ensure we have detected fonts
        if not self.available_font:
            self.get_available_font()

        # Platform-specific scaling
        if IS_LINUX:
            # Linux often needs smaller fonts for the same perceived size
            scaled_size = max(size - 1, 8)  # Reduce by 1 but keep minimum of 8
        elif IS_MACOS:
            # macOS handles font scaling well, use original size
            scaled_size = size
        else:
            scaled_size = size

        # Handle special font styles
        weight_val = "bold" if weight == "bold" else "normal"
        slant_val = "italic" if slant == "italic" else "roman"

        # Return standard 4-element font tuple
        return (self.available_font, scaled_size, weight_val, slant_val)

# Initialize font manager
font_manager = FontManager()

class ClaudeConfigSwitcher:
    def __init__(self, root):
        self.root = root
        self.root.title("")

        # Platform-specific window settings
        if IS_LINUX:
            # Linux: More conservative size and allow resizing
            self.root.geometry("550x850")
            self.root.resizable(True, True)
            self.root.minsize(450, 700)
        elif IS_MACOS:
            # macOS: Original size and no resizing
            self.root.geometry("600x1000")
            self.root.resizable(False, False)
        else:
            # Windows: Increased height to account for taskbar and prevent footer cutoff
            self.root.geometry("600x1100")
            self.root.resizable(False, False)

        # Keep native window decorations (title bar with minimize/maximize/close buttons)
        # Platform-specific window handling
        if IS_WINDOWS:
            # Keep native window decorations on Windows
            pass
        elif IS_MACOS:
            # On macOS, use native window decorations for best integration
            # Don't override redirect to maintain proper macOS behavior
            pass
        else:
            # On Linux, skip window override to avoid focus issues
            # Keep native window decorations for better compatibility
            pass

  
        # Set window styles
        self.set_window_style()

        # Path for storing API keys persistently
        self.config_dir = Path.home() / ".claude_ez_switch"
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        
        # Path for Claude Code settings.json
        self.claude_settings_dir = Path.home() / ".claude"
        self.claude_settings_file = self.claude_settings_dir / "settings.json"
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Color scheme
        self.bg_color = "#1e1e1e"
        self.fg_color = "#ffffff"
        self.accent_color = "#007acc"
        self.radio_orange_color = "#FFB366"  # Lighter orange for radio buttons
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
                       font=font_manager.get_font(22, 'bold'))
        style.configure('Subtitle.TLabel', background=self.bg_color, foreground=self.fg_color,
                       font=font_manager.get_font(13))
        style.configure('TLabel', background=self.bg_color, foreground=self.fg_color,
                       font=font_manager.get_font(10))

        # Linux-specific radio button styling - use custom approach for larger indicators
        if IS_LINUX:
            # Custom radio button variables and storage
            self.custom_radio_buttons = {}
            # Don't use ttk radio buttons on Linux - we'll create custom ones
        else:
            style.configure('TRadiobutton', background=self.bg_color, foreground=self.fg_color,
                           font=font_manager.get_font(10))
            style.map('TRadiobutton', background=[('active', self.bg_color)])

        # Linux-specific combobox styling for larger dropdown arrow
        if IS_LINUX:
            # Keep the original theme but enhance combobox visibility
            style.configure('TCombobox',
                           fieldbackground=self.entry_bg,
                           background=self.entry_bg,
                           foreground=self.fg_color,
                           arrowsize=25,  # Much larger arrow for better visibility
                           padding=(8, 4),  # More padding
                           borderwidth=1,
                           relief="solid")
            style.map('TCombobox',
                     background=[('readonly', self.entry_bg), ('active', "#5a5a5a")],
                     fieldbackground=[('readonly', self.entry_bg)],
                     arrowcolor=[('readonly', self.fg_color), ('active', "#ffffff")])

            # Linux-specific checkbox styling for better visibility
            style.configure('TCheckbutton', background=self.bg_color, foreground=self.fg_color,
                           font=font_manager.get_font(12),  # Larger font
                           padding=(10, 6))  # More padding
            style.map('TCheckbutton', background=[('active', self.bg_color)])
        
        self.create_widgets()
        self.load_saved_api_keys()
        self.load_existing_api_keys()
        # Update UI to match loaded configuration
        self.on_config_change()
        self.on_claude_mode_change()
        self.check_current_status()
        
        # Set up focus management for Linux
        if IS_LINUX:
            # Schedule focus setup after window is fully displayed
            self.root.after(1000, self.setup_linux_focus)

    def set_window_style(self):
        """Set window styles for borderless window with shadow (platform-specific)"""
        if IS_WINDOWS and WIN32_AVAILABLE:
            try:
                # Get the window handle
                hwnd = self.root.winfo_id()
                if hwnd == 0:
                    # Window not yet created, try again later
                    self.root.after(100, self.set_window_style)
                    return

                # Set window styles for borderless window with shadow
                style = c_int(win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE))
                style.value |= win32con.WS_EX_APPWINDOW | win32con.WS_EX_TOOLWINDOW
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style.value)

                # Add window shadow
                try:
                    windll.dwmapi.DwmSetWindowAttribute(hwnd, 2, byref(c_int(2)), 4)
                except:
                    # DWM might not be available, continue without shadow
                    pass

            except Exception:
                pass
        elif IS_LINUX:
            # On Linux, be more careful with window decorations to avoid display issues
            try:
                # Check if we successfully removed decorations earlier
                if self.root.overrideredirect():
                    # Try to set some window manager hints for better integration
                    try:
                        self.root.attributes('-type', 'dialog')
                        self.root.attributes('-topmost', False)
                        # Try to enable window compositing for better visuals
                        self.root.tk.call('tkwait', 'visibility', self.root._w)
                    except:
                        pass
                else:
                    # If we have window decorations, try to make them minimal
                    try:
                        self.root.attributes('-toolpalette', True)
                    except:
                        pass
            except Exception:
                pass
        elif IS_MACOS:
            # On macOS, ensure proper window behavior and appearance
            try:
                # macOS-specific window attributes for better integration
                self.root.attributes('-alpha', 1.0)  # Ensure full opacity
                self.root.attributes('-topmost', False)
                # Try to disable window animations for smoother experience
                try:
                    self.root.tk.call('tk::mac::standardAboutPanel')
                except:
                    pass
            except Exception:
                pass
        else:
            # For other platforms, just use basic borderless mode
            pass

    
    def minimize_window(self):
        """Minimize the window by hiding it and showing a restore notification"""
        try:
            # Simple approach: hide the window and show a notification
            self.root.withdraw()

            # Schedule the restore notification to run after the window is hidden
            self.root.after(200, self._show_minimize_notification)
        except Exception:
            pass
            # Fallback: try to at least hide the window
            try:
                self.root.withdraw()
            except:
                pass

    def _show_minimize_notification(self):
        """Show a notification that the app is minimized"""
        try:
            # Create a small restore dialog
            self.restore_dialog = tk.Toplevel()
            self.restore_dialog.title("")
            self.restore_dialog.geometry("300x120")
            self.restore_dialog.resizable(False, False)

            # Center the restore dialog
            self.restore_dialog.update_idletasks()
            x = (self.restore_dialog.winfo_screenwidth() // 2) - (150)
            y = (self.restore_dialog.winfo_screenheight() // 2) - (60)
            self.restore_dialog.geometry(f'+{x}+{y}')

            # Style the restore dialog
            self.restore_dialog.configure(bg=self.bg_color)

            # Add content
            title_label = tk.Label(self.restore_dialog, text="Application Minimized",
                                 bg=self.bg_color, fg=self.fg_color,
                                 font=font_manager.get_font(12, 'bold'))
            title_label.pack(pady=(15, 5))

            info_label = tk.Label(self.restore_dialog, text="Claude Code EZ Switch is running in the background",
                                bg=self.bg_color, fg=self.fg_color,
                                font=font_manager.get_font(9))
            info_label.pack(pady=(0, 10))

            restore_button = tk.Button(self.restore_dialog, text="Restore Window",
                                     bg=self.button_bg, fg=self.fg_color,
                                     font=font_manager.get_font(10, 'bold'),
                                     relief=tk.FLAT, bd=0, pady=8,
                                     command=self._restore_from_notification,
                                     cursor="hand2")
            restore_button.pack(pady=(0, 15))

            # Bind hover effects
            restore_button.bind('<Enter>', lambda e: restore_button.configure(bg=self.button_hover))
            restore_button.bind('<Leave>', lambda e: restore_button.configure(bg=self.button_bg))

            # Make the dialog stay on top
            self.restore_dialog.attributes('-topmost', True)

            # Handle window close
            self.restore_dialog.protocol("WM_DELETE_WINDOW", self._restore_from_notification)

        except Exception:
            pass
            # If dialog creation fails, just restore the main window
            self._restore_main_window()

    def _restore_from_notification(self):
        """Restore the main window from the notification"""
        try:
            # Close the restore dialog if it exists
            if hasattr(self, 'restore_dialog') and self.restore_dialog:
                self.restore_dialog.destroy()
                self.restore_dialog = None

            # Restore the main window
            self._restore_main_window()
        except Exception:
            pass
            self._restore_main_window()

    def _restore_main_window(self):
        """Restore the main window to its original state"""
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        except Exception:
            pass

    def close_window(self):
        """Close the window"""
        self.close_application()
        
    def create_widgets(self):
        # Main container with slightly more padding since we don't have custom title bar
        main_frame = tk.Frame(self.root, bg=self.bg_color, padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Content frame (everything except footer)
        content_frame = tk.Frame(main_frame, bg=self.bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Message area (hidden by default)
        self.message_frame = tk.Frame(content_frame, bg=self.entry_bg, relief=tk.RAISED, bd=1)
        self.message_label = tk.Label(self.message_frame, bg=self.entry_bg, fg=self.fg_color,
                                  font=font_manager.get_font(10), wraplength=400, justify=tk.LEFT)
        self.message_label.pack(padx=15, pady=10)
        
        # Close button for message
        self.message_close_btn = tk.Button(self.message_frame, text="✕", bg=self.close_button_bg, fg=self.fg_color,
                                      font=font_manager.get_font(8), relief=tk.FLAT, cursor="hand2",
                                      bd=0, width=2, height=1, command=self.hide_message)
        self.message_close_btn.place(relx=0.98, rely=0.02, anchor='ne')
        
        # Modern Logo Container
        logo_container = tk.Frame(content_frame, bg=self.bg_color)
        logo_container.pack(pady=(0, 15))

        # Logo frame with styling
        logo_frame = tk.Frame(logo_container, bg=self.bg_color)
        logo_frame.pack()

        # Orange code symbol
        code_symbol = tk.Label(logo_frame, text="</>", bg=self.bg_color, fg="#FF8C00",
                             font=font_manager.get_font(28, 'bold'))
        code_symbol.pack(side=tk.LEFT, padx=(0, 8))

        claude_code_label = tk.Label(logo_frame, text="Claude Code", bg=self.bg_color, fg="#FF8C00",
                                   font=font_manager.get_font(28, 'bold'))
        claude_code_label.pack(side=tk.LEFT)

        ez_switch_label = tk.Label(logo_frame, text=" EZ Switch", bg=self.bg_color, fg=self.fg_color,
                                 font=font_manager.get_font(28, 'bold'))
        ez_switch_label.pack(side=tk.LEFT)

        # Modern separation line
        separator_frame = tk.Frame(logo_container, bg=self.bg_color)
        separator_frame.pack(pady=(8, 5))

        # Create gradient effect with multiple lines
        separator_top = tk.Frame(separator_frame, bg="#FF8C00", height=2)
        separator_top.pack(fill=tk.X, padx=50)

        separator_middle = tk.Frame(separator_frame, bg="#FFA500", height=1)
        separator_middle.pack(fill=tk.X, padx=70, pady=1)

        separator_bottom = tk.Frame(separator_frame, bg="#FFB84D", height=1)
        separator_bottom.pack(fill=tk.X, padx=90)

        # Subtitle with modern styling
        subtitle_label = ttk.Label(logo_container,
                                   text="Switch between z.ai and custom configurations",
                                   style='Subtitle.TLabel')
        subtitle_label.pack(pady=(5, 0))
        
        # Current Status Frame
        status_frame = tk.Frame(content_frame, bg=self.entry_bg, relief=tk.FLAT, bd=0)
        status_frame.pack(fill=tk.X, pady=(0, 20), padx=2)
        
        status_title = ttk.Label(status_frame, text="Current Status:",
                                font=font_manager.get_font(13, 'bold'))
        status_title.pack(anchor=tk.W, padx=15, pady=(15, 10))

        self.status_label = tk.Label(status_frame, text="Checking...",
                                     bg=self.entry_bg, fg=self.fg_color,
                                     font=font_manager.get_font(12, 'bold'), anchor=tk.W, justify=tk.LEFT)
        self.status_label.pack(anchor=tk.W, padx=15, pady=(0, 15), fill=tk.X)
        
        # Loading indicator (hidden by default)
        self.loading_frame = tk.Frame(status_frame, bg=self.entry_bg)
        self.loading_label = tk.Label(self.loading_frame, text="⟳ Applying configuration...",
                                     bg=self.entry_bg, fg=self.accent_color,
                                     font=font_manager.get_font(12, 'bold'), anchor=tk.W)
        self.loading_label.pack(side=tk.LEFT, padx=15)
        
        self.progress_bar = ttk.Progressbar(self.loading_frame, mode='indeterminate', length=200)
        self.progress_bar.pack(side=tk.LEFT, padx=10)
        
        # Configuration Selection
        config_label = ttk.Label(content_frame, text="Select Configuration:",
                                font=font_manager.get_font(11, 'bold'))
        config_label.pack(anchor=tk.W, pady=(0, 10))
        
        self.config_var = tk.StringVar(value="zai")
        
        # Configuration radio buttons container
        radio_container = tk.Frame(content_frame, bg=self.bg_color)
        radio_container.pack(fill=tk.X, pady=(0, 10))

        if IS_LINUX:
            # Create custom radio buttons for Linux with larger indicators
            self.create_custom_radio_button(radio_container, "Z.ai", "zai")
            self.create_custom_radio_button(radio_container, "Claude", "claude")
            self.create_custom_radio_button(radio_container, "Custom", "custom")
        else:
            # Use standard ttk radio buttons for other platforms
            # Create radio buttons horizontally
            zai_radio = ttk.Radiobutton(radio_container, text="Z.ai",
                                       variable=self.config_var, value="zai",
                                       command=self.on_config_change, style='TRadiobutton')
            zai_radio.pack(side=tk.LEFT, padx=(0, 20))

            claude_radio = ttk.Radiobutton(radio_container, text="Claude",
                                         variable=self.config_var, value="claude",
                                         command=self.on_config_change, style='TRadiobutton')
            claude_radio.pack(side=tk.LEFT, padx=(0, 20))

            custom_radio = ttk.Radiobutton(radio_container, text="Custom",
                                          variable=self.config_var, value="custom",
                                          command=self.on_config_change, style='TRadiobutton')
            custom_radio.pack(side=tk.LEFT)
        
        # Dynamic configuration container (where different configs will be shown)
        self.dynamic_config_container = tk.Frame(content_frame, bg=self.bg_color)
        self.dynamic_config_container.pack(fill=tk.BOTH, expand=False)
        
        # Create all configuration frames but don't pack them yet
        self.create_zai_frame()
        self.create_claude_frame()
        self.create_custom_frame()

        # Show/Hide Password Checkbutton
        self.show_password_var = tk.BooleanVar()
        show_password_check = tk.Checkbutton(content_frame, text="Show API Keys",
                                           variable=self.show_password_var,
                                           command=self.toggle_password_visibility,
                                           bg=self.bg_color, fg=self.fg_color,
                                           selectcolor=self.bg_color,
                                           activebackground=self.bg_color,
                                           activeforeground=self.fg_color,
                                           highlightthickness=0, bd=0,
                                           font=font_manager.get_font(9 if not IS_LINUX else 11),
                                           padx=5, pady=5)
        show_password_check.pack(anchor=tk.W, pady=(10, 0))

        # Show Claude Settings Checkbutton
        self.show_env_vars_var = tk.BooleanVar()
        show_env_vars_check = tk.Checkbutton(content_frame, text="Show Claude Settings",
                                           variable=self.show_env_vars_var,
                                           command=self.toggle_env_vars_visibility,
                                           bg=self.bg_color, fg=self.fg_color,
                                           selectcolor=self.bg_color,
                                           activebackground=self.bg_color,
                                           activeforeground=self.fg_color,
                                           highlightthickness=0, bd=0,
                                           font=font_manager.get_font(9 if not IS_LINUX else 11),
                                           padx=5, pady=5)
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
                                      activebackground=self.button_bg, activeforeground=self.fg_color,
                                      font=font_manager.get_font(11, 'bold'), relief=tk.FLAT,
                                      cursor="hand2", bd=0, pady=12,
                                      command=self.apply_configuration)
        self.apply_button.grid(row=0, column=0, columnspan=2, sticky="ew", padx=(0, 5), pady=(0, 8))
        
        # Hover effects removed
        
        # Refresh Status Button
        self.refresh_button = tk.Button(button_container, text="Refresh",
                                       bg=self.refresh_button_bg, fg=self.fg_color,
                                       activebackground=self.refresh_button_bg, activeforeground=self.fg_color,
                                       font=font_manager.get_font(10, 'bold'), relief=tk.FLAT,
                                       cursor="hand2", bd=0, pady=12,
                                       command=self.check_current_status)
        self.refresh_button.grid(row=0, column=2, sticky="ew", padx=(5, 0), pady=(0, 8))
        
        # Hover effects removed
        
        # Close Button (spans all columns)
        self.close_button = tk.Button(button_container, text="Close Application",
                                     bg=self.close_button_bg, fg=self.fg_color,
                                     activebackground=self.close_button_bg, activeforeground=self.fg_color,
                                     font=font_manager.get_font(10), relief=tk.FLAT,
                                     cursor="hand2", bd=0, pady=10,
                                     command=self.close_application)
        self.close_button.grid(row=1, column=0, columnspan=3, sticky="ew")
        
        # Hover effects removed
        
        # Universal Claude Settings Display (hidden by default)
        self.universal_settings_frame = tk.Frame(main_frame, bg=self.entry_bg)

        # Hide button for universal settings
        universal_hide_frame = tk.Frame(self.universal_settings_frame, bg=self.entry_bg)
        universal_hide_frame.pack(fill=tk.X, padx=15, pady=(10, 5))

        universal_hide_btn = tk.Button(universal_hide_frame, text="✕ Hide Settings",
                                       bg=self.close_button_bg, fg=self.fg_color,
                                       font=font_manager.get_font(9, 'bold'), relief=tk.FLAT,
                                       cursor="hand2", bd=0, pady=5,
                                       command=self.hide_universal_settings)
        universal_hide_btn.pack(side=tk.RIGHT)

        # Create grid layout for settings display
        universal_settings_container = tk.Frame(self.universal_settings_frame, bg=self.entry_bg)
        universal_settings_container.pack(fill=tk.X, padx=15, pady=(0, 10))

        # Settings title
        settings_title = tk.Label(universal_settings_container, text="Current Claude Code Settings:",
                                 bg=self.entry_bg, fg=self.accent_color,
                                 font=font_manager.get_font(10, 'bold'), anchor=tk.W)
        settings_title.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 8))

        # Define all possible ANTHROPIC variables to display
        universal_env_vars = [
            ('ANTHROPIC_AUTH_TOKEN', 'Authentication Token'),
            ('ANTHROPIC_BASE_URL', 'Base URL'),
            ('ANTHROPIC_DEFAULT_OPUS_MODEL', 'Default Opus Model'),
            ('ANTHROPIC_DEFAULT_SONNET_MODEL', 'Default Sonnet Model'),
            ('ANTHROPIC_DEFAULT_HAIKU_MODEL', 'Default Haiku Model'),
            ('ANTHROPIC_API_KEY', 'API Key'),
            ('API_TIMEOUT_MS', 'API Timeout (ms)')
        ]

        # Create labels for each variable
        self.universal_value_labels = {}
        for i, (var_name, display_name) in enumerate(universal_env_vars, start=1):
            # Variable name label
            var_label = tk.Label(universal_settings_container, text=f"{display_name}:",
                               bg=self.entry_bg, fg=self.fg_color,
                               font=font_manager.get_font(9), anchor=tk.W)
            var_label.grid(row=i, column=0, sticky=tk.W, pady=(2, 2))

            # Value label
            value_label = tk.Label(universal_settings_container, text="Not set",
                                 bg=self.entry_bg, fg="#888888",
                                 font=font_manager.get_font(9, 'italic'), anchor=tk.W)
            value_label.grid(row=i, column=1, sticky=tk.W, padx=(10, 0), pady=(2, 2))

            self.universal_value_labels[var_name] = value_label

        # Note at the bottom
        note_label = tk.Label(universal_settings_container,
                            text="Note: These settings are stored in ~/.claude/settings.json",
                            bg=self.entry_bg, fg="#888888",
                            font=font_manager.get_font(8, "italic"), anchor=tk.W)
        note_label.grid(row=len(universal_env_vars) + 1, column=0, columnspan=2, sticky=tk.W, pady=(8, 0))

        # Footer
        footer_frame = tk.Frame(main_frame, bg=self.bg_color)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(20, 10))
        
        footer_text = "Claude Code EZ Switch is open source under the MIT license"
        footer_label = tk.Label(footer_frame, text=footer_text,
                              bg=self.bg_color, fg="#888888",
                              font=font_manager.get_font(8))
        footer_label.pack()
        
        # GitHub link
        github_link = tk.Label(footer_frame, text="Source Code",
                              bg=self.bg_color, fg=self.accent_color,
                              font=font_manager.get_font(8), cursor="hand2")
        github_link.pack()
        github_link.bind("<Button-1>", lambda e: self.open_github_link())
    
    def create_custom_radio_button(self, parent, text, value):
        """Create a custom radio button with larger indicator for Linux"""
        # Create frame for the radio button
        radio_frame = tk.Frame(parent, bg=self.bg_color)
        radio_frame.pack(side=tk.LEFT, padx=(0, 20))

        # Create canvas for drawing the radio button circle
        canvas_size = 24  # Larger than default
        canvas = tk.Canvas(radio_frame, width=canvas_size, height=canvas_size,
                          bg=self.bg_color, highlightthickness=0, bd=0)
        canvas.pack(side=tk.LEFT, padx=(0, 10))

        # Draw the radio button circle (outer ring)
        outer_circle = canvas.create_oval(2, 2, canvas_size-2, canvas_size-2,
                                        outline=self.fg_color, width=3)

        # Draw the inner circle (filled when selected)
        inner_circle = canvas.create_oval(8, 8, canvas_size-8, canvas_size-8,
                                        fill="", outline="")

        # Create the text label
        label = tk.Label(radio_frame, text=text, bg=self.bg_color, fg=self.fg_color,
                        font=font_manager.get_font(11),  # Smaller font size for radio button text
                        bd=0, relief=tk.FLAT, highlightthickness=0)

        # Force background color to override any theme defaults
        label.configure(bg=self.bg_color)

        label.pack(side=tk.LEFT, padx=0, pady=5)

        # Determine which variable and callback to use
        if value in ['subscription', 'api']:
            # Claude mode radio buttons
            var_name = 'claude_mode_var'
            callback = self.on_claude_mode_change
        else:
            # Config radio buttons (zai, claude, custom)
            var_name = 'config_var'
            callback = self.on_config_change

        # Store radio button info
        self.custom_radio_buttons[value] = {
            'canvas': canvas,
            'outer_circle': outer_circle,
            'inner_circle': inner_circle,
            'label': label,
            'selected': False,
            'var_name': var_name,
            'callback': callback
        }

        # Bind click events
        for widget in [canvas, label, radio_frame]:
            widget.bind('<Button-1>', lambda e, val=value: self.on_custom_radio_click(val))
            widget.bind('<Enter>', lambda e, val=value: self.on_custom_radio_hover(val, True))
            widget.bind('<Leave>', lambda e, val=value: self.on_custom_radio_hover(val, False))

        # Set initial selection if this is the default value
        variable = getattr(self, var_name)
        if variable.get() == value:
            self.update_custom_radio_display(value, True)

    def on_custom_radio_click(self, value):
        """Handle custom radio button click"""
        if value not in self.custom_radio_buttons:
            return

        radio_info = self.custom_radio_buttons[value]
        var_name = radio_info['var_name']
        callback = radio_info['callback']

        # Update the appropriate variable
        variable = getattr(self, var_name)
        variable.set(value)

        # Update all radio button displays
        for radio_value in self.custom_radio_buttons:
            self.update_custom_radio_display(radio_value, radio_value == value)

        # Trigger the appropriate callback
        callback()

    def update_custom_radio_display(self, value, is_selected):
        """Update the visual display of a custom radio button"""
        if value not in self.custom_radio_buttons:
            return

        radio_info = self.custom_radio_buttons[value]
        radio_info['selected'] = is_selected

        canvas = radio_info['canvas']
        inner_circle = radio_info['inner_circle']

        if is_selected:
            # Fill the inner circle and change text color
            # Use lighter orange for all radio buttons
            color = self.radio_orange_color
            canvas.itemconfig(inner_circle, fill=color)
            canvas.itemconfig(radio_info['outer_circle'], outline=color)
            radio_info['label'].config(fg=color)
        else:
            # Clear the inner circle and reset text color
            canvas.itemconfig(inner_circle, fill="")
            canvas.itemconfig(radio_info['outer_circle'], outline=self.fg_color)
            radio_info['label'].config(fg=self.fg_color)

    def on_custom_radio_hover(self, value, is_hovering):
        """Handle hover effect for custom radio buttons"""
        if value not in self.custom_radio_buttons:
            return

        radio_info = self.custom_radio_buttons[value]
        canvas = radio_info['canvas']

        if not radio_info['selected']:  # Only apply hover if not selected
            if is_hovering:
                # Use lighter orange for all radio buttons
                color = self.radio_orange_color
                canvas.itemconfig(radio_info['outer_circle'], outline=color)
            else:
                canvas.itemconfig(radio_info['outer_circle'], outline=self.fg_color)

    def on_entry_click(self, event):
        """Handle entry field click to ensure proper focus on Linux"""
        widget = event.widget
        # Ensure the widget can receive focus and input
        widget.focus_set()
        widget.focus_force()
        # Make sure the widget is enabled and can receive input
        if widget.cget('state') == tk.DISABLED:
            widget.configure(state=tk.NORMAL)
        # Ensure the cursor is visible and positioned correctly
        widget.icursor(tk.END)
    
    def setup_linux_focus(self):
        """Set up proper focus handling for Linux"""
        try:
            # Enhanced focus setup for Linux to ensure input fields work
            if hasattr(self, 'zai_key_entry'):
                # Set up all entry fields for proper focus
                entry_fields = [
                    self.zai_key_entry,
                    self.zai_key_name_entry,
                    self.claude_key_entry,
                    self.custom_url_entry,
                    self.custom_key_entry
                ]
                
                for entry in entry_fields:
                    if entry:
                        # Ensure entry is enabled and can receive focus
                        if entry.cget('state') == tk.DISABLED:
                            entry.configure(state=tk.NORMAL)
                        # Set focus and ensure cursor is at end
                        entry.focus_set()
                        entry.icursor(tk.END)
                        # Bind additional events to ensure focus works
                        entry.bind('<FocusIn>', lambda e, widget=entry: widget.icursor(tk.END))
                        entry.bind('<Button-1>', lambda e, widget=entry: self._ensure_entry_focus(widget))
                        
                # Set initial focus to zai_key_entry after a short delay
                self.root.after(200, lambda: self._ensure_entry_focus(self.zai_key_entry))
                 
        except Exception:
            pass
    
    def _ensure_entry_focus(self, entry):
        """Helper method to ensure an entry field has proper focus"""
        try:
            if entry and entry.winfo_exists():
                # Make sure entry is enabled
                if entry.cget('state') == tk.DISABLED:
                    entry.configure(state=tk.NORMAL)
                # Set focus and move cursor to end
                entry.focus_set()
                entry.focus_force()
                entry.icursor(tk.END)
                # Make sure the window is active
                self.root.lift()
                self.root.focus_force()
        except Exception:
            pass
    
    def create_zai_frame(self):
        """Create Z.ai configuration frame"""
        self.zai_frame = tk.LabelFrame(self.dynamic_config_container, text="", bg=self.entry_bg,
                                 fg=self.fg_color, relief=tk.FLAT, bd=2)

        # Key selection section
        key_select_label = ttk.Label(self.zai_frame, text="Select Saved Z.ai Key:")
        key_select_label.pack(anchor=tk.W, padx=15, pady=(10, 2))

        # Frame for key selection and management
        key_management_frame = tk.Frame(self.zai_frame, bg=self.entry_bg)
        key_management_frame.pack(fill=tk.X, padx=15, pady=(0, 5))

        # Combobox for selecting existing keys
        self.zai_key_var = tk.StringVar()
        if IS_LINUX:
            combobox_width = 32  # Make it larger on Linux for better visibility
        else:
            combobox_width = 40
        self.zai_key_combo = ttk.Combobox(key_management_frame, textvariable=self.zai_key_var,
                                          state="readonly", width=combobox_width)
        self.zai_key_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.zai_key_combo.bind('<<ComboboxSelected>>', self.on_zai_key_selected)

        # Add/Delete buttons
        button_frame = tk.Frame(key_management_frame, bg=self.entry_bg)
        button_frame.pack(side=tk.RIGHT)

        add_key_btn = tk.Button(button_frame, text="+", bg=self.refresh_button_bg, fg=self.fg_color,
                                activebackground=self.refresh_button_bg, activeforeground=self.fg_color,
                                font=font_manager.get_font(10, 'bold'), relief=tk.FLAT, cursor="hand2",
                                bd=0, width=3, command=self.add_zai_key)
        add_key_btn.pack(side=tk.LEFT, padx=(0, 2))

        delete_key_btn = tk.Button(button_frame, text="−", bg="#8b4513", fg=self.fg_color,
                                   activebackground="#8b4513", activeforeground=self.fg_color,
                                   font=font_manager.get_font(10, 'bold'), relief=tk.FLAT, cursor="hand2",
                                   bd=0, width=3, command=self.delete_zai_key)
        delete_key_btn.pack(side=tk.LEFT)

        # Current key entry
        zai_key_label = ttk.Label(self.zai_frame, text="Current Z.ai API Key:")
        zai_key_label.pack(anchor=tk.W, padx=15, pady=(10, 2))

        self.zai_key_entry = tk.Entry(self.zai_frame, bg=self.entry_bg, fg=self.fg_color,
                                      insertbackground=self.fg_color, relief=tk.FLAT,
                                      font=font_manager.get_font(10), bd=0, show="*")
        self.zai_key_entry.pack(fill=tk.X, padx=15, pady=(0, 2), ipady=8)
        
        # Bind focus events for proper input handling
        self.zai_key_entry.bind('<Button-1>', self.on_entry_click)

        # Add border to entry
        entry_border = tk.Frame(self.zai_frame, bg=self.accent_color, height=2)
        entry_border.pack(fill=tk.X, padx=15, pady=(0, 5))

        # Key name entry
        key_name_label = ttk.Label(self.zai_frame, text="Key Name (for saving):")
        key_name_label.pack(anchor=tk.W, padx=15, pady=(5, 2))

        self.zai_key_name_entry = tk.Entry(self.zai_frame, bg=self.entry_bg, fg=self.fg_color,
                                           insertbackground=self.fg_color, relief=tk.FLAT,
                                           font=font_manager.get_font(10), bd=0)
        self.zai_key_name_entry.pack(fill=tk.X, padx=15, pady=(0, 2), ipady=8)
        
        # Bind focus events for proper input handling
        self.zai_key_name_entry.bind('<Button-1>', self.on_entry_click)

        # Add border to key name entry
        name_border = tk.Frame(self.zai_frame, bg=self.accent_color, height=2)
        name_border.pack(fill=tk.X, padx=15, pady=(0, 10))

        # Save current key button
        save_key_btn = tk.Button(self.zai_frame, text="Save Current Key",
                                bg=self.refresh_button_bg, fg=self.fg_color,
                                activebackground=self.refresh_button_bg, activeforeground=self.fg_color,
                                font=font_manager.get_font(9, 'bold'), relief=tk.FLAT,
                                cursor="hand2", bd=0, pady=8,
                                command=self.save_current_zai_key)
        save_key_btn.pack(fill=tk.X, padx=15, pady=(0, 10))

        # Model selection section
        model_selection_label = ttk.Label(self.zai_frame, text="Model Selection:")
        model_selection_label.pack(anchor=tk.W, padx=15, pady=(10, 5))

        # Create a frame for model selection dropdowns
        model_frame = tk.Frame(self.zai_frame, bg=self.entry_bg)
        model_frame.pack(fill=tk.X, padx=15, pady=(0, 10))

        # Define available GLM models
        self.available_models = ["GLM-4.7", "GLM-4.6", "GLM-4.5", "GLM-4.5-Air"]

        # Opus Model Selection
        opus_label = ttk.Label(model_frame, text="Opus Model:")
        opus_label.grid(row=0, column=0, sticky=tk.W, pady=(2, 5))

        self.zai_opus_model_var = tk.StringVar(value="GLM-4.7")
        self.zai_opus_combo = ttk.Combobox(model_frame, textvariable=self.zai_opus_model_var,
                                           values=self.available_models, state="readonly", width=20)
        self.zai_opus_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=(2, 5))

        # Sonnet Model Selection
        sonnet_label = ttk.Label(model_frame, text="Sonnet Model:")
        sonnet_label.grid(row=1, column=0, sticky=tk.W, pady=(2, 5))

        self.zai_sonnet_model_var = tk.StringVar(value="GLM-4.7")
        self.zai_sonnet_combo = ttk.Combobox(model_frame, textvariable=self.zai_sonnet_model_var,
                                             values=self.available_models, state="readonly", width=20)
        self.zai_sonnet_combo.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(2, 5))

        # Haiku Model Selection
        haiku_label = ttk.Label(model_frame, text="Haiku Model:")
        haiku_label.grid(row=2, column=0, sticky=tk.W, pady=(2, 5))

        self.zai_haiku_model_var = tk.StringVar(value="GLM-4.7")
        self.zai_haiku_combo = ttk.Combobox(model_frame, textvariable=self.zai_haiku_model_var,
                                            values=self.available_models, state="readonly", width=20)
        self.zai_haiku_combo.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=(2, 5))

        # Bind combobox changes to update function
        self.zai_opus_combo.bind('<<ComboboxSelected>>', lambda e: self.update_zai_env_display())
        self.zai_sonnet_combo.bind('<<ComboboxSelected>>', lambda e: self.update_zai_env_display())
        self.zai_haiku_combo.bind('<<ComboboxSelected>>', lambda e: self.update_zai_env_display())

        # Initialize storage for multiple keys
        self.zai_keys = {}  # Format: {"name": "key"}
        self.current_zai_key_name = None

        # Environment variables display (hidden by default)
        self.zai_env_frame = tk.Frame(self.zai_frame, bg=self.entry_bg)

        # Hide button for z.ai environment variables
        zai_hide_frame = tk.Frame(self.zai_env_frame, bg=self.entry_bg)
        zai_hide_frame.pack(fill=tk.X, padx=15, pady=(10, 5))

        zai_hide_btn = tk.Button(zai_hide_frame, text="✕ Hide Settings",
                                bg=self.close_button_bg, fg=self.fg_color,
                                font=font_manager.get_font(9, 'bold'), relief=tk.FLAT,
                                cursor="hand2", bd=0, pady=5,
                                command=lambda: self.hide_env_vars('zai'))
        zai_hide_btn.pack(side=tk.RIGHT)
        zai_hide_btn.bind('<Enter>', lambda e: zai_hide_btn.configure(bg=self.close_button_hover))
        zai_hide_btn.bind('<Leave>', lambda e: zai_hide_btn.configure(bg=self.close_button_bg))

        # Create a nice grid layout for environment variables
        zai_env_container = tk.Frame(self.zai_env_frame, bg=self.entry_bg)
        zai_env_container.pack(fill=tk.X, padx=15, pady=(0, 10))

        # Environment variables title
        env_title = tk.Label(zai_env_container, text="Environment Variables Set:",
                            bg=self.bg_color, fg="#cccccc",
                            font=font_manager.get_font(11, 'bold'), anchor=tk.W)
        env_title.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 8))

        # Environment variables data
        zai_env_vars = [
            ("ANTHROPIC_AUTH_TOKEN", "<your-zai-api-key>", "User level"),
            ("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic", "User level"),
            ("ANTHROPIC_DEFAULT_OPUS_MODEL", "GLM-4.6", "User level"),
            ("ANTHROPIC_DEFAULT_SONNET_MODEL", "GLM-4.6", "User level"),
            ("ANTHROPIC_DEFAULT_HAIKU_MODEL", "GLM-4.6", "User level")
        ]

        # Initialize dictionary to store value label references
        self.zai_env_value_labels = {}

        for i, (var_name, var_value, var_level) in enumerate(zai_env_vars, 1):
            # Variable name
            name_label = tk.Label(zai_env_container, text=var_name + ":",
                                bg=self.entry_bg, fg="#ffffff",
                                font=font_manager.get_font(9, 'bold'), anchor=tk.W)
            name_label.grid(row=i, column=0, sticky=tk.W, padx=(0, 10), pady=(0, 4))

            # Variable value - store reference for later updates
            value_label = tk.Label(zai_env_container, text=var_value,
                                  bg=self.entry_bg, fg="#aaaaaa",
                                  font=("Consolas", 9), anchor=tk.W)
            value_label.grid(row=i, column=1, sticky=tk.W, pady=(0, 4))

            # Store reference to this value label
            self.zai_env_value_labels[var_name] = value_label

        # Note at the bottom
        note_label = tk.Label(zai_env_container,
                            text="Note: All variables set at User level - no admin rights required",
                            bg=self.entry_bg, fg="#888888",
                            font=font_manager.get_font(8, "italic"), anchor=tk.W)
        note_label.grid(row=len(zai_env_vars) + 1, column=0, columnspan=2, sticky=tk.W, pady=(8, 0))

    def create_claude_frame(self):
        """Create Claude configuration frame"""
        self.claude_frame = tk.LabelFrame(self.dynamic_config_container, text="", bg=self.entry_bg,
                                     fg=self.fg_color, relief=tk.FLAT, bd=2)

        self.claude_mode_var = tk.StringVar(value="subscription")

        # Create a container for radio buttons to ensure proper vertical layout
        radio_container = tk.Frame(self.claude_frame, bg=self.entry_bg)
        radio_container.pack(fill=tk.X, padx=15, pady=(10, 5))

        if IS_LINUX:
            # Create custom radio buttons for Linux for Claude mode selection
            # Reset custom radio buttons for Claude context
            self.claude_radio_buttons = {}
            self.create_claude_custom_radio_button(radio_container, "Use Claude Subscription (Pro/Team/Enterprise)", "subscription")
            # Create a frame to force layout to stack vertically
            tk.Frame(radio_container, bg=self.entry_bg, height=5).pack(fill=tk.X)
            self.create_claude_custom_radio_button(radio_container, "Use Claude API Key", "api")
        else:
            # Use standard ttk radio buttons for other platforms
            subscription_radio = ttk.Radiobutton(radio_container, text="Use Claude Subscription (Pro/Team/Enterprise)",
                                                variable=self.claude_mode_var, value="subscription",
                                                command=self.on_claude_mode_change, style='TRadiobutton')
            subscription_radio.pack(anchor=tk.W, pady=(0, 5))

            api_radio = ttk.Radiobutton(radio_container, text="Use Claude API Key",
                                        variable=self.claude_mode_var, value="api",
                                        command=self.on_claude_mode_change, style='TRadiobutton')
            api_radio.pack(anchor=tk.W, pady=(0, 5))

        # Add spacing before the API key input field
        tk.Frame(self.claude_frame, bg=self.entry_bg, height=10).pack(fill=tk.X, padx=15, pady=(10, 0))

        claude_key_label = ttk.Label(self.claude_frame, text="Claude API Key:")
        claude_key_label.pack(anchor=tk.W, padx=15, pady=(5, 2))

        self.claude_key_entry = tk.Entry(self.claude_frame, bg=self.entry_bg, fg=self.fg_color,
                                         insertbackground=self.fg_color, relief=tk.FLAT,
                                         font=font_manager.get_font(10), bd=0, show="*", state=tk.DISABLED,
                                         disabledbackground=self.entry_bg, disabledforeground="#888888")
        self.claude_key_entry.pack(fill=tk.X, padx=15, pady=(0, 2), ipady=8)

        # Bind focus events for proper input handling
        self.claude_key_entry.bind('<Button-1>', self.on_entry_click)
        self.claude_key_entry.bind('<KeyRelease>', lambda e: self.save_api_keys())

        # Add border to entry
        claude_entry_border = tk.Frame(self.claude_frame, bg=self.accent_color, height=2)
        claude_entry_border.pack(fill=tk.X, padx=15, pady=(0, 10))

        # Initialize custom radio button display for Linux
        if IS_LINUX:
            self.root.after(100, self.update_claude_radio_display)

    def create_claude_custom_radio_button(self, parent, text, value):
        """Create a custom radio button for Claude that stacks vertically"""
        # Create frame for the radio button that stacks vertically
        radio_frame = tk.Frame(parent, bg=self.entry_bg)
        radio_frame.pack(fill=tk.X, pady=2)

        # Create canvas for drawing the radio button circle
        canvas_size = 24  # Larger than default
        canvas = tk.Canvas(radio_frame, width=canvas_size, height=canvas_size,
                          bg=self.entry_bg, highlightthickness=0, bd=0)
        canvas.pack(side=tk.LEFT, padx=(0, 10))

        # Draw the radio button circle (outer ring)
        outer_circle = canvas.create_oval(2, 2, canvas_size-2, canvas_size-2,
                                        outline=self.fg_color, width=3)

        # Draw the inner circle (filled when selected)
        inner_circle = canvas.create_oval(8, 8, canvas_size-8, canvas_size-8,
                                        fill="", outline="")

        # Create the text label
        label = tk.Label(radio_frame, text=text, bg=self.entry_bg, fg=self.fg_color,
                        font=font_manager.get_font(11),  # Smaller font size for radio button text
                        bd=0, relief=tk.FLAT, highlightthickness=0)

        # Force background color to override any theme defaults
        label.configure(bg=self.entry_bg)

        label.pack(side=tk.LEFT, padx=0, pady=5)

        # Store radio button info for Claude context
        self.claude_radio_buttons[value] = {
            'canvas': canvas,
            'outer_circle': outer_circle,
            'inner_circle': inner_circle,
            'label': label,
            'selected': False,
            'radio_frame': radio_frame
        }

        # Bind click events to all parts of the radio button
        for widget in [canvas, label, radio_frame]:
            widget.bind('<Button-1>', lambda e, val=value: self.on_claude_custom_radio_click(val))
            widget.bind('<Enter>', lambda e, val=value: self.on_claude_custom_radio_hover(val, True))
            widget.bind('<Leave>', lambda e, val=value: self.on_claude_custom_radio_hover(val, False))

        # Set initial selection for subscription mode
        if value == "subscription":
            self.update_claude_custom_radio_display(value, True)

    def on_claude_custom_radio_click(self, value):
        """Handle Claude custom radio button click"""
        if value not in self.claude_radio_buttons:
            return

        # Update the variable
        self.claude_mode_var.set(value)

        # Update all radio button displays
        for radio_value in self.claude_radio_buttons:
            self.update_claude_custom_radio_display(radio_value, radio_value == value)

        # Call the original change handler
        self.on_claude_mode_change()

    def update_claude_custom_radio_display(self, value, is_selected):
        """Update the visual display of a Claude custom radio button"""
        if value not in self.claude_radio_buttons:
            return

        radio_info = self.claude_radio_buttons[value]
        radio_info['selected'] = is_selected

        canvas = radio_info['canvas']
        inner_circle = radio_info['inner_circle']

        if is_selected:
            # Fill the inner circle and change color
            canvas.itemconfig(inner_circle, fill=self.radio_orange_color, outline="")
            # Use lighter orange for all radio buttons
            color = self.radio_orange_color
            canvas.itemconfig(radio_info['outer_circle'], outline=color)
            radio_info['label'].config(fg=color)
        else:
            # Empty the inner circle
            canvas.itemconfig(inner_circle, fill="", outline="")
            canvas.itemconfig(radio_info['outer_circle'], outline=self.fg_color)
            radio_info['label'].config(fg=self.fg_color)

    def on_claude_custom_radio_hover(self, value, is_hovering):
        """Handle hover effect for Claude custom radio buttons"""
        if value not in self.claude_radio_buttons:
            return

        radio_info = self.claude_radio_buttons[value]
        canvas = radio_info['canvas']

        if not radio_info['selected']:  # Only apply hover if not selected
            if is_hovering:
                # Use lighter orange for all radio buttons
                color = self.radio_orange_color
                canvas.itemconfig(radio_info['outer_circle'], outline=color)
            else:
                canvas.itemconfig(radio_info['outer_circle'], outline=self.fg_color)

    def update_claude_radio_display(self):
        """Update Claude radio button display for Linux"""
        if IS_LINUX and hasattr(self, 'claude_radio_buttons'):
            # Set initial selection for subscription mode
            if self.claude_mode_var.get() == "subscription":
                self.update_claude_custom_radio_display("subscription", True)
                self.update_claude_custom_radio_display("api", False)
            else:
                self.update_claude_custom_radio_display("subscription", False)
                self.update_claude_custom_radio_display("api", True)

    def on_claude_mode_change(self):
        """Handle Claude mode radio button change"""
        if self.claude_mode_var.get() == "api":
            self.claude_key_entry.configure(state=tk.NORMAL)
        else:
            self.claude_key_entry.configure(state=tk.DISABLED)

    def create_custom_frame(self):
        """Create Custom configuration frame"""
        self.custom_frame = tk.LabelFrame(self.dynamic_config_container, text="", bg=self.entry_bg,
                                    fg=self.fg_color, relief=tk.FLAT, bd=2)

        custom_url_label = ttk.Label(self.custom_frame, text="Custom Base URL:")
        custom_url_label.pack(anchor=tk.W, padx=15, pady=(10, 2))

        self.custom_url_entry = tk.Entry(self.custom_frame, bg=self.entry_bg, fg=self.fg_color,
                                         insertbackground=self.fg_color, relief=tk.FLAT,
                                         font=font_manager.get_font(10), bd=0)
        self.custom_url_entry.pack(fill=tk.X, padx=15, pady=(0, 2), ipady=8)
        
        # Enhanced focus events for proper input handling
        self.custom_url_entry.bind('<Button-1>', self.on_entry_click)
        self.custom_url_entry.bind('<FocusIn>', lambda e: self.custom_url_entry.icursor(tk.END))
        # Remove the problematic Key binding that was preventing input

        # Add border to entry
        custom_url_border = tk.Frame(self.custom_frame, bg=self.accent_color, height=2)
        custom_url_border.pack(fill=tk.X, padx=15, pady=(0, 5))

        custom_key_label = ttk.Label(self.custom_frame, text="Custom API Key:")
        custom_key_label.pack(anchor=tk.W, padx=15, pady=(5, 2))

        self.custom_key_entry = tk.Entry(self.custom_frame, bg=self.entry_bg, fg=self.fg_color,
                                         insertbackground=self.fg_color, relief=tk.FLAT,
                                         font=font_manager.get_font(10), bd=0, show="*")
        self.custom_key_entry.pack(fill=tk.X, padx=15, pady=(0, 2), ipady=8)
        
        # Enhanced focus events for proper input handling
        self.custom_key_entry.bind('<Button-1>', self.on_entry_click)
        self.custom_key_entry.bind('<FocusIn>', lambda e: self.custom_key_entry.icursor(tk.END))
        # Remove the problematic Key binding that was preventing input

        # Add border to entry
        custom_key_border = tk.Frame(self.custom_frame, bg=self.accent_color, height=2)
        custom_key_border.pack(fill=tk.X, padx=15, pady=(0, 10))

        # Environment variables display (hidden by default)
        self.custom_env_frame = tk.Frame(self.custom_frame, bg=self.entry_bg)

        # Hide button for custom environment variables
        custom_hide_frame = tk.Frame(self.custom_env_frame, bg=self.entry_bg)
        custom_hide_frame.pack(fill=tk.X, padx=15, pady=(10, 5))

        custom_hide_btn = tk.Button(custom_hide_frame, text="✕ Hide Settings",
                                    bg=self.close_button_bg, fg=self.fg_color,
                                    font=font_manager.get_font(9, 'bold'), relief=tk.FLAT,
                                    cursor="hand2", bd=0, pady=5,
                                    command=lambda: self.hide_env_vars('custom'))
        custom_hide_btn.pack(side=tk.RIGHT)
        custom_hide_btn.bind('<Enter>', lambda e: custom_hide_btn.configure(bg=self.close_button_hover))
        custom_hide_btn.bind('<Leave>', lambda e: custom_hide_btn.configure(bg=self.close_button_bg))

        # Create a nice grid layout for environment variables
        custom_env_container = tk.Frame(self.custom_env_frame, bg=self.entry_bg)
        custom_env_container.pack(fill=tk.X, padx=15, pady=(0, 10))

        # Environment variables title
        env_title = tk.Label(custom_env_container, text="Environment Variables Set:",
                            bg=self.bg_color, fg="#cccccc",
                            font=font_manager.get_font(11, 'bold'), anchor=tk.W)
        env_title.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 8))

        # Environment variables data
        custom_env_vars = [
            ("ANTHROPIC_AUTH_TOKEN", "<your-custom-api-key>", "User level"),
            ("ANTHROPIC_BASE_URL", "<your-custom-base-url>", "User level")
        ]

        # Initialize dictionary to store value label references
        self.custom_env_value_labels = {}

        for i, (var_name, var_value, var_level) in enumerate(custom_env_vars, 1):
            # Variable name
            name_label = tk.Label(custom_env_container, text=var_name + ":",
                                bg=self.entry_bg, fg="#ffffff",
                                font=font_manager.get_font(9, 'bold'), anchor=tk.W)
            name_label.grid(row=i, column=0, sticky=tk.W, padx=(0, 10), pady=(0, 4))

            # Variable value - store reference for later updates
            value_label = tk.Label(custom_env_container, text=var_value,
                                  bg=self.entry_bg, fg="#aaaaaa",
                                  font=("Consolas", 9), anchor=tk.W)
            value_label.grid(row=i, column=1, sticky=tk.W, pady=(0, 4))

            # Store reference to this value label
            self.custom_env_value_labels[var_name] = value_label

        # Note at the bottom
        note_label = tk.Label(custom_env_container,
                            text="Note: Only basic auth token and base URL are set at User level",
                            bg=self.entry_bg, fg="#888888",
                            font=font_manager.get_font(8, "italic"), anchor=tk.W)
        note_label.grid(row=len(custom_env_vars) + 1, column=0, columnspan=2, sticky=tk.W, pady=(8, 0))

        # Bind events to save API keys when they change
        self.zai_key_entry.bind('<KeyRelease>', lambda e: self.on_zai_key_changed())
        self.custom_key_entry.bind('<KeyRelease>', lambda e: self.save_api_keys())
        self.custom_url_entry.bind('<KeyRelease>', lambda e: self.save_api_keys())
    
    def load_existing_api_keys(self):
        """Load existing API keys from Claude Code settings.json and pre-fill them"""
        try:
            # Get settings from Claude Code settings.json
            settings = self.get_claude_settings()

            if 'env' not in settings:
                return

            env_vars = settings['env']
            user_auth_token = env_vars.get('ANTHROPIC_AUTH_TOKEN', '').strip()
            user_base_url = env_vars.get('ANTHROPIC_BASE_URL', '').strip()

            # Only update fields if they're empty AND if the settings are explicitly set
            # Don't pre-fill anything if using subscription (no settings)

            # Pre-fill z.ai key only if it's set and base_url explicitly points to z.ai
            if user_auth_token and user_base_url and 'z.ai' in user_base_url:
                if not self.zai_key_entry.get().strip():
                    self.zai_key_entry.delete(0, tk.END)
                    self.zai_key_entry.insert(0, user_auth_token)

            # Pre-fill Claude API key only if auth token is set but no base URL (indicating API mode)
            elif user_auth_token and not user_base_url:
                if not self.claude_key_entry.get().strip():
                    self.claude_key_entry.delete(0, tk.END)
                    self.claude_key_entry.insert(0, user_auth_token)

            # Pre-fill custom configuration only if both auth token and base URL are set and it's not z.ai
            elif user_auth_token and user_base_url and user_base_url and 'z.ai' not in user_base_url:
                if not self.custom_url_entry.get().strip():
                    self.custom_url_entry.delete(0, tk.END)
                    self.custom_url_entry.insert(0, user_base_url)

                if not self.custom_key_entry.get().strip():
                    self.custom_key_entry.delete(0, tk.END)
                    self.custom_key_entry.insert(0, user_auth_token)

            # Load model settings if z.ai configuration is detected
            if user_auth_token and user_base_url and 'z.ai' in user_base_url:
                self.load_model_settings(env_vars)

        except Exception:
            # Silently fail if we can't load keys
            pass

    def load_model_settings(self, env_vars):
        """Load model settings from environment variables and update dropdowns"""
        try:
            # Get current model settings from environment variables
            opus_model = env_vars.get('ANTHROPIC_DEFAULT_OPUS_MODEL', '').strip()
            sonnet_model = env_vars.get('ANTHROPIC_DEFAULT_SONNET_MODEL', '').strip()
            haiku_model = env_vars.get('ANTHROPIC_DEFAULT_HAIKU_MODEL', '').strip()

            # Define available models (matching the existing available_models list)
            available_models = ["GLM-4.6", "GLM-4.5", "GLM-4.5-Air"]

            # Update opus model dropdown if model is valid
            if opus_model and opus_model in available_models:
                self.zai_opus_model_var.set(opus_model)

            # Update sonnet model dropdown if model is valid
            if sonnet_model and sonnet_model in available_models:
                self.zai_sonnet_model_var.set(sonnet_model)

            # Update haiku model dropdown if model is valid
            if haiku_model and haiku_model in available_models:
                self.zai_haiku_model_var.set(haiku_model)

            # Update the environment display to show the loaded models
            self.update_zai_env_display()

        except Exception:
            # Silently fail if we can't load model settings
            pass

    
    
    def get_claude_settings(self):
        """Get current Claude Code settings.json content"""
        try:
            if self.claude_settings_file.exists():
                with open(self.claude_settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Return empty settings if file doesn't exist
                return {}
        except (FileNotFoundError, PermissionError) as e:
            # Log file access errors but don't crash the app
            print(f"Warning: Could not access Claude settings file {self.claude_settings_file}: {e}")
            return {}
        except json.JSONDecodeError as e:
            # Log JSON parsing errors
            print(f"Warning: Invalid JSON in Claude settings file {self.claude_settings_file}: {e}")
            return {}
        except UnicodeDecodeError as e:
            # Log encoding errors
            print(f"Warning: Encoding error reading Claude settings file {self.claude_settings_file}: {e}")
            # Try with different encoding as fallback
            try:
                with open(self.claude_settings_file, 'r', encoding='utf-8-sig') as f:
                    return json.load(f)
            except Exception:
                print(f"Warning: Could not read Claude settings file with any encoding")
                return {}
        except Exception as e:
            # Log any other unexpected errors
            print(f"Warning: Unexpected error reading Claude settings file {self.claude_settings_file}: {e}")
            return {}

    def update_claude_settings(self, env_vars):
        """Update Claude Code settings.json with environment variables"""
        try:
            # Ensure .claude directory exists
            self.claude_settings_dir.mkdir(exist_ok=True)

            # Read current settings
            current_settings = self.get_claude_settings()

            # Update or add environment variables
            if 'env' not in current_settings:
                current_settings['env'] = {}

            for var_name, var_value in env_vars.items():
                current_settings['env'][var_name] = var_value

            # Write back to file with proper formatting
            with open(self.claude_settings_file, 'w', encoding='utf-8') as f:
                json.dump(current_settings, f, indent=4, ensure_ascii=False)

            return True, f"Claude Code settings updated successfully"

        except Exception as e:
            return False, f"Failed to update Claude settings: {str(e)}"

    def remove_claude_settings_vars(self, var_names):
        """Remove specific environment variables from Claude Code settings.json"""
        try:
            # Read current settings
            current_settings = self.get_claude_settings()

            # Check if there are environment variables to remove
            if 'env' not in current_settings:
                return True, "No environment variables in Claude settings to remove"

            # Remove specified variables
            removed_vars = []
            for var_name in var_names:
                if var_name in current_settings['env']:
                    del current_settings['env'][var_name]
                    removed_vars.append(var_name)

            # If no variables were removed, return early
            if not removed_vars:
                return True, "No matching environment variables found in Claude settings"

            # Write updated settings back to file
            with open(self.claude_settings_file, 'w', encoding='utf-8') as f:
                json.dump(current_settings, f, indent=4, ensure_ascii=False)

            return True, f"Removed {', '.join(removed_vars)} from Claude Code settings"

        except Exception as e:
            return False, f"Failed to remove from Claude settings: {str(e)}"

    
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
            
            # Load z.ai keys (new format)
            if 'zai_keys' in saved_keys:
                self.zai_keys = saved_keys['zai_keys']
                self.update_zai_key_combo()
            elif 'zai_key' in saved_keys:
                # Migrate old single key format
                old_key = saved_keys['zai_key']
                self.zai_keys = {'Default': old_key}
                self.update_zai_key_combo()
                self.zai_key_var.set('Default')
                self.on_zai_key_selected()

            # Load current z.ai key name
            if 'current_zai_key_name' in saved_keys:
                self.current_zai_key_name = saved_keys['current_zai_key_name']
                if self.current_zai_key_name and self.current_zai_key_name in self.zai_keys:
                    self.zai_key_var.set(self.current_zai_key_name)
                    self.on_zai_key_selected()
            
            
    # Load Claude config
            if 'claude_mode' in saved_keys:
                self.claude_mode_var.set(saved_keys['claude_mode'])
                self.on_claude_mode_change()

            if 'claude_key' in saved_keys:
                self.claude_key_entry.delete(0, tk.END)
                self.claude_key_entry.insert(0, saved_keys['claude_key'])

            # Load custom config
            if 'custom_url' in saved_keys:
                self.custom_url_entry.delete(0, tk.END)
                self.custom_url_entry.insert(0, saved_keys['custom_url'])

            if 'custom_key' in saved_keys:
                self.custom_key_entry.delete(0, tk.END)
                self.custom_key_entry.insert(0, saved_keys['custom_key'])


            # Always default to Z.ai configuration
            self.config_var.set("zai")

            # Update radio button display to match default config
            if IS_LINUX and hasattr(self, 'custom_radio_buttons'):
                for radio_value in self.custom_radio_buttons:
                    self.update_custom_radio_display(radio_value, radio_value == "zai")
        except Exception as e:
            # Silently fail if we can't load saved keys
            pass
    
    def save_api_keys(self):
        """Save current API keys to persistent storage"""
        try:
            saved_keys = {}
            
           # Save z.ai keys
            saved_keys['zai_keys'] = self.zai_keys
            saved_keys['current_zai_key_name'] = self.current_zai_key_name

            # Save Claude config
            saved_keys['claude_mode'] = self.claude_mode_var.get()
            claude_key = self.claude_key_entry.get().strip()
            if claude_key:
                saved_keys['claude_key'] = claude_key

            # Save custom config if not empty
            custom_url = self.custom_url_entry.get().strip()
            if custom_url:
                saved_keys['custom_url'] = custom_url

            custom_key = self.custom_key_entry.get().strip()
            if custom_key:
                saved_keys['custom_key'] = custom_key


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
    
    def on_zai_key_selected(self, event=None):
        """Handle z.ai key selection from combobox"""
        selected_name = self.zai_key_var.get()
        if selected_name and selected_name in self.zai_keys:
            self.zai_key_entry.delete(0, tk.END)
            self.zai_key_entry.insert(0, self.zai_keys[selected_name])
            self.zai_key_name_entry.delete(0, tk.END)
            self.zai_key_name_entry.insert(0, selected_name)
            self.current_zai_key_name = selected_name

    def on_zai_key_changed(self):
        """Handle when z.ai key entry is changed"""
        # Mark current selection as none since key was manually changed
        self.current_zai_key_name = None
        self.save_api_keys()

    def update_zai_env_display(self):
        """Update the environment variables display to show selected models"""
        if hasattr(self, 'zai_env_value_labels'):
            # Update the model values in the display
            self.zai_env_value_labels["ANTHROPIC_DEFAULT_OPUS_MODEL"].config(
                text=self.zai_opus_model_var.get())
            self.zai_env_value_labels["ANTHROPIC_DEFAULT_SONNET_MODEL"].config(
                text=self.zai_sonnet_model_var.get())
            self.zai_env_value_labels["ANTHROPIC_DEFAULT_HAIKU_MODEL"].config(
                text=self.zai_haiku_model_var.get())

    def add_zai_key(self):
        """Add a new z.ai key"""
        key_name = self.zai_key_name_entry.get().strip()
        key_value = self.zai_key_entry.get().strip()

        if not key_name:
            self.show_inline_message("Error: Please enter a name for this key", "error")
            return

        if not key_value:
            self.show_inline_message("Error: Please enter a key value", "error")
            return

        if key_name in self.zai_keys:
            # Use inline confirmation
            self.show_inline_message(f"Warning: Key '{key_name}' already exists. Overwrite?", "warning")
            self._show_confirmation_buttons(lambda: self._perform_add_key(key_name, key_value), key_name)
        else:
            self._perform_add_key(key_name, key_value)

    def _perform_add_key(self, key_name, key_value):
        """Perform the actual addition of the key"""
        # Save the key
        self.zai_keys[key_name] = key_value
        self.current_zai_key_name = key_name

        # Update combobox
        self.update_zai_key_combo()
        self.zai_key_var.set(key_name)

        # Save to persistent storage
        self.save_api_keys()

        # Show success message
        self.show_inline_message(f"Z.ai key '{key_name}' saved successfully!", "success")

    def delete_zai_key(self):
        """Delete the selected z.ai key"""
        selected_name = self.zai_key_var.get()

        if not selected_name or selected_name not in self.zai_keys:
            self.show_inline_message("Error: Please select a key to delete", "error")
            return

        # Use inline confirmation on all platforms for consistency
        self.show_inline_message(f"Delete key '{selected_name}'? Click Yes to confirm or No to cancel.", "confirmation")
        
        # Add confirmation buttons
        self._show_confirmation_buttons(lambda: self._perform_delete(selected_name), selected_name)

    def _show_confirmation_buttons(self, on_yes_callback, selected_name):
        """Show inline confirmation buttons"""
        # Remove existing buttons if any
        if hasattr(self, 'confirm_button_frame'):
            self.confirm_button_frame.destroy()

        # Create button frame
        self.confirm_button_frame = tk.Frame(self.message_frame, bg=self.entry_bg)
        self.confirm_button_frame.pack(pady=(5, 0))

        # Adjust window height to accommodate confirmation buttons
        self._adjust_window_height_for_confirmation()
        
        # Yes button
        yes_btn = tk.Button(self.confirm_button_frame, text="Yes", bg=self.button_bg, fg=self.fg_color,
                           font=font_manager.get_font(9, 'bold'), relief=tk.FLAT, cursor="hand2",
                           bd=0, padx=15, pady=5, command=lambda: self._confirm_action(on_yes_callback))
        yes_btn.pack(side=tk.LEFT, padx=(0, 10))
        yes_btn.bind('<Enter>', lambda e: yes_btn.configure(bg=self.button_hover))
        yes_btn.bind('<Leave>', lambda e: yes_btn.configure(bg=self.button_bg))
        
        # No button
        no_btn = tk.Button(self.confirm_button_frame, text="No", bg=self.close_button_bg, fg=self.fg_color,
                          font=font_manager.get_font(9, 'bold'), relief=tk.FLAT, cursor="hand2",
                          bd=0, padx=15, pady=5, command=self._cancel_confirmation)
        no_btn.pack(side=tk.LEFT)
        no_btn.bind('<Enter>', lambda e: no_btn.configure(bg=self.close_button_hover))
        no_btn.bind('<Leave>', lambda e: no_btn.configure(bg=self.close_button_bg))

    def _confirm_action(self, callback):
        """Execute confirmed action"""
        self.hide_message()
        callback()

    def _cancel_confirmation(self):
        """Cancel confirmation and hide message"""
        self.hide_message()

    def _perform_delete(self, selected_name):
        """Perform the actual deletion of the key"""
        del self.zai_keys[selected_name]

        # Clear entries if this was the current key
        if self.current_zai_key_name == selected_name:
            self.zai_key_entry.delete(0, tk.END)
            self.zai_key_name_entry.delete(0, tk.END)
            self.current_zai_key_name = None

        # Clean up environment variables and Claude Code settings
        self._cleanup_api_key_configuration()

        # Update combobox
        self.update_zai_key_combo()

        # Save to persistent storage
        self.save_api_keys()

        # Show success message
        self.show_inline_message(f"Z.ai key '{selected_name}' deleted successfully!", "success")

    def _cleanup_api_key_configuration(self):
        """Clean up API key configuration from settings.json"""
        try:
            # All ANTHROPIC-related variables that might be set
            cleanup_vars = [
                'ANTHROPIC_AUTH_TOKEN',
                'ANTHROPIC_BASE_URL',
                'ANTHROPIC_DEFAULT_OPUS_MODEL',
                'ANTHROPIC_DEFAULT_SONNET_MODEL',
                'ANTHROPIC_DEFAULT_HAIKU_MODEL',
                'ANTHROPIC_API_KEY',
                'API_TIMEOUT_MS'
            ]

            # Remove from Claude Code settings
            self.remove_claude_settings_vars(cleanup_vars)

        except Exception:
            pass

    def show_inline_message(self, message, message_type="info"):
        """Show an inline message in the UI"""
        # Set message color based on type
        if message_type == "error":
            fg_color = self.error_color
            icon = "⚠ "
        elif message_type == "success":
            fg_color = self.success_color
            icon = "✓ "
        elif message_type == "warning":
            fg_color = "#ff9800"
            icon = "⚠ "
        else:  # confirmation
            fg_color = self.fg_color
            icon = "? "
        
        # Update message label
        self.message_label.configure(text=icon + message, fg=fg_color)
        
        # Show message frame
        self.message_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Auto-hide success messages after 3 seconds
        if message_type == "success":
            self.root.after(3000, self.hide_message)

    def hide_message(self):
        """Hide the inline message"""
        # Remove confirmation buttons if they exist
        if hasattr(self, 'confirm_button_frame'):
            self.confirm_button_frame.destroy()
            delattr(self, 'confirm_button_frame')

        # Restore original window height if it was increased for confirmation
        self._restore_original_window_height()

        # Hide message frame
        self.message_frame.pack_forget()

    def _adjust_window_height_for_confirmation(self):
        """Increase window height to accommodate confirmation buttons"""
        try:
            # Store original geometry if not already stored
            if not hasattr(self, 'original_geometry'):
                self.original_geometry = self.root.geometry()

            # Get current window dimensions
            current_geometry = self.root.geometry()
            current_width, current_height = map(int, current_geometry.split('+')[0].split('x'))
            x, y = map(int, current_geometry.split('+')[1:3])

            # Add extra height for confirmation buttons (approximately 60 pixels)
            extra_height = 60
            new_height = current_height + extra_height

            # Check if we're exceeding screen height
            screen_height = self.root.winfo_screenheight()
            max_height = screen_height - 100  # Leave some margin

            if new_height > max_height:
                new_height = max_height

            # Apply new geometry
            self.root.geometry(f'{current_width}x{new_height}+{x}+{y}')

            # Ensure the window is fully visible
            if y + new_height > screen_height - 50:
                y = screen_height - new_height - 50
                self.root.geometry(f'{current_width}x{new_height}+{x}+{y}')

        except Exception:
            pass

    def _restore_original_window_height(self):
        """Restore the original window height after confirmation is hidden"""
        try:
            if hasattr(self, 'original_geometry'):
                # Restore original geometry
                self.root.geometry(self.original_geometry)
                # Remove the stored geometry
                delattr(self, 'original_geometry')
        except Exception:
            pass

    def _adjust_window_height_for_env_vars(self):
        """Increase window size to accommodate environment variables display"""
        try:
            # Store original geometry if not already stored
            if not hasattr(self, 'original_geometry'):
                self.original_geometry = self.root.geometry()

            # Get current window dimensions
            current_geometry = self.root.geometry()
            current_width, current_height = map(int, current_geometry.split('+')[0].split('x'))
            x, y = map(int, current_geometry.split('+')[1:3])

            # Add extra height for environment variables (approximately 200 pixels)
            extra_height = 200
            new_height = current_height + extra_height

            # Add extra width to prevent text cutoff (approximately 250 pixels for better visibility)
            extra_width = 250
            new_width = current_width + extra_width

            # Check if we're exceeding screen dimensions
            screen_height = self.root.winfo_screenheight()
            screen_width = self.root.winfo_screenwidth()
            max_height = screen_height - 100  # Leave some margin
            max_width = screen_width - 100  # Leave some margin

            if new_height > max_height:
                new_height = max_height

            if new_width > max_width:
                new_width = max_width

            # Apply new geometry
            self.root.geometry(f'{new_width}x{new_height}+{x}+{y}')

            # Ensure the window is fully visible
            if y + new_height > screen_height - 50:
                y = screen_height - new_height - 50
            if x + new_width > screen_width - 50:
                x = screen_width - new_width - 50

            self.root.geometry(f'{new_width}x{new_height}+{x}+{y}')

        except Exception:
            pass

    def show_non_modal_confirmation(self, title, message, on_yes_callback):
        """Show a non-modal confirmation dialog that works better on Linux"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x150")
        dialog.resizable(False, False)
        
        # Make dialog transient and grab focus
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Style the dialog to match the main app
        dialog.configure(bg=self.bg_color)
        
        # Center the dialog relative to the main window
        self.root.update_idletasks()
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()
        
        dialog_x = main_x + (main_width // 2) - 200
        dialog_y = main_y + (main_height // 2) - 75
        
        dialog.geometry(f"+{dialog_x}+{dialog_y}")
        
        # Multiple approaches to ensure dialog visibility on Linux
        if IS_LINUX:
            # Set window type to dialog for better window manager integration
            try:
                dialog.attributes('-type', 'dialog')
            except:
                pass
            
            # Force dialog to top
            dialog.lift()
            dialog.attributes('-topmost', True)
            
            # Focus the dialog
            dialog.focus_set()
            dialog.focus_force()
            
            # Ensure dialog is visible
            dialog.deiconify()
            dialog.update()
            
            # Schedule additional focus attempts
            dialog.after(50, lambda: dialog.lift())
            dialog.after(100, lambda: dialog.focus_force())
            dialog.after(200, lambda: dialog.attributes('-topmost', False))
        else:
            dialog.lift()
            dialog.attributes('-topmost', True)
        
        # Message label
        msg_label = tk.Label(dialog, text=message, bg=self.bg_color, fg=self.fg_color,
                           font=font_manager.get_font(11), wraplength=350, justify=tk.CENTER)
        msg_label.pack(pady=20)
        
        # Button frame
        button_frame = tk.Frame(dialog, bg=self.bg_color)
        button_frame.pack(pady=10)
        
        # Yes button
        yes_btn = tk.Button(button_frame, text="Yes", bg=self.button_bg, fg=self.fg_color,
                           font=font_manager.get_font(10, 'bold'), relief=tk.FLAT, cursor="hand2",
                           bd=0, padx=20, pady=8,
                           command=lambda: self._close_confirmation_dialog(dialog, on_yes_callback))
        yes_btn.pack(side=tk.LEFT, padx=10)
        yes_btn.bind('<Enter>', lambda e: yes_btn.configure(bg=self.button_hover))
        yes_btn.bind('<Leave>', lambda e: yes_btn.configure(bg=self.button_bg))
        
        # No button
        no_btn = tk.Button(button_frame, text="No", bg=self.close_button_bg, fg=self.fg_color,
                          font=font_manager.get_font(10, 'bold'), relief=tk.FLAT, cursor="hand2",
                          bd=0, padx=20, pady=8,
                          command=dialog.destroy)
        no_btn.pack(side=tk.LEFT, padx=10)
        no_btn.bind('<Enter>', lambda e: no_btn.configure(bg=self.close_button_hover))
        no_btn.bind('<Leave>', lambda e: no_btn.configure(bg=self.close_button_bg))
        
        # Handle window close
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)

    def _close_confirmation_dialog(self, dialog, callback):
        """Close confirmation dialog and execute callback"""
        dialog.destroy()
        # Schedule callback to run after dialog is destroyed
        self.root.after(100, callback)

    def show_error_dialog(self, title, message):
        """Show a custom error dialog that works better on Linux"""
        if IS_LINUX:
            self.show_inline_message(message, "error")
        else:
            messagebox.showerror(title, message, parent=self.root)

    def show_success_dialog(self, title, message):
        """Show a custom success dialog with proper formatting for Linux"""
        if IS_LINUX:
            dialog = tk.Toplevel(self.root)
            dialog.title(title)
            # Make dialog significantly larger to account for window decorations
            dialog.geometry("550x420")
            dialog.resizable(False, False)

            # Make dialog transient and grab focus
            dialog.transient(self.root)
            dialog.grab_set()

            # Style the dialog to match the main app
            dialog.configure(bg=self.bg_color)

            # Center the dialog relative to the main window
            self.root.update_idletasks()
            main_x = self.root.winfo_x()
            main_y = self.root.winfo_y()
            main_width = self.root.winfo_width()
            main_height = self.root.winfo_height()

            dialog_x = main_x + (main_width // 2) - 275
            dialog_y = main_y + (main_height // 2) - 210

            dialog.geometry(f"+{dialog_x}+{dialog_y}")

            # Multiple approaches to ensure dialog visibility on Linux
            try:
                dialog.attributes('-type', 'dialog')
            except:
                pass

            dialog.lift()
            dialog.attributes('-topmost', True)
            dialog.focus_set()
            dialog.focus_force()
            dialog.deiconify()
            dialog.update()

            dialog.after(50, lambda: dialog.lift())
            dialog.after(100, lambda: dialog.focus_force())
            dialog.after(200, lambda: dialog.attributes('-topmost', False))

            # Main container with generous padding to ensure content fits
            main_container = tk.Frame(dialog, bg=self.bg_color)
            main_container.pack(fill=tk.BOTH, expand=True, padx=35, pady=35)

            # Success icon
            icon_label = tk.Label(main_container, text="✓", bg=self.bg_color, fg=self.success_color,
                                font=font_manager.get_font(26, 'bold'))
            icon_label.pack(pady=(0, 18))

            # Message label with proper wrapping and better contrast
            msg_label = tk.Label(main_container, text=message, bg=self.bg_color, fg="#ffffff",
                               font=font_manager.get_font(10), wraplength=470, justify=tk.CENTER)
            msg_label.pack(pady=(0, 25))

            # Ensure the message is clearly visible by updating it after packing
            msg_label.update_idletasks()

            # Button frame
            button_frame = tk.Frame(main_container, bg=self.bg_color)
            button_frame.pack()

            # OK button
            ok_btn = tk.Button(button_frame, text="OK", bg=self.button_bg, fg=self.fg_color,
                             font=font_manager.get_font(10, 'bold'), relief=tk.FLAT, cursor="hand2",
                             bd=0, padx=30, pady=10, command=dialog.destroy)
            ok_btn.pack()
            ok_btn.bind('<Enter>', lambda e: ok_btn.configure(bg=self.button_hover))
            ok_btn.bind('<Leave>', lambda e: ok_btn.configure(bg=self.button_bg))

            # Handle window close
            dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        else:
            messagebox.showinfo(title, message, parent=self.root)

    def show_info_dialog(self, title, message):
        """Show a custom info dialog that works better on Linux"""
        if IS_LINUX:
            self.show_inline_message(message, "success")
        else:
            messagebox.showinfo(title, message, parent=self.root)

    def show_non_modal_dialog(self, title, message, dialog_type="info"):
        """Show a non-modal dialog that works better on Linux"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x120")
        dialog.resizable(False, False)
        
        # Make dialog transient and grab focus
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Style the dialog to match the main app
        dialog.configure(bg=self.bg_color)
        
        # Center the dialog relative to the main window
        self.root.update_idletasks()
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()
        
        dialog_x = main_x + (main_width // 2) - 200
        dialog_y = main_y + (main_height // 2) - 60
        
        dialog.geometry(f"+{dialog_x}+{dialog_y}")
        
        # Multiple approaches to ensure dialog visibility on Linux
        if IS_LINUX:
            # Set window type to dialog for better window manager integration
            try:
                dialog.attributes('-type', 'dialog')
            except:
                pass
            
            # Force dialog to top
            dialog.lift()
            dialog.attributes('-topmost', True)
            
            # Focus the dialog
            dialog.focus_set()
            dialog.focus_force()
            
            # Ensure dialog is visible
            dialog.deiconify()
            dialog.update()
            
            # Schedule additional focus attempts
            dialog.after(50, lambda: dialog.lift())
            dialog.after(100, lambda: dialog.focus_force())
            dialog.after(200, lambda: dialog.attributes('-topmost', False))
        else:
            dialog.lift()
            dialog.attributes('-topmost', True)
        
        # Icon and message frame
        content_frame = tk.Frame(dialog, bg=self.bg_color)
        content_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        # Icon based on dialog type
        if dialog_type == "error":
            icon_text = "⚠"
            icon_color = "#ff9800"
        else:
            icon_text = "✓"
            icon_color = self.success_color
        
        icon_label = tk.Label(content_frame, text=icon_text, bg=self.bg_color, fg=icon_color,
                            font=font_manager.get_font(24, 'bold'))
        icon_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # Message label
        msg_label = tk.Label(content_frame, text=message, bg=self.bg_color, fg=self.fg_color,
                           font=font_manager.get_font(11), wraplength=300, justify=tk.LEFT)
        msg_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # OK button
        ok_btn = tk.Button(dialog, text="OK", bg=self.button_bg, fg=self.fg_color,
                         font=font_manager.get_font(10, 'bold'), relief=tk.FLAT, cursor="hand2",
                         bd=0, padx=30, pady=8, command=dialog.destroy)
        ok_btn.pack(pady=(0, 15))
        ok_btn.bind('<Enter>', lambda e: ok_btn.configure(bg=self.button_hover))
        ok_btn.bind('<Leave>', lambda e: ok_btn.configure(bg=self.button_bg))
        
        # Handle window close
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)

    def save_current_zai_key(self):
        """Save the current z.ai key with the given name"""
        self.add_zai_key()

    def update_zai_key_combo(self):
        """Update the z.ai key combobox with current keys"""
        key_names = sorted(self.zai_keys.keys())
        self.zai_key_combo['values'] = key_names

        # If no keys exist, clear selection
        if not key_names:
            self.zai_key_var.set("")
            self.current_zai_key_name = None

    def on_config_change(self):
        """Handle configuration radio button change - switch visible frame"""
        # Hide all frames first
        self.zai_frame.pack_forget()
        self.claude_frame.pack_forget()
        self.custom_frame.pack_forget()
        # Also hide old environment variable frames
        self.zai_env_frame.pack_forget()
        self.custom_env_frame.pack_forget()

        # Show the selected frame
        if self.config_var.get() == "zai":
            self.zai_frame.pack(fill=tk.X, pady=(0, 10))
        elif self.config_var.get() == "claude":
            self.claude_frame.pack(fill=tk.X, pady=(0, 10))
        elif self.config_var.get() == "custom":
            self.custom_frame.pack(fill=tk.X, pady=(0, 10))

        # If Claude settings are currently visible, update them
        if self.show_env_vars_var.get():
            # Schedule update after widgets are properly packed
            self.root.after(100, self.update_universal_settings_display)
    
        
    def toggle_password_visibility(self):
        """Toggle password visibility in entry fields"""
        if self.show_password_var.get():
            self.zai_key_entry.configure(show="")
            self.claude_key_entry.configure(show="")
            self.custom_key_entry.configure(show="")
        else:
            self.zai_key_entry.configure(show="*")
            self.claude_key_entry.configure(show="*")
            self.custom_key_entry.configure(show="*")

        # Update universal settings display if visible
        if self.show_env_vars_var.get():
            self.update_universal_settings_display()

    def hide_universal_settings(self):
        """Hide universal Claude settings display"""
        self.universal_settings_frame.pack_forget()

        # Always uncheck the main checkbox when hiding settings
        # since the user explicitly clicked the hide button
        self.show_env_vars_var.set(False)
        # Restore original window height when settings are hidden
        self._restore_original_window_height()

    def hide_env_vars(self, config_type):
        """Hide settings display for a specific configuration type"""
        if config_type == 'zai':
            self.zai_env_frame.pack_forget()
        elif config_type == 'custom':
            self.custom_env_frame.pack_forget()

        # Always uncheck the main checkbox when hiding environment variables
        # since the user explicitly clicked the hide button
        self.show_env_vars_var.set(False)
        # Restore original window height when env vars are hidden
        self._restore_original_window_height()

    def toggle_env_vars_visibility(self):
        """Toggle Claude settings display visibility"""
        if self.show_env_vars_var.get():
            # Show universal settings frame (regardless of configuration)
            self.universal_settings_frame.pack(fill=tk.X, pady=(0, 10))

            # Update the display with current settings values
            # Try multiple times to ensure the update works
            self.root.after(50, self.update_universal_settings_display)
            self.root.after(150, self.update_universal_settings_display)
            self.root.after(300, self.update_universal_settings_display)  # Final retry

            # Adjust window height to accommodate settings display
            self.root.after(200, self._adjust_window_height_for_env_vars)  # Allow widgets to render first
        else:
            # Hide universal settings frame
            self.universal_settings_frame.pack_forget()

            # Restore original window height
            self._restore_original_window_height()

    def get_current_env_vars(self):
        """Get current environment variables from Claude Code settings.json"""
        env_vars = {}
        try:
            # Get settings from Claude Code settings.json
            settings = self.get_claude_settings()

            # Debug: Print the raw settings for troubleshooting
            if IS_WINDOWS and settings:
                print(f"Debug: Loaded Claude settings: {list(settings.keys())}")
                if 'env' in settings:
                    print(f"Debug: Found env vars: {list(settings['env'].keys())}")

            # Extract environment variables from settings
            if 'env' in settings:
                env_vars = {k: v for k, v in settings['env'].items() if v}

        except Exception as e:
            print(f"Warning: Error getting current environment variables: {e}")

        return env_vars

    def update_env_vars_display(self):
        """Update the environment variables display with current settings.json values"""
        env_vars = self.get_current_env_vars()

        # Update z.ai environment variables if that frame is visible
        if self.config_var.get() == "zai" and hasattr(self, 'zai_env_value_labels'):
            for var_name, label in self.zai_env_value_labels.items():
                value = env_vars.get(var_name, "Not set")

                # Mask sensitive values for display
                # Fix: Use proper parentheses to ensure correct logic evaluation
                if (('AUTH_TOKEN' in var_name or 'API_KEY' in var_name) and value != "Not set"):
                    if len(value) > 8:
                        display_value = f"{value[:4]}...{value[-4:]}"
                    else:
                        display_value = "***"
                else:
                    display_value = value

                label.configure(text=display_value)

        # Update custom environment variables if that frame is visible
        if self.config_var.get() == "custom" and hasattr(self, 'custom_env_value_labels'):
            for var_name, label in self.custom_env_value_labels.items():
                value = env_vars.get(var_name, "Not set")

                # Mask sensitive values for display
                # Fix: Use proper parentheses to ensure correct logic evaluation
                if (('AUTH_TOKEN' in var_name or 'API_KEY' in var_name) and value != "Not set"):
                    if len(value) > 8:
                        display_value = f"{value[:4]}...{value[-4:]}"
                    else:
                        display_value = "***"
                else:
                    display_value = value

                label.configure(text=display_value)

    def update_universal_settings_display(self):
        """Update the universal Claude settings display with current settings.json values"""
        env_vars = self.get_current_env_vars()

        # Debug: Print what we're about to display
        if IS_WINDOWS:
            print(f"Debug: Updating universal display with {len(env_vars)} environment variables")
            print(f"Debug: Universal labels available: {list(self.universal_value_labels.keys())}")

        # Update universal settings display
        for var_name, label in self.universal_value_labels.items():
            value = env_vars.get(var_name, '')

            if value:
                # Debug: Print found values on Windows
                if IS_WINDOWS:
                    print(f"Debug: Found value for {var_name}: {'[REDACTED]' if 'TOKEN' in var_name or 'KEY' in var_name else value}")

                # Mask sensitive values for display
                if 'TOKEN' in var_name or 'KEY' in var_name:
                    if self.show_password_var.get():
                        display_value = value[:20] + "..." if len(value) > 20 else value
                    else:
                        display_value = "***"
                else:
                    display_value = value
            else:
                display_value = "Not set"

            label.configure(text=display_value)

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
        """Check current configuration from Claude Code settings.json"""
        try:
            # Check Claude Code settings.json
            claude_settings = self.get_claude_settings()
            claude_auth_token = None
            claude_base_url = None

            if 'env' in claude_settings:
                claude_auth_token = claude_settings['env'].get('ANTHROPIC_AUTH_TOKEN')
                claude_base_url = claude_settings['env'].get('ANTHROPIC_BASE_URL')

            if claude_base_url and 'z.ai' in claude_base_url:
                status_text = "✓ Currently using z.ai API\n"
                status_text += "(Configured in Claude Code settings.json)"
                self.status_label.configure(text=status_text, fg=self.success_color)
            elif claude_auth_token and not claude_base_url:
                status_text = "✓ Currently using Claude API Key\n"
                status_text += "(Configured in Claude Code settings.json)"
                self.status_label.configure(text=status_text, fg=self.success_color)
            elif not claude_auth_token and not claude_base_url:
                status_text = "✓ Currently using Claude Subscription\n"
                status_text += "(No custom settings configured)"
                self.status_label.configure(text=status_text, fg=self.success_color)
            elif claude_base_url and claude_auth_token:
                status_text = f"✓ Currently using Custom Base URL\n"
                status_text += f"Base URL: {claude_base_url}\n"
                status_text += "(Configured in Claude Code settings.json)"
                self.status_label.configure(text=status_text, fg=self.success_color)
            else:
                status_text = "⚠ No configuration is currently set"
                self.status_label.configure(text=status_text, fg=self.error_color)

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

                # Configure z.ai settings (only in settings.json)
                env_vars = {
                    'ANTHROPIC_AUTH_TOKEN': zai_key,
                    'ANTHROPIC_BASE_URL': 'https://api.z.ai/api/anthropic',
                    'ANTHROPIC_DEFAULT_OPUS_MODEL': self.zai_opus_model_var.get(),
                    'ANTHROPIC_DEFAULT_SONNET_MODEL': self.zai_sonnet_model_var.get(),
                    'ANTHROPIC_DEFAULT_HAIKU_MODEL': self.zai_haiku_model_var.get(),
                    'API_TIMEOUT_MS': '3000000'
                }

                # Update only Claude Code settings.json
                success, output = self.update_claude_settings(env_vars)
                if not success:
                    self.root.after(0, lambda msg=output: messagebox.showerror("Error", f"Failed to update Claude Code settings:\n{msg}"))
                    self.root.after(0, self.hide_loading)
                    return

                self.root.after(0, lambda: self.show_success_dialog("Success",
                                   "Z.ai configuration applied successfully!\n\nClaude Code settings.json updated.\n\nIMPORTANT: You must restart Claude Code for changes to take effect."))

            elif self.config_var.get() == "claude":
                # Apply Claude configuration
                if self.claude_mode_var.get() == "subscription":
                    # Clear all Claude settings from settings.json to use subscription
                    env_vars_to_remove = [
                        'ANTHROPIC_AUTH_TOKEN',
                        'ANTHROPIC_BASE_URL',
                        'ANTHROPIC_DEFAULT_OPUS_MODEL',
                        'ANTHROPIC_DEFAULT_SONNET_MODEL',
                        'ANTHROPIC_DEFAULT_HAIKU_MODEL',
                        'ANTHROPIC_API_KEY'
                    ]

                    # Clear from Claude Code settings only
                    success, output = self.update_claude_settings({var: '' for var in env_vars_to_remove})
                    if not success:
                        self.root.after(0, lambda msg=output: messagebox.showerror("Error", f"Failed to update Claude Code settings:\n{msg}"))
                        self.root.after(0, self.hide_loading)
                        return

                    self.root.after(0, lambda: self.show_success_dialog("Success",
                                       "Claude Subscription configuration applied successfully!\n\nAll settings cleared from Claude Code settings.json to use your official Claude subscription.\n\nIMPORTANT: You must restart Claude Code for changes to take effect."))

                else:
                    # API mode
                    claude_key = self.claude_key_entry.get().strip()

                    if not claude_key:
                        self.root.after(0, lambda: messagebox.showerror("Error", "Please enter your Claude API key"))
                        self.root.after(0, self.hide_loading)
                        return

                    # Configure Claude API settings (only in settings.json)
                    env_vars = {
                        'ANTHROPIC_AUTH_TOKEN': claude_key
                    }

                    # Update only Claude Code settings
                    success, output = self.update_claude_settings(env_vars)
                    if not success:
                        self.root.after(0, lambda msg=output: messagebox.showerror("Error", f"Failed to update Claude Code settings:\n{msg}"))
                        self.root.after(0, self.hide_loading)
                        return

                    self.root.after(0, lambda: self.show_success_dialog("Success",
                                       "Claude API configuration applied successfully!\n\nClaude Code settings.json updated.\n\nIMPORTANT: You must restart Claude Code for changes to take effect."))

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

                # Configure custom settings (only in settings.json)
                env_vars = {
                    'ANTHROPIC_AUTH_TOKEN': custom_key,
                    'ANTHROPIC_BASE_URL': custom_url
                }

                # Update only Claude Code settings
                success, output = self.update_claude_settings(env_vars)
                if not success:
                    self.root.after(0, lambda msg=output: messagebox.showerror("Error", f"Failed to update Claude Code settings:\n{msg}"))
                    self.root.after(0, self.hide_loading)
                    return

                self.root.after(0, lambda: self.show_success_dialog("Success",
                                   "Custom configuration applied successfully!\n\nClaude Code settings.json updated.\n\nIMPORTANT: You must restart Claude Code for changes to take effect."))


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
    # Check platform compatibility
    if not (IS_WINDOWS or IS_LINUX or IS_MACOS):
        response = input("This application is designed for Windows, Linux, and macOS. Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)

    root = tk.Tk()

    # Set some basic properties before creating the app
    if IS_LINUX:
        try:
            # Try to set a better visual on Linux systems
            root.tk.call('tk', 'scaling', 1.0)
            # Force better color depth if possible
            root.attributes('-depth', 24)
        except:
            pass
    elif IS_MACOS:
        try:
            # macOS-specific window settings
            root.tk.call('tk', 'scaling', 1.0)
            # Ensure proper retina display handling
            root.attributes('-alpha', 1.0)
        except:
            pass

    app = ClaudeConfigSwitcher(root)

    # Center window on screen with platform-specific handling
    root.update_idletasks()

    try:
        # Use reqwidth/reqheight for Linux and macOS, winfo_width/height for Windows
        if IS_LINUX or IS_MACOS:
            width = root.winfo_reqwidth()
            height = root.winfo_reqheight()
        else:
            width = root.winfo_width()
            height = root.winfo_height()

        # Fallback if dimensions are too small
        if width < 400:
            if IS_LINUX:
                width = 500
            elif IS_MACOS:
                width = 600
            else:
                width = 600
        if height < 600:
            if IS_LINUX:
                height = 850
            elif IS_MACOS:
                height = 1000
            else:
                height = 1100

        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # Calculate position with better bounds checking
        x = max(50, (screen_width // 2) - (width // 2))
        y = max(50, (screen_height // 2) - (height // 2))

        # Platform-specific bottom margin to account for taskbar
        bottom_margin = 80 if (not IS_LINUX and not IS_MACOS) else 50  # Windows gets larger margin

        # Ensure window doesn't go off screen
        if x + width > screen_width - 50:
            x = screen_width - width - 50
        if y + height > screen_height - bottom_margin:
            y = screen_height - height - bottom_margin

        root.geometry(f'{width}x{height}+{x}+{y}')

    except Exception:
        # Set a safe fallback geometry
        if IS_LINUX:
            root.geometry("500x850+100+100")
        elif IS_MACOS:
            root.geometry("600x1000+100+100")
        else:
            root.geometry("600x1100+100+100")

    # Apply window styles after window is fully created and displayed
    # Use longer delay on Linux to ensure window manager has processed the window
    if IS_LINUX:
        # Skip complex window styling on Linux to avoid freezes
        pass
    else:
        delay = 200
        root.after(delay, app.set_window_style)
    root.mainloop()

if __name__ == "__main__":
    main()
