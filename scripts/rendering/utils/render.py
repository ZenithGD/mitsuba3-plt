import mitsuba as mi
import drjit as dr

import json
import time
import os

from utils import *

import numpy as np
import matplotlib.pyplot as plt

import argparse

from scripts.utils import *
# from scripts.rendering.integrators.plt import PLTIntegrator

def render_scene(scene, samples, integrator="path", denoise=False):
    
    #render scene using the desired integrator
    integrator = mi.load_dict({
        "type" : "stokes",
        "nested" : {
            "type" : integrator,
            "max_depth": 7,
            "rr_depth": 50,
            'samples_per_pass': 512
        }
    })
    result = integrator.render(scene, spp=samples)
    bmp = mi.Bitmap(result).convert()

    L, sp = stokes_to_bitmaps(bmp)
    
    if denoise:
        print("Denoising...")
        print(L.size())
        # Denoise the rendered image
        denoiser = mi.OptixDenoiser(input_size=L.size(), albedo=False, normals=False, temporal=False)
        L = denoiser(L)

        for i, s in enumerate(sp):
            sp[i] = denoiser(s)

    return L, sp, result