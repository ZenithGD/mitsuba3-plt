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

def render_scene(scene, samples, integrator="path", denoise=False):
    """Render scene with any given number of samples and integrator type.
    Optionally denoise the image.

    Args:
        scene (mi.Scene): The scene loaded from a dict/xml file
        samples (int): The number of samples for the image
        integrator (str, optional): The integrator to use. Defaults to "path".
        denoise (bool, optional): Optionally denoise the image if True. Defaults to False.

    Returns:
        L, sp, result: The captured image, 4 stokes parameters and raw tensor data respectively.
    """
    
    #render scene using the desired integrator
    integrator = mi.load_dict({
        "type" : "stokes",
        "nested" : {
            "type" : integrator,
            "max_depth": 7,
            "rr_depth": 50,
            'samples_per_pass': 512
        }
    })
    result = integrator.render(scene, spp=samples)
    bmp = mi.Bitmap(result).convert()

    L, sp = stokes_to_bitmaps(bmp)
    
    if denoise:
        print("Denoising...")
        print(L.size())
        # Denoise the rendered image
        denoiser = mi.OptixDenoiser(input_size=L.size(), albedo=False, normals=False, temporal=False)
        L = denoiser(L)

        for i, s in enumerate(sp):
            sp[i] = denoiser(s)

    return L, sp, result

def write_data(folder_path, L, sp, el):
    
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
        "time": el / 1e9
    }

    with open(os.path.join(folder_path, "params.json"), "w") as f:
        json.dump(render_data, f)

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

    #render scene using the desired integrator
    
    print("Rendering...")
    L, sp, result = render_scene(scene, args.spp, args.integrator, args.denoise)
    el = time.perf_counter_ns() - start
    print(f"...done. ({el / 1e6} ms)")

    # folder to store data
    folder_path = ""
    if args.outdir:
        folder_path = args.outdir
        try:
            os.makedirs(folder_path)
            print(f"Creating folder at '{folder_path}'")
        except FileExistsError:
            pass
            
    write_data(args.outdir, L, sp, el / 1e9)

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
    parser.add_argument("--integrator", "-i", type=str, help="Integrator type.", default="mispath")
    parser.add_argument("--spp", type=int, help="Samples per pixel", default=64)
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