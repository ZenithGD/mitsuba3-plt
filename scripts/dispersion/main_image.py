import argparse

import mitsuba as mi
import drjit as dr

mi.set_variant("cuda_ad_spectral_polarized")

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

from sample import *
from eval import * 

from scripts.utils import sph_to_dir


def run_eval_and_plot(ax, bsdf, az, ev, eval_context, marker_dot):
    # Update incident direction
    theta_i = dr.deg2rad(az)
    phi_i = dr.deg2rad(ev)
    eval_context["wi"] = sph_to_dir(phi_i, theta_i)

    # Evaluate BSDF image
    image, theta_o, phi_o = eval_wbsdf_image(bsdf, eval_context)
    resx = eval_context["resx"]
    resy = eval_context["resy"]

    values_np = np.clip(np.array(image), 0, 1).reshape(3, 2 * resy, resx).transpose(1, 2, 0)

    # Create meshgrid for outgoing directions
    phi = np.linspace(-np.pi, np.pi, 2 * resy + 1)
    theta = np.linspace(0, np.pi, resx + 1)
    PHI, THETA = np.meshgrid(phi, theta, indexing='ij')

    # Clear and redraw
    ax.clear()
    ax.set_title(f"Azimuth: {az:.1f}°, Elevation: {ev:.1f}°")
    ax.pcolormesh(PHI, THETA, values_np, shading='auto')
    ax.set_yticklabels([])
    ax.set_xticklabels([])

    # Draw incident direction dot
    marker_dot[0], = ax.plot([theta_i], [phi_i], 'wo', markersize=5)

    ax.figure.canvas.draw_idle()

def plot_surface_rgb(ax, theta, phi, rgb_values):
    """Render the hemisphere with RGB colors mapped on the surface."""
    x = np.sin(theta) * np.cos(phi)
    y = np.sin(theta) * np.sin(phi)
    z = np.cos(theta)

    ax.plot_surface(
        x, y, z,
        facecolors=rgb_values,
        rstride=1, cstride=1,
        antialiased=False,
        linewidth=0,
        shade=False
    )

def run_eval_and_plot_3d(ax, bsdf, az, ev, eval_context, marker_dot):
    # Update incident direction
    theta_i = dr.deg2rad(az)
    phi_i = dr.deg2rad(ev)
    eval_context["wi"] = sph_to_dir(theta_i, phi_i)

    # Evaluate BSDF image
    image, theta_o, phi_o = eval_wbsdf_image(bsdf, eval_context)
    resx = eval_context["resx"]
    resy = eval_context["resy"]

    values_np = np.clip(np.array(image), 0, 1).reshape(3, 2 * resy, resx).transpose(1, 2, 0)

    phi = np.linspace(-np.pi, np.pi, 2 * resy)
    theta = np.linspace(0, np.pi / 2, resx)  # hemisphere
    PHI, THETA = np.meshgrid(phi, theta, indexing='ij')

    ax.clear()
    ax.set_title(f"Azimuth: {az:.1f}°, Elevation: {ev:.1f}°")
    ax.set_box_aspect([1, 1, 1])
    ax.axis('off')

    plot_surface_rgb(ax, THETA, PHI, values_np)

    # Draw incident direction dot
    xi = 1.1 * (np.sin(phi_i) * np.cos(theta_i))
    yi = 1.1 * (np.sin(phi_i) * np.sin(theta_i))
    zi = 1.1 * (np.cos(phi_i))

    marker_dot[0] = ax.scatter([xi], [yi], [zi], color='red', s=40)

    ax.figure.canvas.draw_idle()


