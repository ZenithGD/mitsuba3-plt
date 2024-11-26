import mitsuba as mi
import drjit as dr

from integrators import *

from concurrent.futures import ThreadPoolExecutor

import time

class RendererController:

    def __init__(self):
        # Thread pool executor for background tasks
        self.executor = ThreadPoolExecutor(max_workers=1)

    def render_scene(self, scene, params, on_finish):
        """Render scene asynchronously

        Args:
            scene (_type_): _description_
            on_finish (_type_): _description_
        """
        future = self.executor.submit(lambda : self.__do_render(scene, params))
        future.add_done_callback(lambda future: on_finish(future.result()))

    def __do_render(self, scene, params):
        
        # render scene using the desired integrator
        plt_integrator = mi.load_dict({
            "type": params["integrator"],
            "max_depth": 12,
            "rr_depth": 50
        })

        result = plt_integrator.render(scene, scene.sensors()[0])
        bmp = mi.Bitmap(result).convert(srgb_gamma=False)

        return bmp