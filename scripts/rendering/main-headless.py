import mitsuba as mi
import drjit as dr

import time

mi.set_variant("cuda_ad_rgb")

import numpy as np
import matplotlib.pyplot as plt

import argparse

from scripts.rendering.integrators.path import MISPathIntegrator
from scripts.rendering.integrators.plt import PLTIntegrator
# from scripts.rendering.integrators.plt import PLTIntegrator

def main(args):
    
    # load scene
    print("Loading scene...")
    start = time.perf_counter_ns()
    scene = mi.load_file(args.scene)
    el = time.perf_counter_ns() - start
    print(f"...done. ({el / 1e6} ms)")

    if args.verbose:
        scene_params = mi.traverse(scene)
        print(scene_params)

    # render scene using the desired integrator
    plt_integrator = mi.load_dict({
        "type": args.integrator,
        "max_depth": 12,
        "rr_depth": 50
    })

    print("Rendering...")
    start = time.perf_counter_ns()
    result = plt_integrator.render(scene, scene.sensors()[0])
    bmp = mi.Bitmap(result).convert(srgb_gamma=False)
    el = time.perf_counter_ns() - start
    print(f"...done. ({el / 1e6} ms)")

    mi.util.write_bitmap('result.exr', bmp, write_async=True)
    mi.util.write_bitmap('result.png', bmp, write_async=True)

    if args.plot:
        fig, ax = plt.subplots(3, 1)
        res = mi.TensorXf(bmp)

        for i in range(3):
            p0 = ax[i].imshow(np.array(res[:, :, i]))
            fig.colorbar(p0, ax=ax[i])

        plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Wave-based scripted renderer.")
    parser.add_argument("scene", help="Scene description file")
    parser.add_argument("--spectral", "-s", action="store_true", help="Whether to perform spectral rendering.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Shows additional information during rendering (ONLY USE WHILE DEBUGGING!).")
    parser.add_argument("--plot", "-p", action="store_true", help="Plot result")
    parser.add_argument("--integrator", "-i", type=str, help="Integrator type.", default="mispath")

    args = parser.parse_args()
    main(args)