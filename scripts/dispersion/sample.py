import mitsuba as mi
import drjit as dr
import numpy as np
import matplotlib.pyplot as plt

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
    si.sh_frame = mi.Frame3f(si.n)

    samples, gr = bsdf.wbsdf_sample(ctx, si, sample, sample2, lobe_sample2)

    return samples, mi.unpolarized_spectrum(gr.L)

def plot_samples(samples : mi.BSDFSample3f, weights : mi.UnpolarizedSpectrum, sample_context):
    
    fig = plt.figure()
    ax1 = fig.add_subplot(1, 2, 1, projection='3d')
    ax2 = fig.add_subplot(1, 2, 2, projection='polar')

    weights = np.array(weights)
    l = weights[0]

    wi = sample_context["wi"]

    points = np.array(samples.wo)
    print(weights.shape, points.shape)

    ax1.scatter(points[0], points[1], points[2], 'o')
    ax1.quiver(0, 0, 0, wi[0], wi[1], wi[2], color="r")
    ax1.set_xlim3d(-1.2, 1.2)
    ax1.set_ylim3d(-1.2, 1.2)
    ax1.set_zlim3d(-1.2, 1.2)

    plt.show() 