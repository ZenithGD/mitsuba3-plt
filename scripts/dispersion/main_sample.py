import argparse

import mitsuba as mi
import drjit as dr

mi.set_variant("cuda_ad_rgb_polarized")

import numpy as np
import matplotlib.pyplot as plt

from sample import *

def main(args):
    nsamples = args.samples

    bsdf = mi.load_dict({
        'type': 'roughgrating',
        'distribution': 'ggx',
        'alpha' : 0.0005,

        'lobe_type' : 'sinusoidal',
        'height' : 0.05,
        'inv_period_x' : 0.4,
        'inv_period_y' : 0.4,
        'radial' : False,
        'lobes' : 5,
        'grating_angle' : 45,
    })

    # bsdf = mi.load_dict({
    #     'type': 'roughconductor',
    #     'distribution': 'ggx',
    #     'alpha' : 0.01
    # })

    sample_context = {
        "nsamples" : nsamples,
        "wi" : sph_to_dir(dr.deg2rad(30), 0.0)
    }

    samples, weights = sample_wbsdf(bsdf, sample_context)

    plot_samples(samples, weights, sample_context)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Sample wBSDF and plot the dispersion of the samples in 3D")
    parser.add_argument("--samples", "-s", type=int, help="Number of samples", default=1000)

    args = parser.parse_args() 
    main(args)