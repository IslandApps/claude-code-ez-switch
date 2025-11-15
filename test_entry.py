import tkinter as tk

def test_entry():
    root = tk.Tk()
    root.geometry("400x200")
    
    # Simple test entry
    entry = tk.Entry(root, bg="#2d2d2d", fg="#ffffff", 
                     insertbackground="#ffffff", relief=tk.FLAT,
                     font=("Arial", 10), bd=0, show="*")
    entry.pack(fill=tk.X, padx=15, pady=(20, 10), ipady=8)
    
    # Test label
    label = tk.Label(root, text="Try typing in this field:", bg="#1e1e1e", fg="#ffffff")
    label.pack(pady=(10, 0))
    
    # Focus the entry
    entry.focus_set()
    
    root.mainloop()

if __name__ == "__main__":
    test_entry()