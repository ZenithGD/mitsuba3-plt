import numpy as np
import matplotlib.pyplot as plt
import mitsuba as mi
import drjit as dr

import argparse

mi.set_variant("cuda_ad_rgb_polarized")

def gen_srf(domain_wls : np.array, measured_wl : float, delta_wl : float):

    std_dev = delta_wl * 2
    srf = np.exp(-np.square(domain_wls - measured_wl) / (2 * std_dev ** 2))
    srf /= np.trapezoid(srf, domain_wls) 
    return srf

def show_srfs(domain_wls : np.array, measured_wls : np.array, srfs : list):

    fig, ax = plt.subplots()

    for i, srf in enumerate(srfs):
        # colour for the curve
        col = np.clip(np.ravel(mi.xyz_to_srgb(mi.cie1931_xyz(mi.Float(measured_wls[i])))), 0, 1)

        plt.plot(domain_wls, srf, color=col, label=f"{measured_wls[i]:.3f} nm")

    plt.title("Spectrograph SRFs")
    plt.xlabel("wavelength (nm)")
    plt.ylabel("sensitivity")
    plt.legend()
    plt.show()

def gen_srfs(n, points, min_wl, max_wl):

    delta_wl = (max_wl - min_wl) / (n + 2)
    domain_wls = np.linspace(min_wl, max_wl, points)
    measured_wls = np.linspace(min_wl, max_wl, n + 2)[1:-1]
    srfs = []
    for wl in measured_wls:

        srf = gen_srf(domain_wls, wl, delta_wl)

        #mi.spectrum_to_file(f"srf_{wl:.3f}nm.spd", domain_wls, srf)
        srfs.append(srf)

    return domain_wls, measured_wls, srfs

def main(args):

    domain_wls, measured_wls, srfs = gen_srfs(args.n, args.points, args.min_wl, args.max_wl)

    if args.plot:
        show_srfs(domain_wls, measured_wls, srfs)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate a set of evenly spaced gaussian profile SRFs in a finite domain")

    parser.add_argument("n", type=int, help="Number of SRFs to generate")
    parser.add_argument("points", type=int, help="Number of points to evaluate for each SRF")
    parser.add_argument("--min_wl", type=float, help="Lower bound of wavelength domain (in nm)", default=380)
    parser.add_argument("--max_wl", type=float, help="Lower bound of wavelength domain (in nm)", default=750)
    parser.add_argument("--plot", "-s", action="store_true", help="Whether to plot the SRFs")
    
    main(parser.parse_args())