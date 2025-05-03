import os
import time
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pyautogui
import keyboard
import pyperclip
import threading
import re
from datetime import datetime
import webbrowser
import logging
import platform
import subprocess
from PIL import Image, ImageTk
import base64
import io
import requests
from urllib.parse import urlparse
from ttkthemes import ThemedTk

class AdvancedTabScreenshotTool:
    def __init__(self):
        # Setup logging
        self.setup_logging()
        
        # Configuration directories
        self.config_dir = os.path.join(os.path.expanduser("~"), ".advanced_tab_screenshot")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.log_file = os.path.join(self.config_dir, "app.log")
        
        # Create necessary directories
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Load or create config
        self.config = self.load_config()
        
        # Set screenshots directory (from config or default)
        self.screenshots_dir = self.config.get("screenshots_dir", os.path.join(self.config_dir, "screenshots"))
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        # Status flags and counters
        self.operation_in_progress = False
        self.screenshot_count = 0
        self.current_browser = self.detect_browser()
        
        # Screenshot settings
        self.delay_before_screenshot = self.config.get("delay_before_screenshot", 0.5)
        self.delay_between_tabs = self.config.get("delay_between_tabs", 1.0)
        self.auto_open_folder = self.config.get("auto_open_folder", False)
        self.url_detection_method = self.config.get("url_detection_method", "clipboard")
        self.create_subfolder_per_session = self.config.get("create_subfolder_per_session", True)
        self.current_session_folder = None
        
        # Initialize GUI
        self.create_gui()
        
        # Register keyboard shortcuts
        self.setup_keyboard_shortcuts()
        
        # Initialize browser adapter
        self.browser_adapter = BrowserAdapter(self)
        
        # Log startup
        logging.info(f"Application started. Detected browser: {self.current_browser}")
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = os.path.join(os.path.expanduser("~"), ".advanced_tab_screenshot")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "app.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def load_config(self):
        """Load config from file or create default"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logging.error("Config file is corrupted. Loading defaults.")
                return self.create_default_config()
        else:
            return self.create_default_config()
    
    def create_default_config(self):
        """Create and save default configuration"""
        default_config = {
            "screenshots_dir": os.path.join(self.config_dir, "screenshots"),
            "delay_before_screenshot": 0.5,
            "delay_between_tabs": 1.0,
            "auto_open_folder": False,
            "url_detection_method": "clipboard",
            "create_subfolder_per_session": True,
            "hotkey_single_screenshot": "alt+s",
            "hotkey_all_screenshots": "alt+a",
            "theme": "azure",
            "window_size": "600x650"
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def save_config(self):
        """Save config to file"""
        try:
            # Update config with current values
            self.config["screenshots_dir"] = self.screenshots_dir
            self.config["delay_before_screenshot"] = self.delay_before_screenshot
            self.config["delay_between_tabs"] = self.delay_between_tabs
            self.config["auto_open_folder"] = self.auto_open_folder
            self.config["url_detection_method"] = self.url_detection_method
            self.config["create_subfolder_per_session"] = self.create_subfolder_per_session
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logging.info("Configuration saved successfully")
            return True
        except Exception as e:
            logging.error(f"Error saving configuration: {str(e)}")
            return False
    
    def detect_browser(self):
        """Detect which browser is likely to be active"""
        system = platform.system()
        
        if system == "Windows":
            try:
                processes = subprocess.check_output("tasklist", shell=True).decode()
                if "chrome.exe" in processes:
                    return "Chrome"
                elif "firefox.exe" in processes:
                    return "Firefox"
                elif "msedge.exe" in processes:
                    return "Edge"
                elif "safari.exe" in processes:
                    return "Safari"
                else:
                    return "Unknown"
            except:
                return "Unknown"
        elif system == "Darwin":  # macOS
            try:
                processes = subprocess.check_output("ps -ax", shell=True).decode()
                if "Google Chrome" in processes:
                    return "Chrome"
                elif "Firefox" in processes:
                    return "Firefox"
                elif "Safari" in processes:
                    return "Safari"
                else:
                    return "Unknown"
            except:
                return "Unknown"
        else:  # Linux
            try:
                processes = subprocess.check_output("ps -A", shell=True).decode()
                if "chrome" in processes:
                    return "Chrome"
                elif "firefox" in processes:
                    return "Firefox"
                else:
                    return "Unknown"
            except:
                return "Unknown"
    
    def setup_keyboard_shortcuts(self):
        """Register keyboard shortcuts based on config"""
        # Remove any existing hotkeys first
        keyboard.unhook_all()
        
        # Register new hotkeys
        single_key = self.config.get("hotkey_single_screenshot", "alt+s")
        all_key = self.config.get("hotkey_all_screenshots", "alt+a")
        
        keyboard.add_hotkey(single_key, self.take_single_screenshot)
        keyboard.add_hotkey(all_key, self.take_all_screenshots)
        
        logging.info(f"Registered hotkeys: {single_key} for single screenshot, {all_key} for all tabs")
        
    def create_gui(self):
        """Create GUI for the application with modern styling"""
        # Use themed Tk for better appearance
        self.root = ThemedTk(theme=self.config.get("theme", "azure"))
        self.root.title("Advanced Tab Screenshot Tool")
        self.root.geometry(self.config.get("window_size", "600x650"))
        self.root.minsize(600, 600)
        
        # Create main container
        main_container = ttk.Frame(self.root, padding="20 20 20 20")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create header with logo
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # App title
        title_label = ttk.Label(header_frame, text="Advanced Tab Screenshot Tool", 
                               font=("Helvetica", 18, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create main tab
        main_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(main_tab, text="Main")
        
        # Create settings tab
        settings_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(settings_tab, text="Settings")
        
        # Create log tab
        log_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(log_tab, text="Logs")
        
        # Create help tab
        help_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(help_tab, text="Help")
        
        # =========== MAIN TAB ============
        
        # Status frame
        status_frame = ttk.LabelFrame(main_tab, text="Status", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        status_inner_frame = ttk.Frame(status_frame)
        status_inner_frame.pack(fill=tk.X)
        
        # Browser detection status
        browser_label = ttk.Label(status_inner_frame, text="Detected Browser:")
        browser_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        
        self.browser_value = ttk.Label(status_inner_frame, text=self.current_browser)
        self.browser_value.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Screenshot status
        screenshot_label = ttk.Label(status_inner_frame, text="Screenshots Taken:")
        screenshot_label.grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        
        self.screenshot_value = ttk.Label(status_inner_frame, text="0")
        self.screenshot_value.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Current saving directory
        dir_label = ttk.Label(status_inner_frame, text="Saving To:")
        dir_label.grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        
        self.dir_value = ttk.Label(status_inner_frame, text=self.screenshots_dir, width=50)
        self.dir_value.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Action buttons frame
        action_frame = ttk.LabelFrame(main_tab, text="Actions", padding=10)
        action_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Take screenshot buttons
        buttons_frame = ttk.Frame(action_frame)
        buttons_frame.pack(fill=tk.X, expand=True)
        
        # Create style for green button
        style = ttk.Style()
        style.configure("Green.TButton", foreground="green")
        style.configure("Blue.TButton", foreground="blue")
        
        single_btn = ttk.Button(buttons_frame, text="Screenshot Current Tab", 
                              command=self.take_single_screenshot, style="Green.TButton")
        single_btn.grid(row=0, column=0, padx=5, pady=10, sticky=tk.W+tk.E)
        
        all_btn = ttk.Button(buttons_frame, text="Screenshot All Tabs", 
                           command=self.take_all_screenshots, style="Blue.TButton")
        all_btn.grid(row=0, column=1, padx=5, pady=10, sticky=tk.W+tk.E)
        
        refresh_btn = ttk.Button(buttons_frame, text="Refresh Browser Detection", 
                               command=self.refresh_browser_detection)
        refresh_btn.grid(row=1, column=0, padx=5, pady=10, sticky=tk.W+tk.E)
        
        open_folder_btn = ttk.Button(buttons_frame, text="Open Screenshots Folder", 
                                   command=self.open_screenshots_folder)
        open_folder_btn.grid(row=1, column=1, padx=5, pady=10, sticky=tk.W+tk.E)
        
        # Configure grid columns to expand evenly
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)
        
        # Current operation frame
        operation_frame = ttk.LabelFrame(main_tab, text="Current Operation", padding=10)
        operation_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(operation_frame, text="Ready", font=("Helvetica", 10))
        self.status_label.pack(fill=tk.X, pady=(0, 10))
        
        # Progress bar
        self.progress = ttk.Progressbar(operation_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(0, 10))
        
        # Recent screenshots listbox with scrollbar
        recent_frame = ttk.LabelFrame(operation_frame, text="Recent Screenshots")
        recent_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(recent_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.recent_list = tk.Listbox(recent_frame, height=5, 
                                     yscrollcommand=scrollbar.set)
        self.recent_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.recent_list.yview)
        
        # Bind double-click to open selected screenshot
        self.recent_list.bind("<Double-1>", self.open_selected_screenshot)
        
        # =========== SETTINGS TAB ============
        
        # Directory settings
        dir_setting_frame = ttk.LabelFrame(settings_tab, text="Screenshot Storage", padding=10)
        dir_setting_frame.pack(fill=tk.X, pady=(0, 10))
        
        dir_path_frame = ttk.Frame(dir_setting_frame)
        dir_path_frame.pack(fill=tk.X, pady=5)
        
        dir_path_label = ttk.Label(dir_path_frame, text="Screenshots Directory:")
        dir_path_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.dir_entry = ttk.Entry(dir_path_frame)
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.dir_entry.insert(0, self.screenshots_dir)
        
        browse_btn = ttk.Button(dir_path_frame, text="Browse", command=self.choose_directory)
        browse_btn.pack(side=tk.RIGHT)
        
        # Session subfolder option
        subfolder_frame = ttk.Frame(dir_setting_frame)
        subfolder_frame.pack(fill=tk.X, pady=5)
        
        self.subfolder_var = tk.BooleanVar(value=self.create_subfolder_per_session)
        subfolder_check = ttk.Checkbutton(subfolder_frame, text="Create subfolder for each session", 
                                        variable=self.subfolder_var)
        subfolder_check.pack(side=tk.LEFT)
        
        # Auto-open folder option
        auto_open_frame = ttk.Frame(dir_setting_frame)
        auto_open_frame.pack(fill=tk.X, pady=5)
        
        self.auto_open_var = tk.BooleanVar(value=self.auto_open_folder)
        auto_open_check = ttk.Checkbutton(auto_open_frame, text="Automatically open folder after screenshots", 
                                        variable=self.auto_open_var)
        auto_open_check.pack(side=tk.LEFT)
        
        # Timing settings
        timing_frame = ttk.LabelFrame(settings_tab, text="Timing Settings", padding=10)
        timing_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Delay before screenshot
        pre_delay_frame = ttk.Frame(timing_frame)
        pre_delay_frame.pack(fill=tk.X, pady=5)
        
        pre_delay_label = ttk.Label(pre_delay_frame, text="Delay before screenshot (seconds):")
        pre_delay_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.pre_delay_var = tk.DoubleVar(value=self.delay_before_screenshot)
        pre_delay_spinner = ttk.Spinbox(pre_delay_frame, from_=0.1, to=5.0, increment=0.1, 
                                      textvariable=self.pre_delay_var, width=5)
        pre_delay_spinner.pack(side=tk.LEFT)
        
        # Delay between tabs
        tab_delay_frame = ttk.Frame(timing_frame)
        tab_delay_frame.pack(fill=tk.X, pady=5)
        
        tab_delay_label = ttk.Label(tab_delay_frame, text="Delay between tabs (seconds):")
        tab_delay_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.tab_delay_var = tk.DoubleVar(value=self.delay_between_tabs)
        tab_delay_spinner = ttk.Spinbox(tab_delay_frame, from_=0.3, to=5.0, increment=0.1, 
                                      textvariable=self.tab_delay_var, width=5)
        tab_delay_spinner.pack(side=tk.LEFT)
        
        # Method settings
        method_frame = ttk.LabelFrame(settings_tab, text="URL Detection Method", padding=10)
        method_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.method_var = tk.StringVar(value=self.url_detection_method)
        
        clipboard_radio = ttk.Radiobutton(method_frame, text="Clipboard (works with most browsers)", 
                                        variable=self.method_var, value="clipboard")
        clipboard_radio.pack(anchor=tk.W, pady=2)
        
        advanced_radio = ttk.Radiobutton(method_frame, text="Advanced (browser-specific optimizations)", 
                                       variable=self.method_var, value="advanced")
        advanced_radio.pack(anchor=tk.W, pady=2)
        
        ocr_radio = ttk.Radiobutton(method_frame, text="OCR (experimental, requires tesseract)", 
                                  variable=self.method_var, value="ocr")
        ocr_radio.pack(anchor=tk.W, pady=2)
        
        # Hotkey settings
        hotkey_frame = ttk.LabelFrame(settings_tab, text="Keyboard Shortcuts", padding=10)
        hotkey_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Single screenshot hotkey
        single_hotkey_frame = ttk.Frame(hotkey_frame)
        single_hotkey_frame.pack(fill=tk.X, pady=5)
        
        single_hotkey_label = ttk.Label(single_hotkey_frame, text="Single screenshot:")
        single_hotkey_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.single_hotkey_var = tk.StringVar(value=self.config.get("hotkey_single_screenshot", "alt+s"))
        single_hotkey_entry = ttk.Entry(single_hotkey_frame, textvariable=self.single_hotkey_var, width=10)
        single_hotkey_entry.pack(side=tk.LEFT)
        
        # All screenshots hotkey
        all_hotkey_frame = ttk.Frame(hotkey_frame)
        all_hotkey_frame.pack(fill=tk.X, pady=5)
        
        all_hotkey_label = ttk.Label(all_hotkey_frame, text="All tabs screenshot:")
        all_hotkey_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.all_hotkey_var = tk.StringVar(value=self.config.get("hotkey_all_screenshots", "alt+a"))
        all_hotkey_entry = ttk.Entry(all_hotkey_frame, textvariable=self.all_hotkey_var, width=10)
        all_hotkey_entry.pack(side=tk.LEFT)
        
        # Theme selection
        theme_frame = ttk.LabelFrame(settings_tab, text="Appearance", padding=10)
        theme_frame.pack(fill=tk.X, pady=(0, 10))
        
        theme_label = ttk.Label(theme_frame, text="Theme:")
        theme_label.pack(side=tk.LEFT, padx=(0, 10))
        
        available_themes = self.root.get_themes()
        self.theme_var = tk.StringVar(value=self.config.get("theme", "azure"))
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var, 
                                 values=available_themes, width=15)
        theme_combo.pack(side=tk.LEFT)
        
        # Save settings button
        save_settings_btn = ttk.Button(settings_tab, text="Save Settings", 
                                     command=self.save_settings, style="Green.TButton")
        save_settings_btn.pack(pady=10)
        
        # =========== LOGS TAB ============
        
        # Log display
        log_frame = ttk.Frame(log_tab)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_display = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=20)
        self.log_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Load log button
        log_button_frame = ttk.Frame(log_tab)
        log_button_frame.pack(fill=tk.X)
        
        refresh_log_btn = ttk.Button(log_button_frame, text="Refresh Logs", 
                                   command=self.load_logs)
        refresh_log_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_log_btn = ttk.Button(log_button_frame, text="Clear Logs", 
                                 command=self.clear_logs)
        clear_log_btn.pack(side=tk.LEFT)
        
        # =========== HELP TAB ============
        
        help_content = ttk.Frame(help_tab)
        help_content.pack(fill=tk.BOTH, expand=True)
        
        # Help text
        help_text = scrolledtext.ScrolledText(help_content, wrap=tk.WORD, height=20)
        help_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Insert help content
        help_content_text = """
        # Advanced Tab Screenshot Tool - Help
        
        ## Keyboard Shortcuts
        - **Single Tab Screenshot:** Alt+S (customizable)
        - **All Tabs Screenshot:** Alt+A (customizable)
        
        ## Common Issues
        
        ### "Couldn't get URL" Error
        This usually happens when:
        1. The browser's address bar is not accessible
        2. The tab has not fully loaded
        3. The window is not in focus
        
        **Solutions:**
        - Try changing the URL detection method in Settings
        - Increase the delay before screenshot
        - Make sure the browser window is active and in focus
        
        ### Screenshots of Wrong Tabs
        This can happen when:
        1. Tab switching is too fast
        2. Browser is still loading content
        
        **Solutions:**
        - Increase the delay between tabs in Settings
        - Use the "Advanced" URL detection method
        
        ## Tips for Best Results
        
        1. **Browser Focus:** Make sure your browser is the active window
        2. **Wait for Loading:** Let pages fully load before taking screenshots
        3. **Adjust Timing:** Different browsers may need different delay settings
        4. **Check Browser Compatibility:** Some features work better with specific browsers
        
        ## Support
        
        For problems or suggestions, check the log tab for error details.
        """
        
        help_text.insert(tk.END, help_content_text)
        help_text.config(state=tk.DISABLED)  # Make read-only
        
        # =========== FOOTER ============
        
        # Footer with status and version
        footer_frame = ttk.Frame(main_container)
        footer_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Status message
        self.footer_status = ttk.Label(footer_frame, text="Ready")
        self.footer_status.pack(side=tk.LEFT)
        
        # Version info
        version_label = ttk.Label(footer_frame, text="Version 2.0")
        version_label.pack(side=tk.RIGHT)
        
        # Initial load of logs
        self.load_logs()
        
        # Center window on screen
        self.center_window()
    
    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def choose_directory(self):
        """Choose directory for screenshots"""
        directory = filedialog.askdirectory(initialdir=self.screenshots_dir)
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)
    
    def save_settings(self):
        """Save all settings from UI to config"""
        # Get values from UI
        new_dir = self.dir_entry.get().strip()
        
        # Validate directory
        if not new_dir or not os.path.isdir(new_dir):
            messagebox.showerror("Error", "Invalid directory path. Please select a valid directory.")
            return
        
        # Update values
        self.screenshots_dir = new_dir
        self.delay_before_screenshot = self.pre_delay_var.get()
        self.delay_between_tabs = self.tab_delay_var.get()
        self.auto_open_folder = self.auto_open_var.get()
        self.url_detection_method = self.method_var.get()
        self.create_subfolder_per_session = self.subfolder_var.get()
        
        # Update hotkeys
        old_single_hotkey = self.config.get("hotkey_single_screenshot", "alt+s")
        old_all_hotkey = self.config.get("hotkey_all_screenshots", "alt+a")
        
        new_single_hotkey = self.single_hotkey_var.get()
        new_all_hotkey = self.all_hotkey_var.get()
        
        # Update theme
        old_theme = self.config.get("theme", "azure")
        new_theme = self.theme_var.get()
        
        # Save to config
        self.config["screenshots_dir"] = self.screenshots_dir
        self.config["delay_before_screenshot"] = self.delay_before_screenshot
        self.config["delay_between_tabs"] = self.delay_between_tabs
        self.config["auto_open_folder"] = self.auto_open_folder
        self.config["url_detection_method"] = self.url_detection_method
        self.config["create_subfolder_per_session"] = self.create_subfolder_per_session
        self.config["hotkey_single_screenshot"] = new_single_hotkey
        self.config["hotkey_all_screenshots"] = new_all_hotkey
        self.config["theme"] = new_theme
        
        # Save config to file
        if self.save_config():
            # Update UI
            self.dir_value.config(text=self.screenshots_dir)
            self.show_status("Settings saved successfully", "success")
            
            # Re-register hotkeys if they changed
            if old_single_hotkey != new_single_hotkey or old_all_hotkey != new_all_hotkey:
                self.setup_keyboard_shortcuts()
            
            # Change theme if it changed
            if old_theme != new_theme:
                try:
                    self.root.set_theme(new_theme)
                    messagebox.showinfo("Theme Changed", 
                                       "Theme will be fully applied next time you start the application.")
                except:
                    logging.error(f"Failed to apply theme: {new_theme}")
        else:
            messagebox.showerror("Error", "Failed to save settings. Check logs for details.")
    
    def load_logs(self):
        """Load logs from file into the display"""
        self.log_display.config(state=tk.NORMAL)
        self.log_display.delete(1.0, tk.END)
        
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    # Get the last 100 lines (or fewer if file is smaller)
                    lines = f.readlines()
                    last_lines = lines[-100:] if len(lines) > 100 else lines
                    
                    self.log_display.insert(tk.END, "".join(last_lines))
            else:
                self.log_display.insert(tk.END, "No log file found.")
        except Exception as e:
            self.log_display.insert(tk.END, f"Error loading logs: {str(e)}")
        
        # Scroll to the end
        self.log_display.see(tk.END)
        self.log_display.config(state=tk.DISABLED)
    
    def clear_logs(self):
        """Clear logs file"""
        try:
            with open(self.log_file, 'w') as f:
                f.write(f"Logs cleared on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            self.load_logs()
            self.show_status("Logs cleared", "info")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear logs: {str(e)}")
    
    def refresh_browser_detection(self):
        """Refresh the browser detection"""
        self.current_browser = self.detect_browser()
        self.browser_value.config(text=self.current_browser)
        self.show_status(f"Browser detection refreshed: {self.current_browser}", "info")
        logging.info(f"Browser detection refreshed: {self.current_browser}")
    
    def create_session_folder(self):
        """Create a new folder for this session if enabled"""
        if not self.create_subfolder_per_session:
            return self.screenshots_dir
        
        # Create session folder with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_folder = os.path.join(self.screenshots_dir, f"session_{timestamp}")
        os.makedirs(session_folder, exist_ok=True)
        
        self.current_session_folder = session_folder
        return session_folder
    
    def get_active_url(self):
        """Get URL from current browser tab using selected method"""
        if self.url_detection_method == "clipboard":
            return self.get_url_via_clipboard()
        elif self.url_detection_method == "advanced":
            return self.browser_adapter.get_url_browser_specific()
        elif self.url_detection_method == "ocr":
            # OCR method would be implemented here
            # For now, fall back to clipboard method
            logging.warning("OCR method not fully implemented, falling back to clipboard method")
            return self.get_url_via_clipboard()
        else:
            return self.get_url_via_clipboard()  # Default fallback
    
    def get_url_via_clipboard(self):
        """Get URL using clipboard method (most compatible)"""
        try:
            # Store original clipboard content
            original_clipboard = pyperclip.paste()
            
            # Clear clipboard to ensure we get fresh content
            pyperclip.copy('')
            time.sleep(0.1)
            
            # Select address bar with browser-specific method if possible
            if self.current_browser == "Chrome" or self.current_browser == "Edge":
                keyboard.press_and_release('alt+d')
            elif self.current_browser == "Firefox":
                keyboard.press_and_release('ctrl+l')
            else:
                # Generic method as fallback
                keyboard.press_and_release('ctrl+l')
            
            # Wait a bit for the address bar to be selected
            time.sleep(self.delay_before_screenshot)
            
            # Copy the URL
            keyboard.press_and_release('ctrl+c')
            time.sleep(0.2)  # Wait for clipboard to update
            
            url = pyperclip.paste()
            
            # Restore original clipboard content
            pyperclip.copy(original_clipboard)
            
            # Simple validation to ensure we got a URL
            if url and (url.startswith('http://') or url.startswith('https://') or url.startswith('file://')):
                logging.info(f"Successfully detected URL: {url[:50]}...")
                return url
            else:
                logging.warning(f"Retrieved text doesn't look like a URL: {url[:50]}")
                return None
            
        except Exception as e:
            logging.error(f"Error getting URL via clipboard: {str(e)}")
            return None
    
    def clean_filename(self, url):
        """Convert URL to valid filename with improved handling"""
        if not url:
            # Generate a timestamp-based filename if URL is not available
            return f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        try:
            # Parse the URL
            parsed = urlparse(url)
            
            # Start with the hostname
            filename = parsed.netloc
            
            # Add the path, but clean it up
            path = parsed.path
            if path and path != "/":
                # Replace slashes with underscores
                path = path.replace('/', '_')
                # Remove trailing underscore if present
                if path.endswith('_'):
                    path = path[:-1]
                filename += path
            
            # Remove protocol and www
            filename = re.sub(r'^https?://(www\.)?', '', filename)
            
            # Replace special chars with underscores
            filename = re.sub(r'[\\/*?:"<>|]', '_', filename)
            
            # Remove duplicate underscores
            filename = re.sub(r'_+', '_', filename)
            
            # If filename is too long, truncate it
            if len(filename) > 200:
                filename = filename[:200]
            
            # Remove trailing punctuation and underscores
            filename = re.sub(r'[._-]+$', '', filename)
            
            # Add timestamp to ensure uniqueness
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Add .png extension
            filename = f"{filename}_{timestamp}.png"
            
            # If filename still invalid, use timestamp
            if not filename or filename == ".png":
                filename = f"screenshot_{timestamp}.png"
                
            return filename
            
        except Exception as e:
            logging.error(f"Error cleaning filename: {str(e)}")
            # Fallback to timestamp
            return f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    
    def take_single_screenshot(self):
        """Take screenshot of current tab and save with URL as filename"""
        if self.operation_in_progress:
            self.show_status("Operation already in progress", "warning")
            return
            
        self.operation_in_progress = True
        threading.Thread(target=self._take_single_screenshot_thread).start()
    
    def _take_single_screenshot_thread(self):
        """Thread function to take single screenshot"""
        try:
            # Start progress indication
            self.root.after(0, lambda: self.progress.start())
            self.show_status("Taking screenshot...", "info")
            
            # Make sure the session folder exists if needed
            if self.create_subfolder_per_session and not self.current_session_folder:
                target_dir = self.create_session_folder()
            else:
                target_dir = self.current_session_folder if self.current_session_folder else self.screenshots_dir
            
            # Wait before taking screenshot
            time.sleep(self.delay_before_screenshot)
            
            # Get URL
            url = self.get_active_url()
            if not url:
                self.show_status("Couldn't get URL - trying alternative method", "warning")
                # Try alternative method as fallback
                if self.url_detection_method != "clipboard":
                    url = self.get_url_via_clipboard()
                
            # Generate filename from URL
            filename = self.clean_filename(url)
            filepath = os.path.join(target_dir, filename)
            
            # Log the filepath
            logging.info(f"Saving screenshot to: {filepath}")
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            
            # Update screenshot count
            self.screenshot_count += 1
            self.root.after(0, lambda: self.screenshot_value.config(text=str(self.screenshot_count)))
            
            # Add to recent list
            self.root.after(0, lambda: self.recent_list.insert(0, filename))
            
            # Show success message
            self.show_status(f"Screenshot saved: {filename}", "success")
            
            # Auto-open folder if enabled
            if self.auto_open_folder:
                self.open_screenshots_folder()
            
        except Exception as e:
            logging.error(f"Error taking screenshot: {str(e)}")
            self.show_status(f"Error: {str(e)}", "error")
        finally:
            self.operation_in_progress = False
            self.root.after(0, lambda: self.progress.stop())
    
    def take_all_screenshots(self):
        """Take screenshots of all tabs sequentially"""
        if self.operation_in_progress:
            self.show_status("Operation already in progress", "warning")
            return
            
        self.operation_in_progress = True
        threading.Thread(target=self._take_all_screenshots_thread).start()
    
    def _take_all_screenshots_thread(self):
        """Thread function to take screenshots of all tabs"""
        try:
            # Start progress indication
            self.root.after(0, lambda: self.progress.start())
            self.show_status("Starting to capture all tabs...", "info")
            
            # Make sure the session folder exists if needed
            if self.create_subfolder_per_session:
                target_dir = self.create_session_folder()
            else:
                target_dir = self.screenshots_dir
                
            # First tab
            url = self.get_active_url()
            if not url:
                self.show_status("Couldn't get URL for first tab - trying alternative method", "warning")
                # Try alternative method as fallback
                if self.url_detection_method != "clipboard":
                    url = self.get_url_via_clipboard()
            
            # If still no URL, continue anyway but log it
            if not url:
                logging.warning("Couldn't get URL for first tab - continuing with timestamp filename")
                
            # Take screenshot of first tab
            filename = self.clean_filename(url)
            filepath = os.path.join(target_dir, filename)
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            
            # Update UI
            self.screenshot_count += 1
            self.root.after(0, lambda: self.screenshot_value.config(text=str(self.screenshot_count)))
            self.root.after(0, lambda: self.recent_list.insert(0, filename))
            
            # Track visited URLs to avoid loops
            visited_urls = {url} if url else set()
            first_url = url
            tab_count = 1
            
            # Use the appropriate key sequence for tab switching
            if self.current_browser == "Firefox":
                tab_key = 'ctrl+tab'
            else:  # Chrome, Edge, and most others
                tab_key = 'ctrl+tab'
            
            # Move to next tab
            keyboard.press_and_release(tab_key)
            time.sleep(self.delay_between_tabs)  # Wait for tab to switch
            
            # Maximum number of tabs to prevent infinite loop
            max_tabs = 100
            
            # Keep going until we cycle back to first tab or hit max tabs
            while tab_count < max_tabs:
                url = self.get_active_url()
                
                # If we can't get URL, still take the screenshot but log it
                if not url:
                    logging.warning(f"Couldn't get URL for tab {tab_count+1}")
                    # Try alternative method
                    if self.url_detection_method != "clipboard":
                        url = self.get_url_via_clipboard()
                
                # If returned to first URL, we've completed the cycle
                if url and url in visited_urls:
                    logging.info(f"Detected return to previously visited URL: {url[:50]}...")
                    break
                
                # Add URL to visited set if we have one
                if url:
                    visited_urls.add(url)
                
                # Take screenshot regardless of URL detection
                tab_count += 1
                
                # Update status
                self.show_status(f"Capturing tab {tab_count}...", "info")
                
                # Pause before taking screenshot
                time.sleep(self.delay_before_screenshot)
                
                # Take screenshot
                filename = self.clean_filename(url)
                filepath = os.path.join(target_dir, filename)
                screenshot = pyautogui.screenshot()
                screenshot.save(filepath)
                
                # Update UI
                self.screenshot_count += 1
                self.root.after(0, lambda: self.screenshot_value.config(text=str(self.screenshot_count)))
                self.root.after(0, lambda: self.recent_list.insert(0, filename))
                
                # Move to next tab
                keyboard.press_and_release(tab_key)
                time.sleep(self.delay_between_tabs)  # Wait for tab to switch
            
            self.show_status(f"Completed capturing {tab_count} tabs", "success")
            
            # Auto-open folder if enabled
            if self.auto_open_folder:
                self.open_screenshots_folder()
            
        except Exception as e:
            logging.error(f"Error capturing all tabs: {str(e)}")
            self.show_status(f"Error: {str(e)}", "error")
        finally:
            self.operation_in_progress = False
            self.root.after(0, lambda: self.progress.stop())
    
    def open_screenshots_folder(self):
        """Open screenshots folder in file explorer"""
        try:
            target_dir = self.current_session_folder if self.current_session_folder else self.screenshots_dir
            
            if os.path.exists(target_dir):
                if platform.system() == 'Windows':  # Windows
                    os.startfile(target_dir)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.call(['open', target_dir])
                else:  # Linux
                    subprocess.call(['xdg-open', target_dir])
                    
                logging.info(f"Opened screenshots folder: {target_dir}")
            else:
                messagebox.showerror("Error", "Screenshots directory not found.")
                logging.error(f"Screenshots directory not found: {target_dir}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {str(e)}")
            logging.error(f"Error opening folder: {str(e)}")
    
    def open_selected_screenshot(self, event):
        """Open the selected screenshot from the recent list"""
        try:
            selection = self.recent_list.curselection()
            if not selection:
                return
                
            filename = self.recent_list.get(selection[0])
            target_dir = self.current_session_folder if self.current_session_folder else self.screenshots_dir
            filepath = os.path.join(target_dir, filename)
            
            if os.path.exists(filepath):
                if platform.system() == 'Windows':  # Windows
                    os.startfile(filepath)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.call(['open', filepath])
                else:  # Linux
                    subprocess.call(['xdg-open', filepath])
            else:
                messagebox.showerror("Error", f"File not found: {filepath}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image: {str(e)}")
    
    def show_status(self, message, status_type="info"):
        """Show status message with appropriate styling"""
        # Colors based on status type
        colors = {
            "info": "#3897f1",     # Blue
            "success": "#28a745",  # Green
            "warning": "#ffc107",  # Yellow
            "error": "#dc3545"     # Red
        }
        
        color = colors.get(status_type, colors["info"])
        
        # Log the message
        if status_type == "error":
            logging.error(message)
        elif status_type == "warning":
            logging.warning(message)
        else:
            logging.info(message)
        
        # Update status labels in the main thread
        self.root.after(0, lambda: self._update_status_labels(message, color))
        
        # Clear success/info messages after 5 seconds
        if status_type in ["success", "info"]:
            self.root.after(5000, lambda: self._update_status_labels("Ready", "#28a745"))
    
    def _update_status_labels(self, message, color):
        """Update all status labels (to be called in main thread)"""
        self.status_label.config(text=message, foreground=color)
        self.footer_status.config(text=message, foreground=color)
    
    def run(self):
        """Run the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """Handle application closing"""
        try:
            # Save settings before closing
            self.save_config()
            
            # Unhook keyboard shortcuts
            keyboard.unhook_all()
            
            # Close the window
            self.root.destroy()
        except Exception as e:
            logging.error(f"Error during shutdown: {str(e)}")
            self.root.destroy()


