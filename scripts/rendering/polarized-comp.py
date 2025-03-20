import mitsuba as mi
import drjit as dr

import time
import os

from utils import *

mi.set_variant("cuda_ad_rgb_polarized")

import numpy as np
import matplotlib.pyplot as plt

import argparse

from scripts.rendering.integrators.path import MISPathIntegrator
from scripts.rendering.integrators.plt import PLTIntegrator
# from scripts.rendering.integrators.plt import PLTIntegrator

def plot_sp_row(axs, sp):

    # plot intensity (s0)
    img = axs[0].imshow(sp[0], cmap='gray')
    plt.colorbar(img, ax=axs[0])
    plt.xticks([]); plt.yticks([])

    # plot linear, diagonal and circular polarization
    img = plot_stokes_component(axs[1], sp[1])
    plt.colorbar(img, ax=axs[1])
    img = plot_stokes_component(axs[2], sp[2])
    plt.colorbar(img, ax=axs[2])
    img = plot_stokes_component(axs[3], sp[3])
    plt.colorbar(img, ax=axs[3])

    axs[0].set_xlabel("S0: Intensity", size=10, weight='bold')
    axs[1].set_xlabel("S1: Horizontal vs. vertical", size=10, weight='bold')
    axs[2].set_xlabel("S2: Diagonal", size=10, weight='bold')
    axs[3].set_xlabel("S3: Circular", size=10, weight='bold')

def main(args):
    nfolders = len(args.folders)
    if nfolders < 2:
        print("At least 2 folders needed!")
        exit(1)

    fig = plt.figure(constrained_layout=True)
    fig.suptitle('Polarized comparison')

    subfigs = fig.subfigures(nrows=nfolders, ncols=1)

    for i, folder in enumerate(args.folders):
        imgs = [ read_exr(os.path.join(folder, f"result_s{p}.exr")) for p in range(4) ]

        axs = subfigs[i].subplots(nrows=1, ncols=4)
        subfigs[i].suptitle(folder)
        plot_sp_row(axs, imgs)

    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Comparison tool for stokes parameters images")
    parser.add_argument("folders", nargs="+", help="folders containing the 4 stokes parameters images")

    args = parser.parse_args()
    main(args)