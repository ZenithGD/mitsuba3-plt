from dataclasses import dataclass
import mitsuba as mi
import drjit as dr

import os
from pathlib import Path

@dataclass
class SceneParameter:

    def __init__(self, name, diff, disc, ptype):

        self.name = name
        self.diff = diff
        self.disc = disc
        self.type = ptype

def _deep_store(dc, key, value):
    """Store the value according to the depth of the compound key.
    A compound key is formed by a sequence of keys and dots that
    represent the location of the value within the dictionary.

    Args:
        dc (dict): The dictionary
        key (str): A compound key in string form
        value (any): The value to store
    """
    subkeys = key.split(".")
    subdict = dc
    for sk in subkeys[:-1]:
        if sk not in subdict:
            subdict[sk] = {}
        subdict = subdict[sk]

    # store final value
    subdict[subkeys[-1]] = value
    return dc

def _deep_elm_insert(dc, key, value) -> bool:
    """Insert the value in the location represented by the compound key.
    If the location cannot be reached from the top level, the function will return False.
    Otherwise, it will return True

    Args:
        dc (dict): The dictionary
        key (str): The compound key
        value (any): The value to insert

    Returns:
        (bool): False if the value couldn't be inserted, True otherwise.
    """
    subkeys = key.split(".")
    if subkeys[0] not in dc:
        return False
    
    _deep_store(dc, key, value)
    return True

def props_to_dict(scene: mi.Scene):
    """Return a traversable dictionary that contains the different parameters
    that can be modified in a scene.

    Note: This function is a bit dirty and tries to overcome some of the restrictions
    of Mitsuba's object hierarchy. It only serves as a way to organize
    the parameters of the scene in a tree-like structure.

    Args:
        scene (mi.Scene): The scene to convert into a dictionary of values

    Returns:
        dict: The dictionary that contains the values
    """
    assert isinstance(scene, mi.Scene)

    integrator = scene.integrator()
    shapes = scene.shapes()
    emitters = scene.emitters()
    sensors = scene.sensors()

    dict_rep = {
        "integrator": {
            "type" : "path",
            "max_depth" : 12,
        },
        "shapes" : {},
        "emitters" : {},
        "sensors" : {},
        "films" : {}
    }

    scene_params = mi.traverse(scene)
    scene_props = list(scene_params.properties.items())

    # sort parameters by the depth in the hierarchy
    # to ensure that the correct high-level plugin type is inferred
    # dirtiest trick on the book :/
    sorted_properties = sorted(scene_props, key=lambda t: len(t[0].split(".")))

    # loop through all parameters and determine where it is stored
    for key, value in sorted_properties:
        value, value_type, node, flags = value

        if value_type is not None:
            value = scene_params.get_property(value, value_type, node)

        # determine where will the property be stored based on its type and depth
        if isinstance(node, mi.Shape):
            _deep_store(dict_rep["shapes"], key, scene_params[key])
        elif isinstance(node, mi.Emitter):
            _deep_store(dict_rep["emitters"], key, scene_params[key])
        elif isinstance(node, mi.Sensor):
            _deep_store(dict_rep["sensors"], key, scene_params[key])
        elif isinstance(node, mi.Film):
            _deep_store(dict_rep["films"], key, scene_params[key])
        else:
            # Find and insert, continue if the insertion point is found
            if _deep_elm_insert(dict_rep["shapes"], key, scene_params[key]):
                continue
            elif _deep_elm_insert(dict_rep["emitters"], key, scene_params[key]):
                continue
            elif _deep_elm_insert(dict_rep["sensors"], key, scene_params[key]):
                continue
            elif _deep_elm_insert(dict_rep["films"], key, scene_params[key]):
                continue
        

    return dict_rep

class SceneController:

    def __init__(self):
        
        # scene dict containing the name of the scene folder and the scene 
        # object and its path
        self.scenes = {}

    def load_scene(self, path, name = None):
        """Load a scene with some name. If not specified, 
        the name will be the same as the description file's name

        Args:
            path (str): The path of the scene description
            name (str): The name that uniquely identifies the scene.
        """
        if name is None:
            name = Path(path).stem

        if name not in self.scenes:
            self.scenes[name] = mi.load_file(path)

        return self.scenes[name]

    def remove_scene(self, name):
        if name in self.scenes:
            del self.scenes[name]


    