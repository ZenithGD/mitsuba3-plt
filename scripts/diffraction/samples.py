import mitsuba as mi
import drjit as dr
import time
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # Import required for 3D plotting

import argparse

from utils import *

# initialize variant
mi.set_variant("cuda_ad_rgb_polarized")

def compute_intensity_grid(grating, wi, wl, lobes):

    nlobesx = lobes
    nlobesy = lobes
    
    lobes_x = np.arange(nlobesx) - nlobesx // 2
    lobes_y = np.arange(nlobesy) - nlobesy // 2
    lobes_xv, lobes_yv = np.meshgrid(lobes_x, lobes_y)
    lobes_xv = lobes_xv.ravel()
    lobes_yv = lobes_yv.ravel()
    
    lobevec = mi.Vector2i(dr.cuda.Int(lobes_xv), dr.cuda.Int(lobes_yv))

    it = grating.lobe_intensity(lobevec, wi, wl)

    return np.array(it).reshape(nlobesx, nlobesy)


def compute_samples(grating, wi, wl, samples, lobes) -> tuple:

    freqs = np.zeros((lobes, lobes))
    avg_pdf = np.zeros((lobes, lobes))

    sample = np.random.rand(2, samples)
    r, p = grating.sample_lobe(mi.Vector2f(sample[0,:], sample[1,:]), wi, wl)

    r = np.array(r).T
    p = np.array(p).T
    np.add.at(freqs, (r[:, 0] - lobes//2 - 1, r[:, 1] - lobes//2 - 1), 1)

    for i in range(r.shape[0]):
        avg_pdf[r[i, 0] - lobes//2 - 1, r[i, 1] - lobes//2 - 1] += p[i, 0] * p[i, 1]

    avg_pdf = np.where(freqs != 0, avg_pdf / freqs, 0)
    
    return avg_pdf, freqs

def compare_samples(grating, wi, wl, samples, lobes):
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3)

    pdf_grid, sample_grid = compute_samples(grating, wi, wl, samples, lobes)
    gt_grid = compute_intensity_grid(grating, wi, wl, lobes)

    # visualize samples and true intensity lobes (normalized for comparison)
    visualize_lobe_intensity(sample_grid, ax1, normalize=True)
    visualize_lobe_intensity(gt_grid, ax2, normalize=True)
    visualize_lobe_intensity(pdf_grid, ax3, normalize=False)

    rmse = np.sqrt(np.mean((sample_grid / np.sum(sample_grid) - gt_grid / np.sum(gt_grid))**2))

    fig.suptitle(f"RMSE = {rmse:.4f}")
    ax1.set_title("Sample grid")
    ax2.set_title("True intensities")
    ax3.set_title("Averaged pdf")

    plt.show()

def show_sampling_error(grating, wi, wl, min_samples, max_samples, lobes, steps=150):
    step_array = np.geomspace(min_samples, max_samples, steps).astype(np.int32)
    rmse_list = []

    gt_grid = compute_intensity_grid(grating, wi, wl, lobes)
    gt_grid /= np.sum(gt_grid)

    for samples in step_array:
        pdf_grid, sample_grid = compute_samples(grating, wi, wl, samples, lobes)

        # normalize both grids
        sample_grid /= np.sum(sample_grid)

        rmse = np.sqrt(np.mean((sample_grid-gt_grid)**2))
        rmse_list.append(rmse)

    fig, ax = plt.subplots()

    ax.plot(step_array, rmse_list, ".-g")
    ax.set_xscale('log')
    ax.set_title("RMSE between distributions")
    plt.show()

def main(args):

    np.random.seed(35122)

    grating = mi.DiffractionGrating3f(
        45, 
        mi.Vector2f(0.4, 0.4), 
        0.084, 
        args.lobes, 
        mi.DiffractionGratingType.Sinusoidal,
        1, mi.Vector2f(0.0)
    )
    wi = sph_to_dir(dr.deg2rad(45), 0.0)
    wl = 0.45

    compare_samples(grating, wi, wl, args.samples, args.lobes)

    show_sampling_error(grating, wi, wl, 10, args.samples, args.lobes, steps=15)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Sample diffraction grating")
    parser.add_argument("--samples", type=int, default=10, help="Number of samples")
    parser.add_argument("--lobes", type=int, default=5, help="Number of lobes of the diffraction grating")

    args = parser.parse_args()

    main(args)