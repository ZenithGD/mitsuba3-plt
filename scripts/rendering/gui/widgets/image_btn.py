import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class ImageButton(ttk.Frame):
        
    def __init__(self, image_path, text, parent = None, command = None, **kwargs):

        super().__init__(parent, **kwargs)  # Initialize the parent frame
        
        # Create a PhotoImage object from the provided image path
        self.photo = tk.PhotoImage(file=image_path)
        
        # Optionally resize the image (subsample) to fit on the button
        self.photoimage = self.photo.subsample(15)
        
        # Create the button with the image and text
        self.button = ttk.Button(
            self, 
            text=text, 
            image=self.photoimage, 
            compound="left",  # Align image on the left side of the text
            command=command,
            **kwargs
        )
        
        # Pack the button in the frame
        self.button.pack(side="top")