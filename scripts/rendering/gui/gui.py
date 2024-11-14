import ttkbootstrap as ttkb

from .controller import *
from .layout import *

class MitsubaViewer(ttkb.Frame):

    def __init__(self, parent = None):

        self.app = parent

        # create the controllers
        self.scene_ctrl = SceneController()
        self.renderer_ctrl = RendererController()

        # create the views and attach controllers
        self.home_view = Home(self.scene_ctrl, self.renderer_ctrl, parent)

    def display(self):

        self.home_view.display()