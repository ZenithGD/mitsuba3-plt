import argparse

import mitsuba as mi
import drjit as dr

mi.set_variant("cuda_ad_rgb_polarized")

import numpy as np
import matplotlib.pyplot as plt

from sample import *

def plot_roughness_diagrams(alphas, sample_context):
    n = alphas.shape[0]
    fig = plt.figure()
    for i in range(n):
        alpha = alphas[i]
        sample_context["roughness"] = alpha
        bsdf = mi.load_dict({
            'type': 'roughgrating',
            'distribution': 'ggx',
            'alpha' : alpha,

            'lobe_type' : 'sinusoidal',
            'height' : 0.05,
            'inv_period_x' : 0.4,
            'inv_period_y' : 0.4,
            'radial' : False,
            'lobes' : 5,
            'grating_angle' : 0,
        })

        ax = fig.add_subplot(1, n, i+1, projection='polar')
        samples, weights = sample_wbsdf(bsdf, sample_context)

        wi = sample_context["wi"]

        print(weights)

        points = np.array(samples.wo * weights)
        print(weights.shape, points.shape)

        pcols = np.hstack([np.array(weights).T, np.ones((weights.shape[1], 1))])
        pcols = np.clip(pcols, 0, 1) * np.array([0.21, 0.53, 0.9, 0.05])
        
        ax.set_rlim(0, 1)

        print(pcols)

        wi_theta, wi_phi = dir_to_sph(wi)
        theta, phi = dir_to_sph(samples.wo)
        ax.scatter(theta, phi, c=pcols, s=8) 
        ax.scatter(wi_theta, wi_phi, color="r")

        angle = sample_context["angle"]
        ax.set_title(f"alpha = {alpha:.3f}")
    plt.show()

def main(args):
    nsamples = args.samples

    bsdf = mi.load_dict({
        'type': 'roughgrating',
        'distribution': 'ggx',
        'alpha' : args.roughness,

        'lobe_type' : 'sinusoidal',
        'height' : 0.05,
        'inv_period_x' : 0.4,
        'inv_period_y' : 0.4,
        'radial' : False,
        'lobes' : 5,
        'grating_angle' : 0,
    })

    # bsdf = mi.load_dict({
    #     'type': 'roughconductor',
    #     'distribution': 'ggx',
    #     'alpha' : 0.01
    # })

    angle = 0
    sample_context = {
        "nsamples" : nsamples,
        "angle" : angle,
        "wi" : sph_to_dir(dr.deg2rad(angle), 0.0),
        "roughness": args.roughness
    }

    samples, weights = sample_wbsdf(bsdf, sample_context)

    plot_samples(samples, weights, sample_context)

    plot_roughness_diagrams(np.logspace(-3, -1, 5), sample_context)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Sample wBSDF and plot the dispersion of the samples in 3D")
    parser.add_argument("--samples", "-s", type=int, help="Number of samples", default=1000)
    parser.add_argument("--roughness", type=float, help="Roughness of the grating", default=0.01)
    parser.add_argument("--angle", type=float, help="azimuth of incident light", default=0.01)
    args = parser.parse_args() 
    main(args)