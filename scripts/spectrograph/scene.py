import numpy as np
import matplotlib.pyplot as plt
import mitsuba as mi
import drjit as dr

from tqdm import tqdm

import os

from scripts.utils import *

from gen_srfs import gen_srfs

from pprint import pprint

import argparse
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

mi.set_variant("scalar_rgb")

def plot_scene_elements(light_dir : mi.Vector3f, sensors : dict, grating_patch : dict):

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1, projection='3d')

    light_dist = 0.7
    ax.quiver(
        -light_dir[0] * light_dist, -light_dir[1] * light_dist, -light_dir[2] * light_dist,
         light_dir[0], light_dir[1], light_dir[2], length=0.5, color="orange")

    for i, sensor in enumerate(sensors):
        origin = sensor["origin"]
        dir = sensor["direction"]
        ax.quiver(origin[0], origin[1], origin[2], dir[0], dir[1], dir[2], length=0.1, color="blue")

    # show rectangle patch
    vertices = [
        mi.Vector3f(-1, -1, 0),
        mi.Vector3f( 1, -1, 0),
        mi.Vector3f( 1,  1, 0),
        mi.Vector3f(-1,  1, 0),
    ]

    world_vertices = [ np.ravel(np.array(grating_patch["to_world"] @ v).T) for v in vertices ]
    poly = Poly3DCollection([world_vertices], alpha=0.8)
    ax.add_collection3d(poly)

    # plot axes 
    ax.set_xlim3d(-0.7, 0.7)
    ax.set_ylim3d(-0.7, 0.7)
    ax.set_zlim3d(-0.7, 0.7)
    ax.set_xlabel('X axis')
    ax.set_ylabel('Y axis')
    ax.set_zlabel('Z axis')
    plt.show()

def generate_scene_elements(folder_path, domain_wls, measured_wls, srfs, use_srfs):
    # instantiate grating model here 
    grating_bsdf = {
        'type': 'roughgrating',
        'distribution': 'ggx',
        'lobe_type' : 'sinusoidal',
        'height' : 0.05,
        'inv_period_x' : 0.7,
        'inv_period_y' : 0.7,
        'radial' : False,
        'lobes' : 5,
        'multiplier' : 10.0,
        'grating_angle' : 0.0,
        'alpha' : 0.03
    }

    grtype = mi.DiffractionGratingType.Sinusoidal
    grating = mi.scalar_rgb.DiffractionGrating3f(
        grating_bsdf['grating_angle'],
        mi.ScalarVector2f(grating_bsdf['inv_period_x'], grating_bsdf['inv_period_x']), 
        grating_bsdf['height'], grating_bsdf['lobes'], grtype, 1, 
        mi.ScalarVector2f(0.0))
    
    # shading frame construction
    s = mi.ScalarVector3f(0, -1,  0)
    t = mi.ScalarVector3f(0,  0,  1)
    n = mi.ScalarVector3f(1,  0,  0)
    grating_frame = mi.scalar_rgb.Frame3f(s, t, n)

    # directional light angle
    incident = np.deg2rad(-15) - np.pi / 2
    if incident > np.pi:
        incident -= 2 * np.pi
    light_dir = scalar_sph_to_dir(incident, 0)
    light_dir_local = grating_frame.to_local(light_dir)

    sensors = []
    
    L = 0.4
    for i, wl in tqdm(enumerate(measured_wls)):
        mi.spectrum_to_file(os.path.join(folder_path, "spectra", f"srf_{i}.spd"), domain_wls, srfs[i])

        # diffract first lobe (wi)
        local_diff_dir, mask = grating.diffract(-light_dir_local, mi.ScalarVector2i(2, 0), float(wl * 1e-3))
        
        # back to global frame
        diff_dir = grating_frame.to_world(local_diff_dir)

        # position of the sensor at distance L to origin
        pos = diff_dir * L
        
        # save sensor dict
        origin = np.ravel(pos)
        direction = np.ravel(-diff_dir)
        sensor = {
            'type' : 'orthographic',
            # 'origin' : np.ravel(pos),
            # 'direction' : np.ravel(-diff_dir),
            'to_world' : mi.scalar_rgb.Transform4f().look_at(origin=origin, target=[0,0,0], up=[0,0,1]),
            
            'film' : {
                'type': 'hdrfilm',
                'width': 1,
                'height': 1,
                'sample_border': False
            }
        }

        if use_srfs:
            sensor["srf"] = {
                'type' : 'spectrum',
                'filename' : os.path.join(folder_path, "spectra", f"srf_{i}.spd")
            }

        sensors.append(sensor)
    # generate a patch with normals in the positive X dir at origin 0,0,0
    patch_transform = mi.scalar_rgb.Transform4f().to_frame(grating_frame).scale([0.1, 1, 0.1])

    grating_patch = {
        'type': 'rectangle',
        'material': {
            'type' : 'twosided',
            'bsdf' : grating_bsdf
        },
        'to_world' : patch_transform
    }

    return light_dir, sensors, grating_patch

def build_scene(light_dir, sensors, grating_patch, incoming_spectra = 1.0):
    
    batch_sensor = { 
        f"sensor{i}" : s for i, s in enumerate(sensors)
    }

    batch_sensor["type"] = "batch"
    batch_sensor["film"] = {
        'type': 'hdrfilm',
        'width': len(sensors),
        'height': 1,
        'sample_border': False
    }
    batch_sensor["sampler"] = {
        'type': 'independent',
        'sample_count': 512
    }

    # scene dict
    scene = {
        'type' : 'scene',
        'sensor' : batch_sensor,
        'grating_patch' : grating_patch,
        'light' : {
            'type': 'directional',
            'direction': np.ravel(light_dir),
            'irradiance': incoming_spectra
        }
    }

    return scene

def main(args):

    # create folder structure
    sp_sub = os.path.join(args.outdir, "spectra")
    try:
        os.makedirs(args.outdir)
        print(f"Creating folder at '{args.outdir}'")
        os.makedirs(sp_sub)
        print(f"Creating spectra folder at '{sp_sub}'")
    except FileExistsError:
        pass

    domain_wls, measured_wls, srfs = gen_srfs(args.n, args.points, args.min_wl, args.max_wl)
    light_dir, sensors, grating_patch = generate_scene_elements(args.outdir, domain_wls, measured_wls, srfs, args.use_srfs)
    scene = build_scene(light_dir, sensors, grating_patch)

    mi.xml.dict_to_xml(scene, os.path.join(args.outdir, "scene.xml"))

    if args.plot:
        plot_scene_elements(light_dir, sensors, grating_patch)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate a set of evenly spaced gaussian profile SRFs in a finite domain")

    parser.add_argument("outdir", help="Folder to store the scene.")
    parser.add_argument("n", type=int, help="Number of sensors to generate")
    parser.add_argument("points", type=int, help="Amount of values in wavelength domain")
    parser.add_argument("--min_wl", type=float, help="Lower bound of wavelength domain (in nm)", default=380)
    parser.add_argument("--max_wl", type=float, help="Lower bound of wavelength domain (in nm)", default=750)
    parser.add_argument("--use_srfs", action="store_true", help="Use generated SRFs to restrict the captured light")

    parser.add_argument("--plot", action="store_true", help="Plot the scene schema after generating it")

    main(parser.parse_args())