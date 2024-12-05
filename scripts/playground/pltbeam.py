import mitsuba as mi
import drjit as dr

# Bounce data contains all necessary info to rewind a path and
# compute forward coherence-aware wave transport via PLT 

import numpy as np
import matplotlib.pyplot as plt

# initialize variant
mi.set_variant("cuda_ad_spectral_polarized")

dir = mi.Vector3f(0.4, 0.3, 0.5)
dir /= dr.norm(dir)

beam = mi.PLTBeam3f.plt_source_beam_distant(
    dir,
    mi.Float(0.001),
    mi.UnpolarizedSpectrum(0.5),
    mi.UnpolarizedSpectrum(440),
    mi.Float(0.04),
    mi.Bool(False)
)

print(beam.coherence.dmat)