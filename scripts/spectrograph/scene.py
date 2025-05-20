import numpy as np
import matplotlib.pyplot as plt
import mitsuba as mi
import drjit as dr
from scripts.utils import sph_to_dir

from gen_srfs import gen_srfs

import argparse

mi.set_variant("cuda_ad_spectral_polarized")

def plot_scene_elements(light_dir, sensors):

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1, projection='3d')

    ax.quiver(0,0,0,light_dir.x, light_dir.y, light_dir.z, length=0.5)

    # plot axes 
    ax.set_xlim3d(-1, 1)
    ax.set_ylim3d(-1, 1)
    ax.set_zlim3d(-1, 1)
    ax.set_xlabel('X axis')
    ax.set_ylabel('Y axis')
    ax.set_zlabel('Z axis')
    plt.show()

def main(args):

    scene = {}

    wls, srfs = gen_srfs(args.n, args.points, args.min_wl, args.max_wl)

    # instantiate grating model here 
    grating_dict = {
        'type': 'roughgrating',
        'distribution': 'ggx',
        'material': 'Au',
        'lobe_type' : 'sinusoidal',
        'height' : 0.05,
        'inv_period_x' : 0.65,
        'inv_period_y' : 0.65,
        'radial' : False,
        'lobes' : 5,
        'grating_angle' : 0.0,
        'alpha' : 0.04
    }
    bsdf_grating = mi.load_dict(grating_dict)

    grtype = mi.DiffractionGratingType.Sinusoidal
    grating = mi.DiffractionGrating3f(
        grating_dict['grating_angle'],
        mi.Vector2f(grating_dict['inv_period_x'], grating_dict['inv_period_x']), 
        grating_dict['height'], grating_dict['lobes'], grtype, 1, 
        mi.Vector2f(0.0))
    
    # shading frame construction
    s = mi.Vector3f(0,  0, -1)
    t = mi.Vector3f(0, -1,  0)
    n = mi.Vector3f(1,  0,  0)
    grating_frame = mi.Frame3f(s, t, n)

    # directional light angle
    incident = np.deg2rad(-15) - np.pi / 2
    if incident > np.pi:
        incident -= 2 * np.pi
    light_dir = sph_to_dir(incident, 0)

    sensors = {}

    for i, (wl, srf) in enumerate(srfs.items()):
        # pass incident direction to local coords

        # diffract first lobe
        pass

    if args.plot:

        plot_scene_elements(light_dir, sensors)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate a set of evenly spaced gaussian profile SRFs in a finite domain")

    parser.add_argument("n", type=int, help="Number of SRFs to generate")
    parser.add_argument("points", type=int, help="Number of points to evaluate for each SRF")
    parser.add_argument("--min_wl", type=float, help="Lower bound of wavelength domain (in nm)", default=380)
    parser.add_argument("--max_wl", type=float, help="Lower bound of wavelength domain (in nm)", default=750)

    parser.add_argument("--plot", action="store_true", help="Plot the scene schema after generating it")

    main(parser.parse_args())