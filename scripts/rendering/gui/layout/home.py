import importlib.resources as resources
import mitsuba as mi
import json
import pprint 

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

        ttk.Frame.__init__(self, parent)

        self.parent = parent

        self.current_scene = None
        self.scene_ctrl : SceneController = scene_ctrl
        self.renderer_ctrl : RendererController = renderer_ctrl

    def display(self):

        # create menu
        menu = self.__create_menu()
        menu.pack(side=tk.TOP, anchor=tk.NW, fill='x')

        # Separate console and tooling
        console_paned_window = ttk.PanedWindow(self.parent, orient=VERTICAL)
        console_paned_window.pack(fill=BOTH, expand=True)

        self.tool_frame = ttk.Frame(self.parent)
        self.tool_frame.pack(fill="both", expand=True)
        tool_paned_window = self.__create_tool_views(self.tool_frame)

        # add console at the bottom
        self.console = PrintLogger(self.parent)
        self.console.pack(fill="x")

        # Add frames to the PanedWindow with resizable option
        console_paned_window.add(self.tool_frame, weight=1)  # left frame can resize
        console_paned_window.add(self.console, weight=1)  # right frame can resize

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

        assets_path = os.path.join(resources.files(__package__), "..", "assets")
        
        # frame on top
        menu_frame = ttk.Frame()

        # Load scene button
        load_cmd = lambda : self.__load_scene()
        load_btn = ImageButton(
            os.path.join(assets_path, "load.png"), "Load scene", menu_frame,
            bootstyle="dark",
            command=load_cmd)
        
        load_btn.pack(side=tk.LEFT)
        
        # Save scene button
        save_btn = ImageButton(
            os.path.join(assets_path, "save.png"), "Save scene", menu_frame,
            bootstyle="dark")
        
        save_btn.pack(side=tk.LEFT)
        save_cmd = lambda : self.__save_scene()

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

        return render_view, lf
    
    def __save_scene(self):
        pass

    def __load_scene(self):
        scene_path = fd.askopenfilename()
        self.console.write(f"Loading scene...")
        scene = self.scene_ctrl.load_scene(scene_path)
        self.current_scene = props_to_dict(scene)

        self.scene_view.update_scene(scene_path, self.current_scene)
        self.console.write(f"done...")


