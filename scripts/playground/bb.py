import mitsuba as mi
import drjit as dr

# Bounce data contains all necessary info to rewind a path and
# compute forward coherence-aware wave transport via PLT 

import numpy as np
import matplotlib.pyplot as plt

# initialize variant
mi.set_variant("cuda_ad_rgb")

@dr.syntax
def task(max_depth):

    buffer : mi.Local[mi.SurfaceInteraction3f] = dr.alloc_local(mi.SurfaceInteraction3f, max_depth)
    
    i = mi.UInt(0)
    while i < 12:

        # bd = dr.zeros(mi.BounceData3f, 5)
        # bd = mi.BounceData3f(mi.UInt32(i), 
        #                     dr.zeros(mi.SurfaceInteraction3f), 
        #                     mi.Vector3f(1.0), 
        #                     mi.Vector3f(2.0),
        #                     mi.UInt32(4),
        #                     mi.Float(0.5),
        #                     mi.Spectrum(0.1),
        #                     mi.Spectrum(0.42),
        #                     mi.Bool(True),
        #                     mi.Float(0.5),
        #                     mi.Bool(True))

        bd = dr.zeros(mi.SurfaceInteraction3f)
        bd.t = i
        
        buffer[i] = bd
        
        i += 1

    print(buffer[4])

if __name__ == '__main__':
    task(12)