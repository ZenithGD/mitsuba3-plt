import mitsuba as mi
import drjit as dr
import numpy as np
import matplotlib.pyplot as plt
# plt.rcParams['text.usetex'] = True

from utils import *

def sample_wbsdf(bsdf : mi.BSDF, sample_context):
    
    sample = np.random.rand(sample_context["nsamples"])
    sample2 = np.random.rand(2, sample_context["nsamples"])
    lobe_sample2 = np.random.rand(2, sample_context["nsamples"])

    ctx = mi.BSDFContext(mi.TransportMode.Importance)
    si = mi.SurfaceInteraction3f()
    si.p = [0, 0, 0]
    si.n = [0, 0, 1]
    si.wi = sample_context["wi"]
    si.wavelengths = sample_context["wavelengths"]
    si.sh_frame = mi.Frame3f(si.n)

    samples, gr = bsdf.wbsdf_sample(ctx, si, sample, sample2, lobe_sample2)

    return samples, mi.unpolarized_spectrum(gr.L)

def plot_samples(samples : mi.BSDFSample3f, weights : mi.UnpolarizedSpectrum, sample_context):
    
    fig = plt.figure()
    ax1 = fig.add_subplot(1, 2, 1, projection='3d')
    ax2 = fig.add_subplot(1, 2, 2, projection='polar')

    scaled_weights = mi.xyz_to_srgb(mi.cie1931_xyz(sample_context["wavelengths"][0]))

    l = scaled_weights

    wi = sample_context["wi"]

    points = np.array(samples.bsdf_sample.wo)
    pcols = np.hstack([np.array(l).T, np.ones((l.shape[1], 1))])
    pcols = np.clip(pcols, 0, 1) * np.array([1, 1, 1, 0.05])
    ax1.scatter(points[0], points[1], points[2], 'o')
    ax1.quiver(0, 0, 0, wi[0], wi[1], wi[2], color="r")
    ax1.set_xlim3d(-1.2, 1.2)
    ax1.set_ylim3d(-1.2, 1.2)
    ax1.set_zlim3d(-1.2, 1.2)
    ax1.set_xlabel('X axis')
    ax1.set_ylabel('Y axis')
    ax1.set_zlabel('Z axis')
    ax2.set_rlim(0, 1)

    wi_theta, wi_phi = dir_to_sph(wi)
    theta, phi = dir_to_sph(samples.bsdf_sample.wo)
    ax2.scatter(theta, phi, c=pcols, s=8) 
    ax2.scatter(wi_theta, wi_phi, color="r")

    alpha = sample_context["roughness"]
    angle = sample_context["angle"]
    fig.suptitle(f"alpha = {alpha}, theta_i = {angle}")
    plt.show() 