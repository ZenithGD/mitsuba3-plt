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
        use_prior = cfg["use_prior"]

        return min_wl, max_wl, measure_points, domain_points, spectrum, use_srfs, use_prior

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
    return L, sp, result

def save_spectrograph_output(folder_path, L, sp):

    mi.util.write_bitmap(os.path.join(folder_path, f'result.exr'), L, write_async=True)
    mi.util.write_bitmap(os.path.join(folder_path, f'result.png'), L, write_async=True)

    for i, si in enumerate(sp):
        mi.util.write_bitmap(os.path.join(folder_path, f'result_s{i}.exr'), si, write_async=True)
        mi.util.write_bitmap(os.path.join(folder_path, f'result_s{i}.png'), si, write_async=True)

def eval_spectrum(wavelengths, spectrum):
    sp = mi.load_dict(spectrum)

    si = mi.SurfaceInteraction3f()
    si.wavelengths = mi.Float(wavelengths)

    ev = np.array(sp.eval(si))[0]
    print(ev.shape)
    if ev.shape[0] == 1:
        ev = np.repeat(ev, len(wavelengths))
        return ev

    return ev

def plot_spectra_comparison(wavelengths, recovered, original):
    fig, axes = plt.subplots(2, 2)
    ((ax11, ax12), (ax21, ax22)) = axes

    plot_spectra(ax11, wavelengths, original, label="Original", color="blue")
    plot_spectra(ax12, wavelengths, recovered, label="Recovered", color="red")

    plot_spectra(ax21, wavelengths, original, label="Original", color="blue")
    plot_spectra(ax21, wavelengths, recovered, label="Recovered", color="red")

    plot_spectra(ax22, wavelengths, original - recovered, label="Difference", color="green")
    
    for ax in [ax11, ax12, ax21]:
        ax.set_xlabel("wavelengths")
        ax.set_ylabel("intensity")
        ax.set_ylim(0, np.maximum(np.max(original), np.max(recovered)) * 1.1)
    
    for ax in [ax11, ax12, ax21, ax22]:
        ax.legend()

    ax.set_xlabel("wavelengths")
    ax.set_ylabel("error")
    max_diff = np.max(np.abs(original-recovered))
    ax.set_ylim(-max_diff * 1.1, max_diff * 1.1)
    
    ax11.set_title("Original spectrum")
    ax12.set_title("Recovered spectrum")
    ax21.set_title("Spectra comparison")
    ax22.set_title("Difference")
    fig.tight_layout()
    fig.suptitle("Spectrograph")

    plt.show()

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

    min_wl, max_wl, measure_points, domain_points, spectrum, use_srfs, use_prior = read_config(args.sp_config)
    
    print("Creating scene... ", end="")
    start = time.perf_counter_ns()
    
    domain_wls, measured_wls, srfs = gen_srfs(measure_points, domain_points, min_wl, max_wl)
    light_dir, sensors, grating_patch = generate_scene_elements(args.outdir, domain_wls, measured_wls, srfs, use_srfs)
    
    # scene and prior scene
    prior_spectrum = {
        "type": "uniform",
        "value" : 1.0
    } if use_prior else 1.0
    prior_scene = build_scene(light_dir, sensors, grating_patch, prior_spectrum)
    scene = build_scene(light_dir, sensors, grating_patch, spectrum)
    scene_build_time = time.perf_counter_ns() - start
    mi.xml.dict_to_xml(scene, os.path.join(args.outdir, "scene.xml"))
    print(f"done. ({scene_build_time / 1e6} ms)")

    print("Simulating spectrograph capture... ", end="")
    start = time.perf_counter_ns()

    
    L_prior, sp_prior, raw_prior = render_scene(mi.load_dict(prior_scene), args.spp)
    L, sp, raw = render_scene(mi.load_dict(scene), args.spp)
    render_time = time.perf_counter_ns() - start
    print(f"done. ({render_time / 1e6} ms)")

    prior_intensity = np.ravel(np.mean(np.array(sp_prior[0]), axis=-1))
    intensity = np.ravel(np.mean(np.array(sp[0]), axis=-1))

    plot_spectra_comparison(np.ravel(measured_wls), intensity / prior_intensity, eval_spectrum(measured_wls, spectrum))

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