def main(args):
    alpha = {}

    if args.roughnessU and args.roughnessV:
        alpha["alpha_u"] = args.roughnessU
        alpha["alpha_v"] = args.roughnessV
    elif args.roughness:
        alpha["alpha"] = args.roughness

    # bsdf = mi.load_dict({
    #     'type': 'measured',
    #     'filename': 'aniso_morpho_melenaus_rgb.bsdf',
    #     **alpha
    # })

    bsdf = mi.load_dict({
        'type': 'roughconductor',
        'material': 'Au',
        **alpha
    })

    λs = np.random.random(args.resx * 2 * args.resy) * (mi.MI_CIE_MAX - 150 - mi.MI_CIE_MIN) + mi.MI_CIE_MIN

    wavelengths = None
    if mi.is_spectral:
        wavelengths = mi.UnpolarizedSpectrum(λs, λs, λs, λs)

    eval_context = {
        "wi": sph_to_dir(0, dr.deg2rad(90)),  # Initial direction
        "roughness": args.roughness,
        "resx": args.resx,
        "resy": args.resy,
        "wavelengths": wavelengths
    }

    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection='3d')
    plt.subplots_adjust(bottom=0.25)

    marker_dot = [None]
    run_eval_and_plot_3d(ax, bsdf, 0, 90, eval_context, marker_dot)

    ax_az = plt.axes([0.2, 0.1, 0.65, 0.03])
    ax_ev = plt.axes([0.2, 0.05, 0.65, 0.03])
    slider_az = Slider(ax_az, 'Azimuth (°)', -180, 180, valinit=0)
    slider_ev = Slider(ax_ev, 'Elevation (°)', -90, 90, valinit=90)

    def update(val):
        az = slider_az.val
        ev = slider_ev.val
        run_eval_and_plot_3d(ax, bsdf, az, ev, eval_context, marker_dot)

    slider_az.on_changed(update)
    slider_ev.on_changed(update)

    plt.show()

def main_2d(args):
    alpha = {}

    if args.roughnessU and args.roughnessV:
        alpha["alpha_u"] = args.roughnessU
        alpha["alpha_v"] = args.roughnessV
    elif args.roughness:
        alpha["alpha"] = args.roughness

    print(args.roughnessU, args.roughnessV)

    # bsdf_measured = mi.load_dict({
    #     'type': 'measured',
    #     'filename': 'aniso_morpho_melenaus_rgb.bsdf',
    #     **alpha
    # })

    bsdf_conductor = mi.load_dict({
        'type': 'roughconductor',
        'material': 'Au',
        **alpha
    })

    bsdf_grating = mi.load_dict({
        'type': 'roughgrating',
        'distribution': 'ggx',
        'material': 'Au',
        'lobe_type' : 'sinusoidal',
        'height' : 0.05,
        'inv_period_x' : 0.65,
        'inv_period_y' : 0.65,
        'radial' : False,
        'lobes' : 5,
        'grating_angle' : 45.0,
        'coherence' : 2e+3,
        **alpha
    })


    λs = np.random.random(args.resx * 2 * args.resy) * (mi.MI_CIE_MAX - 150 - mi.MI_CIE_MIN) + mi.MI_CIE_MIN

    wavelengths = None
    if mi.is_spectral:
        wavelengths = mi.UnpolarizedSpectrum(λs, λs, λs, λs)
    else:
        wavelengths = mi.Color3f(λs, λs, λs)

    angle = 30
    eval_context = {
        "wi": sph_to_dir(0, dr.deg2rad(angle)),  # Initial direction
        "roughness": args.roughness,
        "resx": args.resx,
        "resy": args.resy,
        "wavelengths": wavelengths
    }

    fig, (ax1, ax2) = plt.subplots(1, 2, subplot_kw={'polar': True})
    plt.subplots_adjust(bottom=0.25)

    marker_dot = [None]  # Holder for incident marker

    run_eval_and_plot(ax1, bsdf_conductor, angle, 0, eval_context, marker_dot)
    run_eval_and_plot(ax2, bsdf_grating, angle, 0, eval_context, marker_dot)

    # Sliders
    ax_az = plt.axes([0.2, 0.1, 0.65, 0.03])
    ax_ev = plt.axes([0.2, 0.05, 0.65, 0.03])
    slider_az = Slider(ax_az, 'Azimuth (°)', -180, 180, valinit=0)
    slider_ev = Slider(ax_ev, 'Elevation (°)', -90, 90, valinit=angle)

    def update(val):
        az = slider_az.val
        ev = slider_ev.val
        run_eval_and_plot(ax1, bsdf_conductor, az, ev, eval_context, marker_dot)
        run_eval_and_plot(ax2, bsdf_grating, az, ev, eval_context, marker_dot)

    slider_az.on_changed(update)
    slider_ev.on_changed(update)

    plt.show()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Sample wBSDF and plot the dispersion of the samples in 3D")
    parser.add_argument("--resx", type=int, help="X resolution of the image", default=64)
    parser.add_argument("--resy", type=int, help="half Y resolution of the image", default=64)
    parser.add_argument("--roughness", type=float, help="Roughness of the grating")
    parser.add_argument("--roughnessU", "-ru", type=float, help="Roughness of the grating in UV direction U")
    parser.add_argument("--roughnessV", "-rv", type=float, help="Roughness of the grating in UV direction V")
    parser.add_argument("--angle", type=float, help="azimuth of incident light", default=0.01)
    args = parser.parse_args() 
    main_2d(args)