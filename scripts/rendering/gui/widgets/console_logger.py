import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class PrintLogger(tk.Frame):
    def __init__(self, parent=None, console_height=30, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent

        self.hscrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL)
        self.vscrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL)
        
        # Create the Text widget with console-like styling
        self.textbox = tk.Text(self, 
                               wrap=tk.WORD, 
                               bg='black', 
                               fg='white', 
                               font=('Courier', 10), 
                               bd=0,
                               xscrollcommand=self.hscrollbar.set,
                               yscrollcommand=self.vscrollbar.set)
        self.hscrollbar.config(command=self.textbox.xview)
        self.hscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.vscrollbar.config(command=self.textbox.yview)
        self.vscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.textbox.pack(fill="both", expand=True, padx=5, pady=5)

    def write(self, text):
        self.textbox.insert(tk.END, text + "\n")  # Insert the text at the end
        self.textbox.see(tk.END)  # Scroll to the end of the textbox

    def flush(self):
        """This method is required by file-like objects"""
        pass

    def clear(self):
        """Clear the textbox content"""
        self.textbox.delete(1.0, tk.END)