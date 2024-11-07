import argparse

import scipy.special as sp
import matplotlib.pyplot as plt
import pandas as pd

import numpy as np
import mitsuba as mi
import drjit as dr
import time

def integrate_trapz(func, a, b, points):
    h = (b - a) / (points - 1)
    t = dr.linspace(dr.cuda.Float, a, b, points)

    I = dr.cuda.Float(0)
    for i in range(1, points - 1):
        I += func(t[i])

    return h * (func(t[0]) + 2 * I + func(t[-1]))

def integrate_simpson(func, a, b, points):
    h = (b - a) / (points - 1)
    t = dr.linspace(dr.cuda.Float, a, b, points)

    I_odd = dr.cuda.Float(0)
    I_even = dr.cuda.Float(0)
    for i in range(1, points - 1, 2):
        print(i, t[i], func(t[i]))
        I_odd += func(t[i])

    for i in range(2, points - 1, 2):
        print(i, t[i], func(t[i]))
        I_even += func(t[i])

    print(4 * I_odd,  2 * I_even)

    return (h / 3.0) * (func(t[0]) + 4 * I_odd + 2 * I_even + func(t[-1]))


def approx_jn(x, n, points):
    gm = lambda xx, nn, t : dr.cos(nn * t - xx * dr.sin(t))

    nn = dr.cuda.Float(n)
    return 1 / np.pi * mi.math.integrate_simpson(lambda t: gm(x, nn, t), 0, np.pi, 100)

# compute approximations and the reference implementation
def compute_jn(dmin, dmax, **kwargs) -> tuple:
    npoints = kwargs["npoints"] if "npoints" in kwargs else 100
    orders = kwargs["norders"] if "norders" in kwargs else 5

    # x array repeated n times
    vx = np.repeat(np.expand_dims(np.linspace(dmin, dmax, npoints, endpoint=True), axis=0), orders, 0)
    # range array repeated m times
    vo = np.repeat(np.arange(orders, dtype=int).reshape(orders, 1), npoints, axis=1)

    # compute approximations
    vxr, vor = dr.cuda.Float(vx.ravel()), dr.cuda.Int32(vo.ravel())
    start = time.perf_counter_ns()
    approx = np.array(mi.math.bessel_j(vxr, vor)).reshape(orders, npoints)
    ap_time = time.perf_counter_ns() - start
    
    # compute errors w.r.t reference impl
    start = time.perf_counter_ns()
    jn = sp.jn(vo, vx)
    jn_time = time.perf_counter_ns() - start
    
    print(f"time approx = {ap_time*1e-3:.9f} us.")
    print(f"jn approx = {jn_time*1e-3:.9f} us.")

    return vx, jn, approx

def viz(x, jn, approx):

    # plot bessel j and the errors
    fig, axes = plt.subplots(3, 1)

    # loop through all orders        
    for i in range(x.shape[0]):

        axes[0].plot(x[i], jn[i], label=f"$J_{i}(x)$")
        axes[1].plot(x[i], approx[i], label=f"$\hat J_{i}(x)$")
        axes[2].plot(x[i], np.log10(np.abs(jn[i] - approx[i])), label=f"$\log |\hat J_{i}(x) - J_{i}(x)|$")

    # set options for plots
    for ax in axes.ravel():
        ax.grid()
        ax.legend()

    axes[0].set_title("Reference implementation")
    axes[1].set_title("Our approximation")
    axes[2].set_title("log abs error w.r.t reference")    


    plt.show()

def main(args):
    # set environment
    mi.set_variant("cuda_ad_rgb")

    # compute different approaches
    x, jn, approx = compute_jn(
        args.dmin, 
        args.dmax, 
        npoints=args.npoints,
        norders=args.norders)
    
    # report errors
    min_eps_approx = [ np.min(np.abs(approx[i] - jn[i])) for i in range(x.shape[0]) ]
    
    max_eps_approx = [ np.max(np.abs(approx[i] - jn[i])) for i in range(x.shape[0]) ]

    mean_eps_approx = [ np.mean(np.abs(approx[i] - jn[i])) for i in range(x.shape[0]) ]

    d = {
        'approx_min': min_eps_approx, 
        'approx_max': max_eps_approx, 
        'approx_avg': mean_eps_approx
    }
    
    df = pd.DataFrame(data=d)
    print(df)
    
    if args.viz:
        viz(x, jn, approx)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Test BesselJ function approximation")
    parser.add_argument("--viz", action="store_true", help="Visualize error graphs")
    parser.add_argument("--dmin", type=float, default=0, help="Minimum of the domain")
    parser.add_argument("--dmax", type=float, default=15, help="Maximum of the domain")
    parser.add_argument("--npoints", type=int, default=100, help="Number of points to evaluate")
    parser.add_argument("--norders", type=int, default=5, help="Number of orders to evaluate")

    args = parser.parse_args()
    main(args)

