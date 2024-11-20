import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tksheet import Sheet

import mitsuba as mi

class SceneView(ttk.Frame):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.parent = parent
        self.current_scene = None

        self.scene_view = ttk.Label(self.parent, text="No scene loaded")
        self.scene_view.pack(side=tk.TOP)
        self.treeview = None

    def update_scene(self, scene_name, scene_dict, scene_obj):
        if self.scene_view:
            self.scene_view.destroy()

        self.current_scene = scene_obj
        self.current_scene_dict = scene_dict

        self.scene_view = ttk.Frame(self.parent)
        self.scene_view.pack(fill="both", expand=True)

        label = ttk.Label(self.scene_view, text=scene_name).pack(side="top")
        # Create the Treeview with two columns: "name" and "value"
        self.tree_view = Sheet(self.scene_view, treeview=True)
        self.tree_view.pack(fill=BOTH, expand=True)
        self.tree_view.change_theme("dark")

        # enable various bindings
        self.tree_view.enable_bindings("all", "edit_index", "edit_header")

        # self.sheet_was_modified is your function
        self.tree_view.bind("<<SheetModified>>", self.__on_modify)

        self._insert_tree_node(self.tree_view, "", scene_dict)

    def _insert_tree_node(self, tree_view, tree_node, obj, prefix = ""):

        if isinstance(obj, dict):
            for k, v in obj.items():
                compound_key = f"{prefix}.{k}"
                if isinstance(v, dict):
                    node_iid = tree_view.insert(
                        iid=compound_key,
                        parent=tree_node,
                        text=k)
                    
                else:
                    node_iid = tree_view.insert(
                        iid=compound_key,
                        parent=tree_node,
                        text=k, 
                        values=[repr(v)]
                    )

                self._insert_tree_node(tree_view, node_iid, obj[k], compound_key)

    def clear_scene(self):
        self.scene_view.destroy()
        self.scene_view = ttk.Label(self.parent, "No scene loaded").pack(side=tk.TOP)
        self.tree_view.unbind("<<SheetModified>>")
        self.tree_view.destroy()

    def __on_modify(self, event):

        params = mi.traverse(self.current_scene)

        for (row, column), old_value in event.cells.table.items():
            val_key = self.tree_view.rowitem(row)
            curr_values = self.tree_view.item(val_key)["values"]

            print(curr_values)

            # modify scene params
            params[val_key] = curr_values[0]

        params.update()