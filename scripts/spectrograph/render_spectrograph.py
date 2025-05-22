import mitsuba as mi
import drjit as dr

import json
import time
import os

import numpy as np
import matplotlib.pyplot as plt

import argparse

from pprint import pprint

from scripts.utils import *
from plot_spectra import *
from gen_srfs import gen_srfs
from scene import generate_scene_elements, build_scene
# from scripts.rendering.integrators.plt import PLTIntegrator

def read_config(config):

    with open(config) as f:
        cfg = json.load(f)

        min_wl = cfg["wavelengths"]["min"] 
        max_wl = cfg["wavelengths"]["max"] 
        measure_points = cfg["wavelengths"]["measure_points"] 
        domain_points = cfg["wavelengths"]["domain_points"] 

        spectrum = cfg["spectrum"]
        use_srfs = cfg["use_srfs"]

        return min_wl, max_wl, measure_points, domain_points, spectrum, use_srfs

def render_scene(scene, samples):
    
    #render scene using the desired integrator
    integrator = mi.load_dict({
        "type" : "stokes",
        "nested" : {
            "type" : "plt",
            "max_depth": 7,
            "rr_depth": 50,
            'samples_per_pass': 512
        }
    })
    result = integrator.render(scene, spp=samples)
    bmp = mi.Bitmap(result).convert()

    L, sp = stokes_to_bitmaps(bmp)
    return L, sp, sp[0].convert(mi.Bitmap.PixelFormat.Y), result

def save_spectrograph_output(folder_path, L, sp):

    mi.util.write_bitmap(os.path.join(folder_path, f'result.exr'), L, write_async=True)
    mi.util.write_bitmap(os.path.join(folder_path, f'result.png'), L, write_async=True)

    for i, si in enumerate(sp):
        mi.util.write_bitmap(os.path.join(folder_path, f'result_s{i}.exr'), si, write_async=True)
        mi.util.write_bitmap(os.path.join(folder_path, f'result_s{i}.png'), si, write_async=True)

def main(args):
    
    # create folder structure
    sp_sub = os.path.join(args.outdir, "spectra")
    try:
        os.makedirs(args.outdir)
        print(f"Creating folder at '{args.outdir}'")
    except:
        pass
    finally:
        try:
            os.makedirs(sp_sub)
            print(f"Creating spectra folder at '{sp_sub}'")
        except:
            pass

    min_wl, max_wl, measure_points, domain_points, spectrum, use_srfs = read_config(args.sp_config)
    
    print("Creating scene... ", end="")
    start = time.perf_counter_ns()
    domain_wls, measured_wls, srfs = gen_srfs(measure_points, domain_points, min_wl, max_wl)
    light_dir, sensors, grating_patch = generate_scene_elements(args.outdir, domain_wls, measured_wls, srfs, use_srfs)
    scene = build_scene(light_dir, sensors, grating_patch, spectrum)
    scene_build_time = time.perf_counter_ns() - start
    mi.xml.dict_to_xml(scene, os.path.join(args.outdir, "scene.xml"))
    print(f"done. ({scene_build_time / 1e6} ms)")

    print("Simulating spectrograph capture... ", end="")
    start = time.perf_counter_ns()

    pprint(scene)
    L, sp, intensity, raw = render_scene(mi.load_dict(scene), args.spp)
    render_time = time.perf_counter_ns() - start
    print(f"done. ({render_time / 1e6} ms)")

    plot_spectra(np.ravel(measured_wls), np.ravel(intensity))

    save_spectrograph_output(args.outdir, L, sp)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Wave-based scripted renderer.")
    parser.add_argument("sp_config", help="Spectrograph configuration file")
    parser.add_argument("outdir", help="Where to store the scene data")
    parser.add_argument("--spectral", "-s", action="store_true", help="Whether to perform spectral rendering.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Shows additional information during rendering (ONLY USE WHILE DEBUGGING!).")
    parser.add_argument("--spp", type=int, help="Samples per pixel", default=64)

    args = parser.parse_args()

    # setup mode here
    if args.spectral:
        print("Loading spectral variant...")
        mi.set_variant("cuda_ad_spectral_polarized")
    else:
        print("Loading RGB variant...")
        mi.set_variant("cuda_ad_rgb_polarized")

    # load integrators
    from scripts.rendering.integrators.plt import PLTIntegrator

    main(args)