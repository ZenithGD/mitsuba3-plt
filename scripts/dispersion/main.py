import argparse

import mitsuba as mi
import drjit as dr

import numpy as np
import matplotlib.pyplot as plt

from dispersion import *

def main(args):

    # create diffuse dispersion diagram
    angles, disp = diffuse_dispersion(args)

    plot_dispersion(angles, disp)

    # create grating dispersion diagram
    grating_dispersion(args)

if __name__ == '__main__':
    # initialize variant
    mi.set_variant("cuda_ad_rgb")

    parser = argparse.ArgumentParser(description="Analize dispersion diagram of a diffraction grating wBSDF")
    parser.add_argument("--inv-period", type=float)
    args = parser.parse_args() 
    main(args)