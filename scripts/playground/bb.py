import mitsuba as mi
import drjit as dr

# Bounce data contains all necessary info to rewind a path and
# compute forward coherence-aware wave transport via PLT 

import numpy as np
import matplotlib.pyplot as plt

# initialize variant
mi.set_variant("cuda_ad_rgb")

bb = mi.BounceBuffer()
# bd = dr.zeros(mi.BounceData3f, 5)
bd = mi.BounceData3f(mi.UInt32(1), 
                     dr.zeros(mi.SurfaceInteraction3f), 
                     mi.Vector3f(1.0), 
                     mi.Vector3f(2.0),
                     mi.UInt32(4),
                     mi.Float(0.5),
                     mi.Spectrum(0.1),
                     mi.Spectrum(0.42),
                     mi.Bool(True),
                     mi.Float(0.5),
                     mi.Bool(True))

print(bd.interaction)