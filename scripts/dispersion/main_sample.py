import argparse

import mitsuba as mi
import drjit as dr

mi.set_variant("cuda_ad_rgb_polarized")

import numpy as np
import matplotlib.pyplot as plt

from sample import *

from scripts.utils import *

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
            'grating_angle' : 0.0,
        })

        ax = fig.add_subplot(1, n, i+1, projection='polar')
        samples, weights = sample_wbsdf(bsdf, sample_context)

        scaled_weights = mi.xyz_to_srgb(mi.cie1931_xyz(sample_context["wavelengths"][0]))
        l = scaled_weights

        points = np.array(samples.bsdf_sample.wo)
        pcols = np.hstack([np.array(l).T, np.ones((l.shape[1], 1))])
        pcols = np.clip(pcols, 0, 1) * np.array([1, 1, 1, 0.05])
        wi = sample_context["wi"]

        ax.set_rlim(0, 1)

        wi_theta, wi_phi = dir_to_sph(wi)
        theta, phi = dir_to_sph(samples.bsdf_sample.wo)
        ax.scatter(theta, phi, c=pcols, s=8) 
        ax.scatter(wi_theta, wi_phi, color="r")

        angle = sample_context["angle"]
        ax.set_title(f"alpha = {alpha:.3f}")
    plt.show()

def main(args):
    nsamples = args.samples

    alpha = {}

    if args.roughnessU and args.roughnessV:
        alpha["alpha_u"] = args.roughnessU
        alpha["alpha_v"] = args.roughnessV
    
    elif args.roughness:
        alpha["alpha"] = args.roughness

    print(args.roughnessU, args.roughnessV)

    bsdf = mi.load_dict({
        'type': 'roughgrating',
        'distribution': 'ggx',
        'lobe_type' : 'sinusoidal',
        'height' : 0.05,
        'inv_period_x' : 0.4,
        'inv_period_y' : 0.4,
        'radial' : False,
        'lobes' : 5,
        'grating_angle' : 0.0,
        **alpha
    })

    # bsdf = mi.load_dict({
    #     'type': 'roughconductor',
    #     'distribution': 'ggx',
    #     'alpha' : 0.01
    # })
    λs = np.random.random(nsamples) * (mi.MI_CIE_MAX - 150 - mi.MI_CIE_MIN) + mi.MI_CIE_MIN
    # λs = dr.linspace(mi.Float, mi.MI_CIE_MIN, mi.MI_CIE_MAX - 200, nsamples)
    if mi.is_spectral:
        wavelengths = mi.UnpolarizedSpectrum(
            λs, λs, λs, λs
        )
    else:
        wavelengths = mi.UnpolarizedSpectrum(
            λs, λs, λs
        )

    angle = args.angle
    sample_context = {
        "nsamples" : nsamples,
        "angle" : angle,
        "wi" : sph_to_dir(dr.deg2rad(angle), 0.0),
        "roughness": args.roughness,
        "wavelengths" : wavelengths
    }

    print(sample_context["wi"])

    samples, weights = sample_wbsdf(bsdf, sample_context)

    plot_samples(samples, weights, sample_context)

    plot_roughness_diagrams(np.logspace(-3, -1, 5), sample_context)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Sample wBSDF and plot the dispersion of the samples in 3D")
    parser.add_argument("--samples", "-s", type=int, help="Number of samples", default=1000)
    parser.add_argument("--roughness", type=float, help="Roughness of the grating", default=0.01)
    parser.add_argument("--roughnessU", "-ru", type=float, help="Roughness of the grating in UV direction U")
    parser.add_argument("--roughnessV", "-rv", type=float, help="Roughness of the grating in UV direction V")
    parser.add_argument("--angle", type=float, help="azimuth of incident light", default=0.0)
    args = parser.parse_args() 
    main(args)