import argparse

import mitsuba as mi
import drjit as dr

mi.set_variant("cuda_ad_rgb_polarized")

import numpy as np
import matplotlib.pyplot as plt

from dispersion import *

from scripts.utils import sph_to_dir

def main(args):

    # create diffuse dispersion diagram
    angles, disp = diffuse_dispersion(args)

    plot_dispersion(angles, disp, show_sp=mi.is_polarized, title="Diffuse importance")

     # create conductor dispersion diagram
    angles, disp = conductor_dispersion(args)

    plot_dispersion(angles, disp, show_sp=mi.is_polarized, title="Conductor importance")

    # create conductor dispersion diagram
    angles, disp = dielectric_dispersion(args)

    plot_dispersion(angles, disp, show_sp=mi.is_polarized, show_360=True, title="Dielectric importance")

    # create rough conductor dispersion diagram
    angles, disp = roughconductor_dispersion(args)

    plot_dispersion(angles, disp, show_sp=mi.is_polarized, title="Rough conductor importance")

    # create grating dispersion diagram
    angles, disp = grating_dispersion(args)

    plot_dispersion(angles, disp, show_sp=mi.is_polarized, title="Grating importance")

    plt.show()

if __name__ == '__main__':
    # initialize variant

    parser = argparse.ArgumentParser(description="Analize dispersion diagram of a diffraction grating wBSDF")
    parser.add_argument("--inv-period", type=float)
    args = parser.parse_args() 
    main(args)