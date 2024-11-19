import mitsuba as mi
import drjit as dr
from dataclasses import dataclass
import time

# Bounce data contains all necessary info to rewind a path and
# compute forward coherence-aware wave transport via PLT 

import numpy as np
import matplotlib.pyplot as plt

# initialize variant
mi.set_variant("cuda_ad_rgb")

coh = dr.zeros(mi.Coherence3f, 5)
#print(coh)

@dataclass
class BounceData:
    # interaction : mi.SurfaceInteraction3f
    wi : mi.Vector3f
    wo : mi.Vector3f
    bsdf : mi.BSDFPtr
    throughput : mi.Spectrum
    bsdf_weight : mi.Spectrum
    lobe_type : mi.UInt32
    last_nondelta_pdf : mi.Float
    rr_weight : mi.Float
    # is_emitter : mi.Bool
    # active : mi.Bool

gr = dr.zeros(mi.GeneralizedRadiance3f, 5)
gr.L += mi.Float(5)

print(gr.L)
