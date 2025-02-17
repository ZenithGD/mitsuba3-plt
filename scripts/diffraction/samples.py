import mitsuba as mi
import drjit as dr
import time
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # Import required for 3D plotting

import argparse

from matplotlib.widgets import Slider

from utils import *

def compute_samples(grating, wi, wl, samples, lobes) -> tuple:

    freqs = np.zeros((lobes, lobes))
    ls = []

    for i in range(samples):
        sample = np.random.rand(2)
        r = grating.sample_lobe(mi.Vector2f(sample[0], sample[1]), wi, wl)
        
        print(r)
        ls.append(r[0])

    return freqs, ls

def main(args):

    # initialize variant
    mi.set_variant("cuda_ad_spectral")
    #np.random.seed(None)

    grating = mi.DiffractionGrating3f(
        45, 
        mi.Vector2f(0.5, 0.5), 
        0.02, 
        args.lobes, 
        mi.DiffractionGratingType.Sinusoidal,
        1, mi.Vector2f(0.0)
    )
    wi = sph_to_dir(dr.deg2rad(45), 0.0)
    wl = 0.46

    samples, freq = compute_samples(grating, wi, wl, args.samples, args.lobes)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Sample diffraction grating")
    parser.add_argument("--samples", type=int, default=10, help="Number of samples")
    parser.add_argument("--lobes", type=int, default=5, help="Number of lobes of the diffraction grating")

    args = parser.parse_args()

    main(args)