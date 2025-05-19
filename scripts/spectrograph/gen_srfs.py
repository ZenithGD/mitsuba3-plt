import numpy as np
import matplotlib.pyplot as plt
import mitsuba as mi
import drjit as dr

import argparse

mi.set_variant("cuda_ad_rgb_polarized")

def gen_srf(values : np.array, wl : float, delta_wl : float, n : int, points : int):

    std_dev = delta_wl / 4
    srf = np.exp(-np.square(values - wl) / (2 * std_dev ** 2))
    srf /= np.trapezoid(srf, values) 
    return srf

def show_srfs(values : np.array, srfs : dict):

    fig, ax = plt.subplots()

    for wl, srf in srfs.items():
        # colour for the curve
        col = np.clip(np.ravel(mi.xyz_to_srgb(mi.cie1931_xyz(mi.Float(wl)))), 0, 1)

        plt.plot(values, srf, color=col, label=f"{wl:.3f} nm")

    plt.title("Spectrograph SRFs")
    plt.xlabel("wavelength (nm)")
    plt.ylabel("sensitivity")
    plt.legend()
    plt.show()

def main(args):

    delta_wl = (args.max_wl - args.min_wl) / args.n
    print(delta_wl)
    values = np.linspace(args.min_wl, args.max_wl, args.points)
    srfs = {}
    for wl in np.linspace(args.min_wl, args.max_wl, args.n + 2)[1:-1]:

        srf = gen_srf(values, wl, delta_wl, args.n, args.points)

        print(np.trapezoid(srf, values))

        mi.spectrum_to_file(f"srf_{wl:.3f}nm.spd", values, srf)

        srfs[wl] = srf

    show_srfs(values, srfs)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate a set of evenly spaced gaussian profile SRFs in a finite domain")

    parser.add_argument("n", type=int, help="Number of SRFs to generate")
    parser.add_argument("points", type=int, help="Number of points to evaluate for each SRF")
    parser.add_argument("--min_wl", type=float, help="Lower bound of wavelength domain (in nm)", default=380)
    parser.add_argument("--max_wl", type=float, help="Lower bound of wavelength domain (in nm)", default=750)

    main(parser.parse_args())