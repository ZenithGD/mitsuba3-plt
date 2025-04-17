import argparse

import mitsuba as mi
import drjit as dr

import numpy as np
import matplotlib.pyplot as plt

from utils import *

def eval_wbsdf_image(bsdf, eval_context):
    # Create a (dummy) surface interaction to use for the evaluation of the BSDF
    si = dr.zeros(mi.SurfaceInteraction3f)
    
    # Specify an incident direction with 45 degrees elevation
    si.wi = eval_context["wi"]

    # Create grid in spherical coordinates and map it onto the sphere
    lt = dr.linspace(mi.Float,  0,     dr.pi,     eval_context["resx"])
    lp = dr.linspace(mi.Float, -dr.pi, dr.pi, 2 * eval_context["resy"])
    theta_o, phi_o = dr.meshgrid(
        lt, lp
    )
    wo = sph_to_dir(theta_o, phi_o)

    # Evaluate the whole array (18000 directions) at once
    values = bsdf.eval(mi.BSDFContext(), si, wo)

    if mi.is_spectral:
        values = mi.spectrum_to_srgb(mi.unpolarized_spectrum(values), eval_context["wavelengths"])
    else:
        values = mi.unpolarized_spectrum(values)

    return values, theta_o, phi_o

def plot_eval_image(image, theta_o, phi_o, eval_context):
    values_np = np.clip(np.array(image), 0, 1)

    resx = eval_context["resx"]
    resy = eval_context["resy"]

    # Construct meshgrid
    phi = np.linspace(-np.pi, np.pi, 2 * resy + 1)      # azimuth
    theta = np.linspace(0, np.pi, resx + 1)             # elevation
    PHI, THETA = np.meshgrid(phi, theta, indexing='ij')  # shape: (2*resy+1, resx+1)

    # Reshape image: (channels, height, width) → (height, width, channels)
    values_np = values_np.reshape(3, 2 * resy, resx).transpose(1, 2, 0)  # (2*resy, resx, 3)

    fig = plt.figure()
    ax = fig.add_subplot(111, polar=True)
    ax.pcolormesh(PHI, THETA, values_np, shading='auto')  # ✅ swap PHI/THETA

    plt.show()