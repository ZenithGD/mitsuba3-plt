import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tksheet import Sheet

class SceneView(ttk.Frame):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.parent = parent
        self.current_scene = None

        # Initialize style for gridlines
        style = ttk.Style()
        style.configure("Treeview", rowheight=25)
        style.configure("Treeview", highlightthickness=0, bd=0, font=('Helvetica', 10))
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])
        style.map("Treeview", background=[('selected', '#a1a1a1')])
        style.configure("Treeview.Heading", font=('Helvetica', 11, 'bold'))
        
        # Setting the gridlines by enabling border
        style.configure("Treeview", bordercolor="white")
        style.configure("Treeview.Heading", bordercolor="white")

        self.scene_view = ttk.Label(self.parent, text="No scene loaded")
        self.scene_view.pack(side=tk.TOP)

    def update_scene(self, scene_name, scene):
        if self.scene_view:
            self.scene_view.destroy()

        self.scene_view = ttk.Frame(self.parent)
        self.scene_view.pack(fill="both", expand=True)

        label = ttk.Label(self.scene_view, text=scene_name).pack(side="top")
        # Create the Treeview with two columns: "name" and "value"
        tree_view = ttk.Treeview(self.scene_view, columns=("value"))
        tree_view.pack(side="top", fill="both", expand=True)

        # Set up the column headers
        tree_view.heading("#0", text="Property")  # Heading for the tree column
        tree_view.heading("value", text="Value")

        # Set up column widths and alignments if needed
        tree_view.column("#0", width=150, anchor="w")  # The first tree column
        tree_view.column("value", width=100, anchor="center")

        self._insert_tree_node(tree_view, "", scene)

    def _insert_tree_node(self, tree_view, tree_node, obj):

        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, dict):
                    item = tree_view.insert(tree_node, tk.END, text=k)
                else:
                    item = tree_view.insert(tree_node, tk.END, text=k, values=(repr(v)))

                self._insert_tree_node(tree_view, item, obj[k])

    def clear_scene(self):
        self.scene_view.destroy()
        self.scene_view = ttk.Label(self.parent, "No scene loaded").pack(side=tk.TOP)