class BrowserAdapter:
    """Adapter class for browser-specific implementations"""
    
    def __init__(self, app):
        self.app = app
        self.browser = app.current_browser
    
    def get_url_browser_specific(self):
        """Get URL using browser-specific methods"""
        if self.browser == "Chrome":
            return self.get_url_chrome()
        elif self.browser == "Firefox":
            return self.get_url_firefox()
        elif self.browser == "Edge":
            return self.get_url_edge()
        elif self.browser == "Safari":
            return self.get_url_safari()
        else:
            # Fall back to clipboard method for unknown browsers
            return self.app.get_url_via_clipboard()
    
    def get_url_chrome(self):
        """Get URL from Chrome browser"""
        try:
            # Chrome uses Alt+D to select address bar
            keyboard.press_and_release('alt+d')
            time.sleep(0.2)
            
            # Copy URL
            keyboard.press_and_release('ctrl+c')
            time.sleep(0.2)
            
            # Get from clipboard
            url = pyperclip.paste()
            
            # Check if it's a URL
            if url and (url.startswith('http://') or url.startswith('https://') or url.startswith('file://')):
                return url
            
            # If not, try with Ctrl+L instead
            keyboard.press_and_release('ctrl+l')
            time.sleep(0.2)
            keyboard.press_and_release('ctrl+c')
            time.sleep(0.2)
            
            url = pyperclip.paste()
            if url and (url.startswith('http://') or url.startswith('https://') or url.startswith('file://')):
                return url
            
            return None
        except Exception as e:
            logging.error(f"Error getting URL from Chrome: {str(e)}")
            return None
    
    def get_url_firefox(self):
        """Get URL from Firefox browser"""
        try:
            # Firefox uses Ctrl+L to select address bar
            keyboard.press_and_release('ctrl+l')
            time.sleep(0.2)
            
            # Copy URL
            keyboard.press_and_release('ctrl+c')
            time.sleep(0.2)
            
            # Get from clipboard
            url = pyperclip.paste()
            
            # Check if it's a URL
            if url and (url.startswith('http://') or url.startswith('https://') or url.startswith('file://')):
                return url
            
            # If not, try with Alt+D instead
            keyboard.press_and_release('alt+d')
            time.sleep(0.2)
            keyboard.press_and_release('ctrl+c')
            time.sleep(0.2)
            
            url = pyperclip.paste()
            if url and (url.startswith('http://') or url.startswith('https://') or url.startswith('file://')):
                return url
            
            return None
        except Exception as e:
            logging.error(f"Error getting URL from Firefox: {str(e)}")
            return None
    
    def get_url_edge(self):
        """Get URL from Edge browser (similar to Chrome)"""
        try:
            # Edge uses Alt+D or F4 to select address bar
            keyboard.press_and_release('alt+d')
            time.sleep(0.2)
            
            # Copy URL
            keyboard.press_and_release('ctrl+c')
            time.sleep(0.2)
            
            # Get from clipboard
            url = pyperclip.paste()
            
            # Check if it's a URL
            if url and (url.startswith('http://') or url.startswith('https://') or url.startswith('file://')):
                return url
            
            # If not, try with F4 instead
            keyboard.press_and_release('f4')
            time.sleep(0.2)
            keyboard.press_and_release('ctrl+c')
            time.sleep(0.2)
            
            url = pyperclip.paste()
            if url and (url.startswith('http://') or url.startswith('https://') or url.startswith('file://')):
                return url
            
            return None
        except Exception as e:
            logging.error(f"Error getting URL from Edge: {str(e)}")
            return None
    
    def get_url_safari(self):
        """Get URL from Safari browser (macOS)"""
        try:
            # Safari uses Cmd+L to select address bar
            if platform.system() == 'Darwin':  # macOS
                keyboard.press_and_release('command+l')
            else:
                keyboard.press_and_release('ctrl+l')  # Fallback for Safari on Windows (rare)
                
            time.sleep(0.2)
            
            # Copy URL
            if platform.system() == 'Darwin':  # macOS
                keyboard.press_and_release('command+c')
            else:
                keyboard.press_and_release('ctrl+c')
                
            time.sleep(0.2)
            
            # Get from clipboard
            url = pyperclip.paste()
            
            # Check if it's a URL
            if url and (url.startswith('http://') or url.startswith('https://') or url.startswith('file://')):
                return url
            
            return None
        except Exception as e:
            logging.error(f"Error getting URL from Safari: {str(e)}")
            return None


if __name__ == "__main__":
    app = AdvancedTabScreenshotTool()
    app.run()