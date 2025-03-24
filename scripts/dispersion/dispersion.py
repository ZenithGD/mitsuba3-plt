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
            'value': [0.2, 0.25, 0.7]
        }
    })

    # Create a (dummy) surface interaction to use for the evaluation of the BSDF
    si = dr.zeros(mi.SurfaceInteraction3f)

    # Specify an incident direction with 0 degrees elevation (normal incidence)
    si.wi = sph_to_dir(dr.deg2rad(45.0), 0.0)
    si.t = 0.5

    # Create grid in spherical coordinates and map it onto the sphere
    res = n
    theta_o = dr.linspace(mi.Float, 0, 2 * dr.pi, 2 * res)

    wo = sph_to_dir(theta_o, 0.0)
    
    ctx = mi.BSDFContext(mi.TransportMode.Impotance)

    val = bsdf.wbsdf_weight(ctx, si, wo)
    val = val.L 

    # val = bsdf.eval(ctx, si, wo)

    # Evaluate the whole array at once
    return theta_o, val

def conductor_dispersion(args, n = 400):
    bsdf = mi.load_dict({
        'type': 'conductor',
        'material' : "Ag"
    })

    # Create a (dummy) surface interaction to use for the evaluation of the BSDF
    si = dr.zeros(mi.SurfaceInteraction3f)

    # Specify an incident direction with 0 degrees elevation (normal incidence)
    si.wi = sph_to_dir(dr.deg2rad(45.0), 0.0)

    # Create grid in spherical coordinates and map it onto the sphere
    res = n
    theta_o = dr.linspace(mi.Float, 0, 2 * dr.pi, 2 * res)

    wo = sph_to_dir(theta_o, 0.0)

    ctx = mi.BSDFContext(mi.TransportMode.Impotance)
    val = bsdf.wbsdf_weight(ctx, si, wo)
    val = val.L

    return theta_o, val

def dielectric_dispersion(args, n = 400):
    bsdf = mi.load_dict({
        'type': 'dielectric',
        'int_ior': 'amber',
        'ext_ior': 'water'
    })

    # Create a (dummy) surface interaction to use for the evaluation of the BSDF
    si = dr.zeros(mi.SurfaceInteraction3f)

    # Specify an incident direction with 0 degrees elevation (normal incidence)
    si.wi = sph_to_dir(dr.deg2rad(45.0), 0.0)

    # Create grid in spherical coordinates and map it onto the sphere
    res = n
    theta_o = dr.linspace(mi.Float, 0, 2 * dr.pi, 2 * res)

    wo = sph_to_dir(theta_o, 0.0)

    ctx = mi.BSDFContext(mi.TransportMode.Importance)
    val = bsdf.wbsdf_weight(ctx, si, wo)
    val = val.L

    return theta_o, val

def roughconductor_dispersion(args, n = 400):
    bsdf = mi.load_dict({
        'type': 'roughconductor',
        'material' : "Au",
        'alpha' : 0.3
    })

    # Create a (dummy) surface interaction to use for the evaluation of the BSDF
    si = dr.zeros(mi.SurfaceInteraction3f)

    # Specify an incident direction with 0 degrees elevation (normal incidence)
    si.wi = sph_to_dir(dr.deg2rad(45.0), 0.0)

    # Create grid in spherical coordinates and map it onto the sphere
    res = n
    theta_o = dr.linspace(mi.Float, 0, 2 * dr.pi, 2 * res)

    wo = sph_to_dir(theta_o, 0.0)

    ctx = mi.BSDFContext(mi.TransportMode.Importance)
    val, pdf = bsdf.eval_pdf(ctx, si, wo)
    val = val

    return theta_o, val

def grating_dispersion(args):
    pass
