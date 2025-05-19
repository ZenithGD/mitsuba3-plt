import numpy as np
import matplotlib.pyplot as plt
import mitsuba as mi
import drjit as dr

import argparse

mi.set_variant("cuda_ad_spectral_polarized")

def main(args):

    wls, srfs = gen_srfs(args.points)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate a set of evenly spaced gaussian profile SRFs in a finite domain")

    parser.add_argument("n", type=int, help="Number of SRFs to generate")
    parser.add_argument("points", type=int, help="Number of points to evaluate for each SRF")
    parser.add_argument("--min_wl", type=float, help="Lower bound of wavelength domain (in nm)", default=380)
    parser.add_argument("--max_wl", type=float, help="Lower bound of wavelength domain (in nm)", default=750)

    main(parser.parse_args())