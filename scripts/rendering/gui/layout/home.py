import importlib.resources as resources
import mitsuba as mi
import json
import pprint 
import time
from PIL import ImageTk, Image

from ..controller import SceneController, RendererController, props_to_dict

import os
import tkinter as tk
import ttkbootstrap as ttk
from tkinter import filedialog as fd
from ttkbootstrap.constants import *

from ..widgets import *

class Home(ttk.Frame):

    def __init__(self, 
        scene_ctrl,
        renderer_ctrl,
        parent=None, 
        **kwargs):

        self.assets_path = os.path.join(resources.files(__package__), "..", "assets")

        ttk.Frame.__init__(self, parent)

        self.parent = parent

        self.current_scene = None
        self.render_result = None

        self.scene_ctrl : SceneController = scene_ctrl
        self.renderer_ctrl : RendererController = renderer_ctrl

    def display(self):

        # create menu
        menu = self.__create_menu()
        menu.pack(side=tk.TOP, anchor=tk.NW, fill='x')

        # Separate console and tooling
        horz_paned_window = ttk.PanedWindow(self.parent, orient=VERTICAL)
        horz_paned_window.pack(fill=BOTH, expand=True)

        self.tool_frame = ttk.Frame(self.parent)
        self.tool_frame.pack(fill="both", expand=True)
        self.__create_tool_views(self.tool_frame)

        # add bottom frame with workspace and console

        self.bottom_frame = ttk.Frame(self.parent)
        self.__create_bottom_frame(self.bottom_frame)

        # Add frames to the PanedWindow with resizable option
        horz_paned_window.add(self.tool_frame, weight=1)  # left frame can resize
        horz_paned_window.add(self.bottom_frame, weight=1)  # right frame can resize

    def __create_tool_views(self, parent):
        # paned window allows to resize in one direction
        tool_paned_window = ttk.PanedWindow(parent, orient=HORIZONTAL)
        tool_paned_window.pack(fill=BOTH, expand=True)

        # Add two frames to the PanedWindow
        self.frame_left, self.label_frame_left = self.__create_scene_edit(tool_paned_window)
        self.frame_right, self.label_frame_right = self.__create_render_view(tool_paned_window)

        self.scene_view = SceneView(self.label_frame_left)

        # Add frames to the PanedWindow with resizable option
        tool_paned_window.add(self.frame_left, weight=1)  # left frame can resize
        tool_paned_window.add(self.frame_right, weight=1)  # right frame can resize

    def __create_menu(self):
        
        # frame on top
        menu_frame = ttk.Frame()

        # Load scene button
        load_cmd = lambda : self.__load_scene()
        load_btn = ImageButton(
            os.path.join(self.assets_path, "load.png"), "Load scene", menu_frame,
            bootstyle="dark",
            command=load_cmd)
        
        load_btn.pack(side=tk.LEFT)
        
        # Save scene button
        save_cmd = lambda : self.__save_scene()
        save_btn = ImageButton(
            os.path.join(self.assets_path, "save.png"), "Save scene", menu_frame,
            bootstyle="dark",
            command=save_cmd)
        
        save_btn.pack(side=tk.LEFT)

        return menu_frame
        
    def __create_scene_edit(self, pane, ix = 200, iy = 400):
        
        scene_edit = ttk.Frame(pane, width=ix, height=iy)
        scene_edit.pack(fill="both")

        lf = ttk.LabelFrame(scene_edit, text="Scene Edit", width=ix, height=iy)
        lf.pack(fill="both", padx=10, pady=10, expand=True)
            
        return scene_edit, lf
        
    def __create_render_view(self, pane, ix = 200, iy = 400):
        
        render_view = ttk.Frame(pane, width=ix, height=iy)
        render_view.pack(fill="both")

        lf = ttk.LabelFrame(render_view, text="Render View", width=ix, height=iy)
        lf.pack(fill="both", padx=10, pady=10, expand=True)

        self.render_window = ttk.Frame(lf)
        self.render_window.pack(fill="both", expand=True)

        # Save scene button
        render_cmd = lambda : self.__render_current_scene()
        render_btn = ImageButton(
            os.path.join(self.assets_path, "render.png"), "Render scene", self.render_window,
            bootstyle="dark",
            command=render_cmd)
        
        render_btn.pack(side=tk.BOTTOM)

        return render_view, lf
    
    def __create_bottom_frame(self, parent):
        # add tabs
        notebook = ttk.Notebook(parent)
        notebook.pack(pady=10, fill="both", expand=True)

        # console frame
        console_frame = ttk.Frame()
        console_frame.pack(fill="both", expand=True)

        self.console = PrintLogger(console_frame)
        self.console.pack(fill="x")

        # workspace frame
        workspace_frame = ttk.Frame()

        notebook.add(workspace_frame, text='Workspace')
        notebook.add(console_frame, text='Console')
        
    def __save_scene(self):
        pass

    def __load_scene(self):
        scene_path = fd.askopenfilename()

        if scene_path:
            self.console.write(f"Loading scene...")
            self.current_scene = self.scene_ctrl.load_scene(scene_path)
            self.current_scene_params = props_to_dict(self.current_scene)

            self.scene_view.update_scene(scene_path, self.current_scene_params, self.current_scene)
            self.console.write(f"done...")

    def __render_current_scene(self):

        self.console.write(f"{self.render_result is None}")
        if self.render_result is None:
            self.render_result = ttk.Label(self.render_window, text="Rendering...")
            self.render_result.pack(fill=ttk.BOTH, expand=True)

        self.console.write(f"Rendering scene...")
        start = time.perf_counter()
        def on_finish(result):
            elapsed = time.perf_counter() - start

            self.console.write(f"Done. ({elapsed} s.)")

            # destroy previous render
            if self.render_result:
                self.render_result.destroy()
                self.render_result = None
        
            self.render_result = ttk.Frame(self.render_window)
            self.render_result.pack(side=tk.TOP, fill="both", expand=True)

            mi.util.write_bitmap('result.png', result, write_async=False)

            im = Image.open('result.png')
            self.rendered_tkimage = ImageTk.PhotoImage(im)
            image_panel = ttk.Label(self.render_result, image = self.rendered_tkimage)
            image_panel.pack(side = "bottom", fill = "both", expand = "yes", anchor=ttk.CENTER)

            # Manually trigger the resize logic after the image is loaded
            self.resize_image({'height': self.render_result.winfo_height()})

            # Bind resize event to adjust image size dynamically
            self.render_result.bind("<Configure>", self.resize_image)

        if self.current_scene:

            params = { "integrator" : "plt" }

            self.renderer_ctrl.render_scene(self.current_scene, params, on_finish)
        else:
            self.console.write("Can't render, no scene loaded!")

    def resize_image(self, event):
        # Resize the image to fill the container vertically, maintaining aspect ratio
        container_height = event['height'] if isinstance(event, dict) else event.height
        im = Image.open('result.png')
        
        # Calculate the new width based on the aspect ratio
        width, height = im.size
        new_height = container_height
        new_width = int((new_height / height) * width)

        # Resize the image to fit vertically
        im_resized = im.resize((new_width, new_height), Image.Resampling.BICUBIC)

        # Update the Tkinter image reference
        self.rendered_tkimage = ImageTk.PhotoImage(im_resized)

        # Find the label widget and update its image
        image_panel = self.render_result.winfo_children()[0]
        image_panel.config(image=self.rendered_tkimage)

        # Re-center the image by setting the anchor to 'center'
        image_panel.place(relx=0.5, rely=0.5, anchor="center")