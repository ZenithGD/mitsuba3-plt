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

import flip_evaluator as flip

def compare_bitmap(b1, b2):
    b1_np = np.array(mi.Bitmap(b1))
    b2_np = np.array(mi.Bitmap(b2))

    # FLIP
    FLIP_err_map, mean_FLIP_error, parameters = flip.evaluate(b1, b2, "LDR")
    
    # RMSE
    rmse = np.sqrt(np.mean(np.square(b1_np - b2_np)))

    return FLIP_err_map, mean_FLIP_error, rmse

def perform_experiment(args, scene, integrator):

    # folder to store data
    folder_path = ""
    if args.outdir:
        folder_path = os.path.join(args.outdir, integrator)
        try:
            os.makedirs(folder_path)
            print(f"Creating folder at '{folder_path}'")
        except FileExistsError:
            pass

    rmses = []
    flips = []
    render_times = []

    #render scene using the desired integrator for each sample count
    for spp in args.spp:
        print(f"Rendering image with {spp} spp...")
        start = time.perf_counter_ns()
        L, sp, result = render_scene(scene, spp, integrator, args.denoise)
        el = time.perf_counter_ns() - start
        print(f"...done. ({format_time(el)})")

        hdr_path = os.path.join(folder_path, f'result_{spp}.exr')
        ldr_path = os.path.join(folder_path, f'result_{spp}.png')
        mi.util.write_bitmap(hdr_path, sp[0], write_async=False)
        mi.util.write_bitmap(ldr_path, sp[0], write_async=False)

        FLIP_err_map, mean_FLIP_err, rmse = compare_bitmap(hdr_path, args.reference) 

        err_map_path = os.path.join(folder_path, f'error_map_{spp}.exr')
        mi.util.write_bitmap(err_map_path, mi.Bitmap(FLIP_err_map), write_async=True)

        # write data about the render
        print("Mean FLIP =", mean_FLIP_err)
        print("Mean RMSE =", rmse)

        render_data = {
            "bitmap_size" : {
                "width" : L.size().x,
                "height" : L.size().y
            },
            "samples" : spp,
            "time": format_time(el),
            "time_per_sample": format_time(el / spp),
            "FLIP_error" : float(mean_FLIP_err),
            "RMSE_error" : float(rmse)
        }

        with open(os.path.join(folder_path, f"params_{spp}.json"), "w") as f:
            json.dump(render_data, f, indent=2)

        rmses.append(rmse)
        flips.append(mean_FLIP_err)
        render_times.append(el / 1e9)

    return rmses, flips, render_times

def main(args):
   
    # load scene
    print("Loading scene...")
    start = time.perf_counter_ns()
    scene = mi.load_file(args.scene)
    el = time.perf_counter_ns() - start
    print(f"...done. ({format_time(el)})")

    if args.verbose:
        scene_params = mi.traverse(scene)
        print(scene_params)
    if args.path_comp:
        path_flips, path_rmses, path_render_times = perform_experiment(args, scene, "path")
    
    plt_flips, plt_rmses, plt_render_times = perform_experiment(args, scene, "plt")

    # now plot both errors
    fig, axs = plt.subplots(1, 3)
    (ax_flip, ax_rmse, ax_time) = axs
    # plt.tight_layout()
    fig.subplots_adjust(wspace=0.4, hspace=0.5)

    if args.path_comp:
        ax_flip.plot(args.spp, path_flips, label="Path traced")
        ax_rmse.plot(args.spp, path_rmses, label="Path traced")
        ax_time.plot(args.spp, path_render_times, label="Path traced")

    ax_flip.plot(args.spp, plt_flips, label="PLT")
    ax_rmse.plot(args.spp, plt_rmses, label="PLT")
    ax_time.plot(args.spp, plt_render_times, label="PLT")

    ax_flip.set_title("FLIP error")
    ax_flip.set_ylabel("Mean FLIP")
    ax_rmse.set_title("RMSE error")
    ax_rmse.set_ylabel("RMSE")
    ax_time.set_title("Render time")
    ax_time.set_ylabel("Render time (s)")

    for ax in axs:
        ax.set_xscale('log', base=10)
        ax.set_yscale('log', base=2)
        ax.set_xlabel("Samples per pixel")
        ax.set_xticks(args.spp)
        ax.get_xaxis().set_major_formatter(plt.ScalarFormatter())
        ax.get_yaxis().set_major_formatter(plt.ScalarFormatter())
        ax.ticklabel_format(style='plain', axis='x')
        ax.ticklabel_format(style='plain', axis='y')
        ax.minorticks_off()
        ax.legend()
        
    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Wave-based scripted renderer.")
    parser.add_argument("scene", help="Scene description file")
    parser.add_argument("--spectral", "-s", action="store_true", help="Whether to perform spectral rendering.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Shows additional information during rendering (ONLY USE WHILE DEBUGGING!).")
    parser.add_argument("--plot", "-p", action="store_true", help="Plot result")
    parser.add_argument("--spp", type=int, nargs="+", help="List of samples per pixel values to try", default=[ 2**i for i in range(4, 10, 1)])
    parser.add_argument("--outdir", "-o", type=str, help="The folder in which to store the results")
    parser.add_argument("--denoise", "-d", action="store_true", help="Whether to denoise the final result.")
    parser.add_argument("--reference", "-r", type=str, help="The reference image")
    parser.add_argument("--path_comp", "-c", action="store_true", help="Whether to compare against path traced solution")
    
    
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