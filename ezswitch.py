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

# Try to import Windows-specific modules
try:
    import win32gui
    import win32con
    from ctypes import windll, c_int, byref
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("Warning: pywin32 not available. Some window styling features may not work.")

# Font management for Poppins
class FontManager:
    def __init__(self):
        self.primary_font = "Poppins"
        self.fallback_fonts = ["Segoe UI", "Arial", "Helvetica", "sans-serif"]
        self.available_font = None
        self._font_detection_attempted = False

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
        """Get a font tuple with the best available font"""
        # Ensure we have detected fonts
        if not self.available_font:
            self.get_available_font()

        # Handle special font styles
        weight_val = "bold" if weight == "bold" else "normal"
        slant_val = "italic" if slant == "italic" else "roman"

        # Return standard 4-element font tuple
        return (self.available_font, size, weight_val, slant_val)

# Initialize font manager
font_manager = FontManager()

class ClaudeConfigSwitcher:
    def __init__(self, root):
        self.root = root
        self.root.title("")
        self.root.geometry("600x1000")
        self.root.resizable(False, False)

        # Remove window decorations and create custom title bar
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

    def set_window_style(self):
        """Set window styles for borderless window with shadow"""
        if not WIN32_AVAILABLE:
            print("Windows styling modules not available. Using basic borderless mode.")
            return

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

        # Add border to entry
        custom_url_border = tk.Frame(self.custom_frame, bg=self.accent_color, height=2)
        custom_url_border.pack(fill=tk.X, padx=15, pady=(0, 5))

        custom_key_label = ttk.Label(self.custom_frame, text="Custom API Key:")
        custom_key_label.pack(anchor=tk.W, padx=15, pady=(5, 2))

        self.custom_key_entry = tk.Entry(self.custom_frame, bg=self.entry_bg, fg=self.fg_color,
                                         insertbackground=self.fg_color, relief=tk.FLAT,
                                         font=font_manager.get_font(10), bd=0, show="*")
        self.custom_key_entry.pack(fill=tk.X, padx=15, pady=(0, 2), ipady=8)

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
            messagebox.showerror("Error", "Please enter a name for this key")
            return

        if not key_value:
            messagebox.showerror("Error", "Please enter a key value")
            return

        if key_name in self.zai_keys:
            if not messagebox.askyesno("Warning", f"Key '{key_name}' already exists. Overwrite?"):
                return

        # Save the key
        self.zai_keys[key_name] = key_value
        self.current_zai_key_name = key_name

        # Update combobox
        self.update_zai_key_combo()
        self.zai_key_var.set(key_name)

        # Save to persistent storage
        self.save_api_keys()

        messagebox.showinfo("Success", f"Z.ai key '{key_name}' saved successfully!")

    def delete_zai_key(self):
        """Delete the selected z.ai key"""
        selected_name = self.zai_key_var.get()

        if not selected_name or selected_name not in self.zai_keys:
            messagebox.showerror("Error", "Please select a key to delete")
            return

        if messagebox.askyesno("Confirm Delete", f"Delete key '{selected_name}'?"):
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

            messagebox.showinfo("Success", f"Z.ai key '{selected_name}' deleted successfully!")

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
                result = subprocess.run(
                    ['powershell', '-Command',
                     f"[System.Environment]::GetEnvironmentVariable('{var_name}', 'User')"],
                    capture_output=True, text=True, timeout=5
                )
                value = result.stdout.strip()
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
            elif user_base_url and user_auth_token:
                status_text = f"✓ Currently using Custom Base URL\n"
                status_text += f"Base URL: {user_base_url}"
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
                commands = [
                    f"[System.Environment]::SetEnvironmentVariable('ANTHROPIC_AUTH_TOKEN', '{zai_key}', 'User')",
                    f"[System.Environment]::SetEnvironmentVariable('ANTHROPIC_BASE_URL', 'https://api.z.ai/api/anthropic', 'User')",
                    "[System.Environment]::SetEnvironmentVariable('ANTHROPIC_DEFAULT_OPUS_MODEL', 'GLM-4.6', 'User')",
                    "[System.Environment]::SetEnvironmentVariable('ANTHROPIC_DEFAULT_SONNET_MODEL', 'GLM-4.6', 'User')",
                    "[System.Environment]::SetEnvironmentVariable('ANTHROPIC_DEFAULT_HAIKU_MODEL', 'GLM-4.6', 'User')"
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

    # Apply window styles after window is fully created and displayed
    root.after(200, app.set_window_style)

    root.mainloop()

if __name__ == "__main__":
    main()
