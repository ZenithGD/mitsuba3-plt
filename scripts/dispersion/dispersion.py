import argparse

import mitsuba as mi
import drjit as dr

import numpy as np
import matplotlib.pyplot as plt

from utils import *

def diffuse_dispersion(args, n = 400):
    bsdf = mi.load_dict({
        'type': 'diffuse',
        'reflectance': {
            'type': 'rgb',
            'value': [0.4, 0.2, 0.8]
        }
    })

    # Create a (dummy) surface interaction to use for the evaluation of the BSDF
    si = dr.zeros(mi.SurfaceInteraction3f)

    # Specify an incident direction with 0 degrees elevation (normal incidence)
    si.wi = sph_to_dir(dr.deg2rad(45.0), 0.0)

    # Create grid in spherical coordinates and map it onto the sphere
    res = n
    theta_o = dr.linspace(mi.Float, 0, 2 * dr.pi, 2 * res)

    wo = sph_to_dir(theta_o, 0.0)

    print(bsdf.coherence_transform(mi.BSDFContext(), si, wo))
    val, pdf = bsdf.wbsdf_eval_pdf(mi.BSDFContext(), si, wo)
    # Evaluate the whole array at once
    print(pdf)
    return theta_o, val

def grating_dispersion(args):
    pass

def plot_dispersion(angles, values):
    values_np = np.array(mi.unpolarized_spectrum(values.L))

    print(values.L)
    angles_np = np.array(angles)

    # Extract channels of BRDF values
    values_r = values_np[0]
    values_g = values_np[1]
    values_b = values_np[2]

    print(values_r[:5], values_g[:5], values_b[:5])

    # Plot values for spherical coordinates (upper hemisphere)
    fig, ax = plt.subplots(figsize=(8, 4), subplot_kw={'projection': 'polar'})
    ax.set_thetamin(-90)
    ax.set_thetamax(90)
    ax.set_theta_offset(np.pi / 2.0)

    # plot red, green, blue separately
    ax.plot(angles_np, values_r, '-r')
    ax.plot(angles_np, values_g, '-g')
    ax.plot(angles_np, values_b, '-b')

    plt.show()