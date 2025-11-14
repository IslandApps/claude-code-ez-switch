import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import sys
import threading
import json
from pathlib import Path
from PIL import Image, ImageTk
import platform

# Platform detection and module imports
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

# Try to import Windows-specific modules
try:
    import win32gui
    import win32con
    from ctypes import windll, c_int, byref
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    if IS_WINDOWS:
        print("Warning: pywin32 not available. Some window styling features may not work.")

# Font management for Poppins
class FontManager:
    def __init__(self):
        self.primary_font = "Poppins"
        # Platform-specific font preferences
        if IS_LINUX:
            self.fallback_fonts = ["Ubuntu", "DejaVu Sans", "Liberation Sans", "Noto Sans", "Cantarell", "Arial", "Helvetica", "sans-serif"]
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

        except Exception as e:
            print(f"Font detection error: {e}")
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
        self.root.title("Claude Code EZ Switch")

        # Platform-specific window settings
        if IS_LINUX:
            # Linux: More conservative size and allow resizing
            self.root.geometry("500x850")
            self.root.resizable(True, True)
            self.root.minsize(450, 700)
        else:
            # Windows: Original size and no resizing
            self.root.geometry("600x1000")
            self.root.resizable(False, False)

        # Remove window decorations and create custom title bar
        # On Linux, be more conservative with window decorations
        if IS_LINUX:
            # Keep decorations on Linux to avoid focus issues
            self.root.overrideredirect(False)
        else:
            self.root.overrideredirect(True)

        # Variables for window dragging
        self.start_x = None
        self.start_y = None

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
        style.configure('TRadiobutton', background=self.bg_color, foreground=self.fg_color,
                       font=font_manager.get_font(10))
        style.map('TRadiobutton', background=[('active', self.bg_color)])
        
        self.create_widgets()
        self.load_saved_api_keys()
        self.load_existing_api_keys()
        # Update UI to match loaded configuration
        self.on_config_change()
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

            except Exception as e:
                print(f"Could not set window style: {e}")
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
            except Exception as e:
                print(f"Linux window styling limited: {e}")
        else:
            # For other platforms, just use basic borderless mode
            print(f"Using basic window styling for {platform.system()}")

    def start_move(self, event):
        """Start moving the window"""
        self.start_x = event.x
        self.start_y = event.y

    def on_move(self, event):
        """Handle window movement"""
        if self.start_x and self.start_y:
            x = self.root.winfo_x() + (event.x - self.start_x)
            y = self.root.winfo_y() + (event.y - self.start_y)
            self.root.geometry(f"+{x}+{y}")

    def stop_move(self, event):
        """Stop moving the window"""
        self.start_x = None
        self.start_y = None

    def minimize_window(self):
        """Minimize the window by hiding it and showing a restore notification"""
        try:
            # Simple approach: hide the window and show a notification
            self.root.withdraw()

            # Schedule the restore notification to run after the window is hidden
            self.root.after(200, self._show_minimize_notification)
        except Exception as e:
            print(f"Minimize error: {e}")
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

        except Exception as e:
            print(f"Restore dialog error: {e}")
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
        except Exception as e:
            print(f"Restore error: {e}")
            self._restore_main_window()

    def _restore_main_window(self):
        """Restore the main window to its original state"""
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        except Exception as e:
            print(f"Main window restore error: {e}")

    def close_window(self):
        """Close the window"""
        self.close_application()
        
    def create_widgets(self):
        # Custom title bar
        title_bar = tk.Frame(self.root, bg=self.bg_color, relief=tk.RAISED, bd=0, height=30)
        title_bar.pack(fill=tk.X, side=tk.TOP)
        title_bar.pack_propagate(False)

        # Bind mouse events for window dragging
        title_bar.bind('<Button-1>', self.start_move)
        title_bar.bind('<B1-Motion>', self.on_move)
        title_bar.bind('<ButtonRelease-1>', self.stop_move)

        # Title text
        title_frame = tk.Frame(title_bar, bg=self.bg_color)
        title_frame.pack(side=tk.LEFT, padx=10, pady=5)

        claude_code_label = tk.Label(title_frame, text="Claude Code", bg=self.bg_color, fg="#FF8C00",
                                   font=font_manager.get_font(10, 'bold'))
        claude_code_label.pack(side=tk.LEFT)

        ez_switch_label = tk.Label(title_frame, text=" EZ Switch", bg=self.bg_color, fg=self.fg_color,
                                 font=font_manager.get_font(10, 'bold'))
        ez_switch_label.pack(side=tk.LEFT)

        # Window controls container
        controls_frame = tk.Frame(title_bar, bg=self.bg_color)
        controls_frame.pack(side=tk.RIGHT, padx=5, pady=2)

  
        # Close button
        close_btn = tk.Button(controls_frame, text="×", bg="#dc3545", fg=self.fg_color,
                             font=font_manager.get_font(12, 'bold'), relief=tk.FLAT, bd=0, width=3, height=1,
                             cursor="hand2", command=self.close_window)
        close_btn.pack(side=tk.LEFT, padx=2)
        close_btn.bind('<Enter>', lambda e: close_btn.configure(bg="#c82333"))
        close_btn.bind('<Leave>', lambda e: close_btn.configure(bg="#dc3545"))

        # Main container
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
        title_frame = tk.Frame(content_frame, bg=self.bg_color)
        title_frame.pack(pady=(0, 5))

        claude_code_label = tk.Label(title_frame, text="Claude Code", bg=self.bg_color, fg="#FF8C00",
                                   font=font_manager.get_font(22, 'bold'))
        claude_code_label.pack(side=tk.LEFT)

        ez_switch_label = tk.Label(title_frame, text=" EZ Switch", bg=self.bg_color, fg=self.fg_color,
                                 font=font_manager.get_font(22, 'bold'))
        ez_switch_label.pack(side=tk.LEFT)
        
        subtitle_label = ttk.Label(content_frame,
                                   text="Switch between z.ai and custom configurations",
                                   style='Subtitle.TLabel')
        subtitle_label.pack(pady=(0, 15))
        
        # Current Status Frame
        status_frame = tk.Frame(content_frame, bg=self.entry_bg, relief=tk.FLAT, bd=0)
        status_frame.pack(fill=tk.X, pady=(0, 20), padx=2)
        
        status_title = ttk.Label(status_frame, text="Current Status:",
                                font=font_manager.get_font(15, 'bold'))
        status_title.pack(anchor=tk.W, padx=15, pady=(15, 10))

        self.status_label = tk.Label(status_frame, text="Checking...",
                                     bg=self.entry_bg, fg=self.fg_color,
                                     font=font_manager.get_font(14, 'bold'), anchor=tk.W, justify=tk.LEFT)
        self.status_label.pack(anchor=tk.W, padx=15, pady=(0, 15), fill=tk.X)
        
        # Loading indicator (hidden by default)
        self.loading_frame = tk.Frame(status_frame, bg=self.entry_bg)
        self.loading_label = tk.Label(self.loading_frame, text="⟳ Applying configuration...",
                                     bg=self.entry_bg, fg=self.accent_color,
                                     font=font_manager.get_font(14, 'bold'), anchor=tk.W)
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
        
        # Z.ai radio button
        zai_radio = ttk.Radiobutton(radio_container, text="Z.ai", 
                                   variable=self.config_var, value="zai",
                                   command=self.on_config_change)
        zai_radio.pack(anchor=tk.W, pady=(0, 5))
        
    
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
        self.create_custom_frame()

        # Show/Hide Password Checkbutton
        self.show_password_var = tk.BooleanVar()
        show_password_check = tk.Checkbutton(content_frame, text="Show API Keys",
                                           variable=self.show_password_var,
                                           command=self.toggle_password_visibility,
                                           bg=self.bg_color, fg=self.fg_color,
                                           selectcolor=self.entry_bg,
                                           activebackground=self.bg_color,
                                           activeforeground=self.fg_color,
                                           font=font_manager.get_font(9))
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
                                           font=font_manager.get_font(9))
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
                                      font=font_manager.get_font(11, 'bold'), relief=tk.FLAT,
                                      cursor="hand2", bd=0, pady=12,
                                      command=self.apply_configuration)
        self.apply_button.grid(row=0, column=0, columnspan=2, sticky="ew", padx=(0, 5), pady=(0, 8))
        
        # Bind hover effects
        self.apply_button.bind('<Enter>', lambda e: self.apply_button.configure(bg=self.button_hover))
        self.apply_button.bind('<Leave>', lambda e: self.apply_button.configure(bg=self.button_bg))
        
        # Refresh Status Button
        self.refresh_button = tk.Button(button_container, text="Refresh",
                                       bg=self.refresh_button_bg, fg=self.fg_color,
                                       font=font_manager.get_font(10, 'bold'), relief=tk.FLAT,
                                       cursor="hand2", bd=0, pady=12,
                                       command=self.check_current_status)
        self.refresh_button.grid(row=0, column=2, sticky="ew", padx=(5, 0), pady=(0, 8))
        
        # Bind hover effects
        self.refresh_button.bind('<Enter>', lambda e: self.refresh_button.configure(bg=self.refresh_button_hover))
        self.refresh_button.bind('<Leave>', lambda e: self.refresh_button.configure(bg=self.refresh_button_bg))
        
        # Close Button (spans all columns)
        self.close_button = tk.Button(button_container, text="Close Application",
                                     bg=self.close_button_bg, fg=self.fg_color,
                                     font=font_manager.get_font(10), relief=tk.FLAT,
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
                              font=font_manager.get_font(8))
        footer_label.pack()
        
        # GitHub link
        github_link = tk.Label(footer_frame, text="Source Code",
                              bg=self.bg_color, fg=self.accent_color,
                              font=font_manager.get_font(8), cursor="hand2")
        github_link.pack()
        github_link.bind("<Button-1>", lambda e: self.open_github_link())
    
    def on_entry_click(self, event):
        """Handle entry field click to ensure proper focus on Linux"""
        widget = event.widget
        # Simple focus setting - avoid complex focus management
        widget.focus_set()
    
    def setup_linux_focus(self):
        """Set up proper focus handling for Linux"""
        try:
            # Simple focus setup - avoid complex focus management that might cause freezes
            if hasattr(self, 'zai_key_entry'):
                self.root.after(500, lambda: self.zai_key_entry.focus_set())
                
        except Exception as e:
            print(f"Linux focus setup error: {e}")
    
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
        self.zai_key_combo = ttk.Combobox(key_management_frame, textvariable=self.zai_key_var,
                                          state="readonly", width=40)
        self.zai_key_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.zai_key_combo.bind('<<ComboboxSelected>>', self.on_zai_key_selected)

        # Add/Delete buttons
        button_frame = tk.Frame(key_management_frame, bg=self.entry_bg)
        button_frame.pack(side=tk.RIGHT)

        add_key_btn = tk.Button(button_frame, text="+", bg=self.refresh_button_bg, fg=self.fg_color,
                                font=font_manager.get_font(10, 'bold'), relief=tk.FLAT, cursor="hand2",
                                bd=0, width=3, command=self.add_zai_key)
        add_key_btn.pack(side=tk.LEFT, padx=(0, 2))
        add_key_btn.bind('<Enter>', lambda e: add_key_btn.configure(bg=self.refresh_button_hover))
        add_key_btn.bind('<Leave>', lambda e: add_key_btn.configure(bg=self.refresh_button_bg))

        delete_key_btn = tk.Button(button_frame, text="−", bg="#8b4513", fg=self.fg_color,
                                   font=font_manager.get_font(10, 'bold'), relief=tk.FLAT, cursor="hand2",
                                   bd=0, width=3, command=self.delete_zai_key)
        delete_key_btn.pack(side=tk.LEFT)
        delete_key_btn.bind('<Enter>', lambda e: delete_key_btn.configure(bg="#a0522d"))
        delete_key_btn.bind('<Leave>', lambda e: delete_key_btn.configure(bg="#8b4513"))

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
                                font=font_manager.get_font(9, 'bold'), relief=tk.FLAT,
                                cursor="hand2", bd=0, pady=8,
                                command=self.save_current_zai_key)
        save_key_btn.pack(fill=tk.X, padx=15, pady=(0, 10))
        save_key_btn.bind('<Enter>', lambda e: save_key_btn.configure(bg=self.refresh_button_hover))
        save_key_btn.bind('<Leave>', lambda e: save_key_btn.configure(bg=self.refresh_button_bg))

        # Initialize storage for multiple keys
        self.zai_keys = {}  # Format: {"name": "key"}
        self.current_zai_key_name = None

        # Environment variables display (hidden by default)
        self.zai_env_frame = tk.Frame(self.zai_frame, bg=self.entry_bg)

        # Hide button for z.ai environment variables
        zai_hide_frame = tk.Frame(self.zai_env_frame, bg=self.entry_bg)
        zai_hide_frame.pack(fill=tk.X, padx=15, pady=(10, 5))

        zai_hide_btn = tk.Button(zai_hide_frame, text="✕ Hide Environment Variables",
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
                            bg=self.entry_bg, fg="#cccccc",
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
        
        # Bind focus events for proper input handling
        self.custom_url_entry.bind('<Button-1>', self.on_entry_click)

        # Add border to entry
        custom_url_border = tk.Frame(self.custom_frame, bg=self.accent_color, height=2)
        custom_url_border.pack(fill=tk.X, padx=15, pady=(0, 5))

        custom_key_label = ttk.Label(self.custom_frame, text="Custom API Key:")
        custom_key_label.pack(anchor=tk.W, padx=15, pady=(5, 2))

        self.custom_key_entry = tk.Entry(self.custom_frame, bg=self.entry_bg, fg=self.fg_color,
                                         insertbackground=self.fg_color, relief=tk.FLAT,
                                         font=font_manager.get_font(10), bd=0, show="*")
        self.custom_key_entry.pack(fill=tk.X, padx=15, pady=(0, 2), ipady=8)
        
        # Bind focus events for proper input handling
        self.custom_key_entry.bind('<Button-1>', self.on_entry_click)

        # Add border to entry
        custom_key_border = tk.Frame(self.custom_frame, bg=self.accent_color, height=2)
        custom_key_border.pack(fill=tk.X, padx=15, pady=(0, 10))

        # Environment variables display (hidden by default)
        self.custom_env_frame = tk.Frame(self.custom_frame, bg=self.entry_bg)

        # Hide button for custom environment variables
        custom_hide_frame = tk.Frame(self.custom_env_frame, bg=self.entry_bg)
        custom_hide_frame.pack(fill=tk.X, padx=15, pady=(10, 5))

        custom_hide_btn = tk.Button(custom_hide_frame, text="✕ Hide Environment Variables",
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
                            bg=self.entry_bg, fg="#cccccc",
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
        """Load existing API keys from environment variables and pre-fill them"""
        try:
            # Check user-level environment variables based on platform
            user_auth_token = self.get_user_env_var('ANTHROPIC_AUTH_TOKEN')
            user_base_url = self.get_user_env_var('ANTHROPIC_BASE_URL')

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


        except Exception as e:
            # Silently fail if we can't load keys
            pass

    def get_user_env_var(self, var_name):
        """Get user-level environment variable based on platform"""
        try:
            if IS_WINDOWS:
                # Use PowerShell for Windows
                result = subprocess.run(
                    ['powershell', '-Command',
                     f"[System.Environment]::GetEnvironmentVariable('{var_name}', 'User')"],
                    capture_output=True, text=True, timeout=5
                )
                return result.stdout.strip()
            elif IS_LINUX:
                # For Linux, check in common shell configuration files with better error handling
                home_dir = Path.home()
                config_files = [
                    home_dir / '.bashrc',
                    home_dir / '.profile',
                    home_dir / '.zshrc',
                    home_dir / '.bash_profile'
                ]

                # Check each file for the environment variable
                for config_file in config_files:
                    try:
                        if config_file.exists() and config_file.is_file():
                            with open(config_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                                # Look for export statements
                                for line in content.splitlines():
                                    line = line.strip()
                                    if line.startswith(f'export {var_name}='):
                                        # Extract value after = and strip quotes
                                        value = line.split('=', 1)[1].strip()
                                        # Remove surrounding quotes if present
                                        if value.startswith('"') and value.endswith('"'):
                                            value = value[1:-1]
                                        elif value.startswith("'") and value.endswith("'"):
                                            value = value[1:-1]
                                        return value
                    except (PermissionError, IOError, UnicodeDecodeError) as e:
                        print(f"Warning: Could not read {config_file}: {e}")
                        continue

            # Fallback to current process environment
            return os.environ.get(var_name, '').strip()

        except Exception as e:
            print(f"Error getting environment variable {var_name}: {e}")
            return ''

    def set_user_env_var(self, var_name, value):
        """Set user-level environment variable based on platform"""
        try:
            if IS_WINDOWS:
                # Use PowerShell for Windows
                command = f"[System.Environment]::SetEnvironmentVariable('{var_name}', '{value}', 'User')"
                success, output = self.run_powershell_command(command)
                return success, output
            elif IS_LINUX:
                # For Linux, use a more robust approach with better error handling
                home_dir = Path.home()
                
                # Try multiple shell config files in order of preference
                config_files = [
                    home_dir / '.bashrc',
                    home_dir / '.profile',
                    home_dir / '.zshrc'
                ]
                
                # Find the first existing/writable config file
                target_file = None
                for config_file in config_files:
                    try:
                        # Test if we can write to this file
                        if config_file.exists():
                            # Test write permission
                            with open(config_file, 'a') as f:
                                pass
                            target_file = config_file
                            break
                        else:
                            # Create the file if it doesn't exist
                            with open(config_file, 'w') as f:
                                f.write("# Claude Code EZ Switch Environment Variables\n")
                            target_file = config_file
                            break
                    except (PermissionError, IOError):
                        continue
                
                if not target_file:
                    return False, "No writable shell configuration file found"
                
                # Read existing content with error handling
                existing_lines = []
                try:
                    with open(target_file, 'r', encoding='utf-8') as f:
                        existing_lines = f.readlines()
                except Exception as e:
                    print(f"Warning: Could not read {target_file}: {e}")
                    existing_lines = []
                
                # Remove existing export for this variable (more robust matching)
                updated_lines = []
                var_pattern = f'export {var_name}='
                for line in existing_lines:
                    if not line.strip().startswith(var_pattern):
                        updated_lines.append(line)
                
                # Add the new export at the end
                updated_lines.append(f'\n# Added by Claude Code EZ Switch\n')
                updated_lines.append(f'export {var_name}="{value}"\n')
                
                # Write back to file with error handling
                try:
                    with open(target_file, 'w', encoding='utf-8') as f:
                        f.writelines(updated_lines)
                    return True, f"Environment variable {var_name} set in {target_file.name}"
                except Exception as e:
                    return False, f"Failed to write to {target_file}: {e}"

            return False, "Unsupported platform for setting environment variables"

        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def get_claude_settings(self):
        """Get current Claude Code settings.json content"""
        try:
            if self.claude_settings_file.exists():
                with open(self.claude_settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Return empty settings if file doesn't exist
                return {}
        except Exception as e:
            print(f"Error reading Claude settings: {e}")
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
            
            
            # Load custom config
            if 'custom_url' in saved_keys:
                self.custom_url_entry.delete(0, tk.END)
                self.custom_url_entry.insert(0, saved_keys['custom_url'])
            
            if 'custom_key' in saved_keys:
                self.custom_key_entry.delete(0, tk.END)
                self.custom_key_entry.insert(0, saved_keys['custom_key'])
            
                        
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
            
            # Save z.ai keys
            saved_keys['zai_keys'] = self.zai_keys
            saved_keys['current_zai_key_name'] = self.current_zai_key_name
            
            
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

        # Update combobox
        self.update_zai_key_combo()

        # Save to persistent storage
        self.save_api_keys()

        # Show success message
        self.show_inline_message(f"Z.ai key '{selected_name}' deleted successfully!", "success")

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
        
        # Hide message frame
        self.message_frame.pack_forget()

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
        self.custom_frame.pack_forget()

        # Show the selected frame
        if self.config_var.get() == "zai":
            self.zai_frame.pack(fill=tk.X, pady=(0, 10))
        elif self.config_var.get() == "custom":
            self.custom_frame.pack(fill=tk.X, pady=(0, 10))

        # If environment variables are currently visible, update them
        if self.show_env_vars_var.get():
            # Schedule update after widgets are properly packed
            self.root.after(100, self.update_env_vars_display)
    
        
    def toggle_password_visibility(self):
        """Toggle password visibility in entry fields"""
        if self.show_password_var.get():
            self.zai_key_entry.configure(show="")
            self.custom_key_entry.configure(show="")
        else:
            self.zai_key_entry.configure(show="*")
            self.custom_key_entry.configure(show="*")

    def hide_env_vars(self, config_type):
        """Hide environment variables for a specific configuration type"""
        if config_type == 'zai':
            self.zai_env_frame.pack_forget()
        elif config_type == 'custom':
            self.custom_env_frame.pack_forget()

        # Also uncheck the main checkbox if all env vars are hidden
        if not self.zai_env_frame.winfo_ismapped() and not self.custom_env_frame.winfo_ismapped():
            self.show_env_vars_var.set(False)

    def toggle_env_vars_visibility(self):
        """Toggle environment variables display visibility"""
        if self.show_env_vars_var.get():
            # Show environment variable frames based on current configuration
            if self.config_var.get() == "zai":
                self.zai_env_frame.pack(fill=tk.X, pady=(0, 10))
            elif self.config_var.get() == "custom":
                self.custom_env_frame.pack(fill=tk.X, pady=(0, 10))

            # Update the display with current system values
            self.root.after(100, self.update_env_vars_display)  # Small delay to ensure widgets are visible
        else:
            # Hide all environment variable frames
            self.zai_env_frame.pack_forget()
            self.custom_env_frame.pack_forget()

    def get_current_env_vars(self):
        """Get current environment variables from the system"""
        env_vars = {}
        try:
            # List of environment variables to check
            var_names = [
                'ANTHROPIC_AUTH_TOKEN',
                'ANTHROPIC_BASE_URL',
                'ANTHROPIC_DEFAULT_OPUS_MODEL',
                'ANTHROPIC_DEFAULT_SONNET_MODEL',
                'ANTHROPIC_DEFAULT_HAIKU_MODEL',
                'ANTHROPIC_API_KEY'
            ]

            for var_name in var_names:
                value = self.get_user_env_var(var_name)
                if value:
                    env_vars[var_name] = value

        except Exception as e:
            print(f"Error getting environment variables: {e}")

        return env_vars

    def update_env_vars_display(self):
        """Update the environment variables display with current system values"""
        env_vars = self.get_current_env_vars()

        # Update z.ai environment variables if that frame is visible
        if self.config_var.get() == "zai" and hasattr(self, 'zai_env_value_labels'):
            for var_name, label in self.zai_env_value_labels.items():
                value = env_vars.get(var_name, "Not set")

                # Mask sensitive values for display
                if 'AUTH_TOKEN' in var_name or 'API_KEY' in var_name and value != "Not set":
                    if len(value) > 8:
                        display_value = f"{value[:4]}...{value[-4:]}"
                    else:
                        display_value = "***"
                else:
                    display_value = value

                label.configure(text=display_value)

        # Update custom environment variables if that frame is visible
        elif self.config_var.get() == "custom" and hasattr(self, 'custom_env_value_labels'):
            for var_name, label in self.custom_env_value_labels.items():
                value = env_vars.get(var_name, "Not set")

                # Mask sensitive values for display
                if 'AUTH_TOKEN' in var_name or 'API_KEY' in var_name and value != "Not set":
                    if len(value) > 8:
                        display_value = f"{value[:4]}...{value[-4:]}"
                    else:
                        display_value = "***"
                else:
                    display_value = value

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
        """Check current configuration from both environment variables and Claude Code settings"""
        try:
            # First check Claude Code settings.json (highest priority)
            claude_settings = self.get_claude_settings()
            claude_auth_token = None
            claude_base_url = None
            
            if 'env' in claude_settings:
                claude_auth_token = claude_settings['env'].get('ANTHROPIC_AUTH_TOKEN')
                claude_base_url = claude_settings['env'].get('ANTHROPIC_BASE_URL')
            
            # Fall back to environment variables if settings.json doesn't have the config
            if not claude_base_url:
                claude_base_url = self.get_user_env_var('ANTHROPIC_BASE_URL')
            if not claude_auth_token:
                claude_auth_token = self.get_user_env_var('ANTHROPIC_AUTH_TOKEN')

            if claude_base_url and 'z.ai' in claude_base_url:
                status_text = "✓ Currently using z.ai API\n"
                status_text += f"(Configured in Claude Code settings.json)" if claude_settings.get('env') else f"(Configured via environment variables)"
                self.status_label.configure(text=status_text, fg=self.success_color)
            elif claude_base_url and claude_auth_token:
                status_text = f"✓ Currently using Custom Base URL\n"
                status_text += f"Base URL: {claude_base_url}\n"
                status_text += f"(Configured in Claude Code settings.json)" if claude_settings.get('env') else f"(Configured via environment variables)"
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

                # Set z.ai environment variables (all at User level to avoid admin requirements)
                env_vars = [
                    ('ANTHROPIC_AUTH_TOKEN', zai_key),
                    ('ANTHROPIC_BASE_URL', 'https://api.z.ai/api/anthropic'),
                    ('ANTHROPIC_DEFAULT_OPUS_MODEL', 'GLM-4.6'),
                    ('ANTHROPIC_DEFAULT_SONNET_MODEL', 'GLM-4.6'),
                    ('ANTHROPIC_DEFAULT_HAIKU_MODEL', 'GLM-4.6')
                ]

                for var_name, var_value in env_vars:
                    success, output = self.set_user_env_var(var_name, var_value)
                    if not success:
                        self.root.after(0, lambda msg=output: messagebox.showerror("Error", f"Failed to set environment variable:\n{msg}"))
                        self.root.after(0, self.hide_loading)
                        return
                
                # Then update Claude Code settings.json
                env_dict = {var_name: var_value for var_name, var_value in env_vars}
                success, output = self.update_claude_settings(env_dict)
                if not success:
                    self.root.after(0, lambda msg=output: messagebox.showerror("Error", f"Failed to update Claude Code settings:\n{msg}"))
                    self.root.after(0, self.hide_loading)
                    return

                restart_message = "IMPORTANT: You must close and reopen VS Code or any application using Claude Code for changes to take effect.\n"
                if IS_LINUX:
                    restart_message += "You may also need to run 'source ~/.bashrc' or restart your terminal."
                else:
                    restart_message += "If using terminal only, close and reopen the terminal."

                self.root.after(0, lambda: messagebox.showinfo("Success",
                                   f"Z.ai configuration applied successfully!\n\nEnvironment variables and Claude Code settings.json updated.\n\n{restart_message}"))

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
                env_vars = [
                    ('ANTHROPIC_AUTH_TOKEN', custom_key),
                    ('ANTHROPIC_BASE_URL', custom_url)
                ]

                # First update environment variables
                for var_name, var_value in env_vars:
                    success, output = self.set_user_env_var(var_name, var_value)
                    if not success:
                        self.root.after(0, lambda msg=output: messagebox.showerror("Error", f"Failed to set environment variable:\n{msg}"))
                        self.root.after(0, self.hide_loading)
                        return
                
                # Then update Claude Code settings.json
                env_dict = {var_name: var_value for var_name, var_value in env_vars}
                success, output = self.update_claude_settings(env_dict)
                if not success:
                    self.root.after(0, lambda msg=output: messagebox.showerror("Error", f"Failed to update Claude Code settings:\n{msg}"))
                    self.root.after(0, self.hide_loading)
                    return

                restart_message = "IMPORTANT: You must close and reopen VS Code or any application using Claude Code for changes to take effect.\n"
                if IS_LINUX:
                    restart_message += "You may also need to run 'source ~/.bashrc' or restart your terminal."
                else:
                    restart_message += "If using terminal only, close and reopen the terminal."

                self.root.after(0, lambda: messagebox.showinfo("Success",
                                   f"Custom configuration applied successfully!\n\nEnvironment variables and Claude Code settings.json updated.\n\n{restart_message}"))


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
    # Display platform information
    print(f"Starting Claude Code EZ Switch on {platform.system()} {platform.release()}")

    # Check platform compatibility
    if not (IS_WINDOWS or IS_LINUX):
        print(f"Warning: This application is designed for Windows and Linux. Your platform ({platform.system()}) may have limited compatibility.")
        response = input("Continue anyway? (y/N): ")
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

    app = ClaudeConfigSwitcher(root)

    # Center window on screen with Linux-specific handling
    root.update_idletasks()

    try:
        width = root.winfo_reqwidth() if IS_LINUX else root.winfo_width()
        height = root.winfo_reqheight() if IS_LINUX else root.winfo_height()

        # Fallback if dimensions are too small
        if width < 400:
            width = 500 if IS_LINUX else 600
        if height < 600:
            height = 850 if IS_LINUX else 1000

        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # Calculate position with better bounds checking
        x = max(50, (screen_width // 2) - (width // 2))
        y = max(50, (screen_height // 2) - (height // 2))

        # Ensure window doesn't go off screen
        if x + width > screen_width - 50:
            x = screen_width - width - 50
        if y + height > screen_height - 50:
            y = screen_height - height - 50

        root.geometry(f'{width}x{height}+{x}+{y}')

    except Exception as e:
        print(f"Warning: Could not center window properly: {e}")
        # Set a safe fallback geometry
        if IS_LINUX:
            root.geometry("500x850+100+100")
        else:
            root.geometry("600x1000+100+100")

    # Apply window styles after window is fully created and displayed
    # Use longer delay on Linux to ensure window manager has processed the window
    if IS_LINUX:
        # Skip complex window styling on Linux to avoid freezes
        print("Linux detected: Using simplified window management")
    else:
        delay = 200
        root.after(delay, app.set_window_style)

    print(f"Window initialized with geometry: {root.geometry()}")
    root.mainloop()

if __name__ == "__main__":
    main()
