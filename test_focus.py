#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import platform

IS_LINUX = platform.system() == "Linux"

def test_entry_focus(event):
    """Test entry focus"""
    widget = event.widget
    print(f"Focus event on: {widget}")
    widget.focus_set()

def main():
    root = tk.Tk()
    root.title("Focus Test")
    root.geometry("400x300")
    
    if IS_LINUX:
        print("Linux detected - testing basic focus")
    
    # Create a simple entry
    entry = tk.Entry(root, width=40)
    entry.pack(pady=20)
    
    # Bind focus event
    entry.bind('<Button-1>', test_entry_focus)
    
    # Add a label
    label = tk.Label(root, text="Click in the entry field above to test focus")
    label.pack()
    
    # Add a button
    button = tk.Button(root, text="Test Button", command=lambda: print("Button clicked"))
    button.pack(pady=10)
    
    print("Test window created - should be visible now")
    root.mainloop()

if __name__ == "__main__":
    main()