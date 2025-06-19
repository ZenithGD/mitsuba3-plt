import mitsuba as mi
import drjit as dr

import json
import time
import os

from utils import *

import numpy as np
import matplotlib.pyplot as plt

import argparse

from scripts.utils import *

def main(args):

    # folder to store data
    folder_path = ""
    if args.outdir:
        folder_path = args.outdir
        try:
            os.makedirs(folder_path)
            print(f"Creating folder at '{folder_path}'")
        except FileExistsError:
            pass
   
    # load scene
    print("Loading scene...")
    start = time.perf_counter_ns()
    scene = mi.load_file(args.scene)
    el = time.perf_counter_ns() - start
    print(f"...done. ({format_time(el)})")

    if args.verbose:
        scene_params = mi.traverse(scene)
        print(scene_params)

    print(args.spp)
    #render scene using the desired integrator for each sample count
    for spp in args.spp:
        print(f"Rendering image with {spp} spp...")
        L, sp, result = render_scene(scene, spp, args.integrator, args.denoise)
        el = time.perf_counter_ns() - start
        print(f"...done. ({format_time(el)})")

        mi.util.write_bitmap(os.path.join(folder_path, f'result_{spp}.exr'), sp[0], write_async=True)
        mi.util.write_bitmap(os.path.join(folder_path, f'result_{spp}.png'), sp[0], write_async=True)

        # write data about the render
        render_data = {
            "bitmap_size" : {
                "width" : L.size().x,
                "height" : L.size().y
            },
            "samples" : spp,
            "time": format_time(el),
            "time_per_sample": format_time(el / spp)
        }

        with open(os.path.join(folder_path, f"params_{spp}.json"), "w") as f:
            json.dump(render_data, f, indent=2)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Wave-based scripted renderer.")
    parser.add_argument("scene", help="Scene description file")
    parser.add_argument("--spectral", "-s", action="store_true", help="Whether to perform spectral rendering.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Shows additional information during rendering (ONLY USE WHILE DEBUGGING!).")
    parser.add_argument("--plot", "-p", action="store_true", help="Plot result")
    parser.add_argument("--integrator", "-i", type=str, help="Integrator type.", default="mispath")
    parser.add_argument("--spp", type=int, nargs="+", help="List of samples per pixel values to try", default=[ 2**i for i in range(4, 10, 1)])
    parser.add_argument("--outdir", "-o", type=str, help="The folder in which to store the results")
    parser.add_argument("--denoise", "-d", action="store_true", help="Whether to denoise the final result.")
    
    args = parser.parse_args()

    # setup mode here
    if args.spectral:
        print("Loading spectral variant...")
        mi.set_variant("cuda_ad_spectral_polarized")
    else:
        print("Loading RGB variant...")
        mi.set_variant("cuda_ad_rgb_polarized")

    # load integrators
    from scripts.rendering.integrators.path import MISPathIntegrator
    from scripts.rendering.integrators.plt import PLTIntegrator

    main(args)