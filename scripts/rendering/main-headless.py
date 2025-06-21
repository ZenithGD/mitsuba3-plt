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
# from scripts.rendering.integrators.plt import PLTIntegrator

def process_override_value(st : str):

    # for now only floats
    return float(st)

def main(args):

    # process overrides in dict
    overrides = {}
    print(args.override)
    for ov in args.override:
        ov_split = ov.split("=")
        name, value = ov_split[0], process_override_value(ov_split[1])
        overrides[name] = value
    
    # load scene
    print("Loading scene...")
    start = time.perf_counter_ns()
    scene = mi.load_file(args.scene)
    el = time.perf_counter_ns() - start
    print(f"...done. ({format_time(el)})")
    
    scene_params = mi.traverse(scene)
    
    if args.verbose:
        print(scene_params)

    # apply each override
    for name, value in overrides.items():
        print("overriding", name, "=", value)
        scene_params[name] = value

    scene_params.update()

    #render scene using the desired integrator    
    print("Rendering...")
    L, sp, result = render_scene(scene, args.spp, args.integrator, args.denoise)
    el = time.perf_counter_ns() - start
    print(f"...done. ({format_time(el)})")

    # folder to store data
    folder_path = ""
    if args.outdir:
        folder_path = args.outdir
        try:
            os.makedirs(folder_path)
            print(f"Creating folder at '{folder_path}'")
        except FileExistsError:
            pass
    
    mi.util.write_bitmap(os.path.join(folder_path, f'result.exr'), L, write_async=True)
    mi.util.write_bitmap(os.path.join(folder_path, f'result.png'), L, write_async=True)

    for i, si in enumerate(sp):
        mi.util.write_bitmap(os.path.join(folder_path, f'result_s{i}.exr'), si, write_async=True)
        mi.util.write_bitmap(os.path.join(folder_path, f'result_s{i}.png'), si, write_async=True)

    # write data about the render
    render_data = {
        "bitmap_size" : {
            "width" : L.size().x,
            "height" : L.size().y
        },
        "samples" : args.spp,
        "time": format_time(el),
        "time_per_sample": format_time(el / args.spp)
    }

    with open(os.path.join(folder_path, "params.json"), "w") as f:
        json.dump(render_data, f, indent=2)

    if args.plot:
        # plot intensity (s0)
        plt.figure(figsize=(5, 5))
        plt.imshow(sp[0].convert(srgb_gamma=True), cmap='gray')
        plt.colorbar()
        plt.xticks([]); plt.yticks([])
        plt.xlabel("S0: Intensity", size=14, weight='bold')
        plt.show()

        # plot linear, diagonal and circular polarization
        fig, ax = plt.subplots(ncols=3, figsize=(18, 5))
        img = plot_stokes_component(ax[0], sp[1])
        plt.colorbar(img, ax=ax[0])
        img = plot_stokes_component(ax[1], sp[2])
        plt.colorbar(img, ax=ax[1])
        img = plot_stokes_component(ax[2], sp[3])
        plt.colorbar(img, ax=ax[2])

        ax[0].set_xlabel("S1: Horizontal vs. vertical", size=14, weight='bold')
        ax[1].set_xlabel("S2: Diagonal", size=14, weight='bold')
        ax[2].set_xlabel("S3: Circular", size=14, weight='bold')

        plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Wave-based scripted renderer.")
    parser.add_argument("scene", help="Scene description file")
    parser.add_argument("--spectral", "-s", action="store_true", help="Whether to perform spectral rendering.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Shows additional information during rendering (ONLY USE WHILE DEBUGGING!).")
    parser.add_argument("--plot", "-p", action="store_true", help="Plot result")
    parser.add_argument("--integrator", "-i", type=str, help="Integratsor type.", default="mispath")
    parser.add_argument("--spp", type=int, help="Samples per pixel", default=64)
    parser.add_argument("--outdir", "-o", type=str, help="The folder in which to store the results")
    parser.add_argument("--denoise", "-d", action="store_true", help="Whether to denoise the final result.")
    parser.add_argument("--override", "-r", type=str, nargs="*", help="Set of overrides to apply to the scene.", default=[])
    
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