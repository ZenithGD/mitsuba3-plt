
import argparse
import matplotlib.pyplot as plt
import numpy as np

import OpenEXR
import Imath
import numpy as np

def read_exr(filename):
    # Open the EXR file
    exr_file = OpenEXR.InputFile(filename)

    # Get the header to extract channel information
    header = exr_file.header()
    dw = header['dataWindow']
    size = (dw.max.x - dw.min.x + 1, dw.max.y - dw.min.y + 1)

    # Assume EXR contains RGB channels
    channels = ['R', 'G', 'B']
    dtype = Imath.PixelType(Imath.PixelType.FLOAT)  # Use FLOAT for actual pixel values

    # Read each channel and stack into a single array
    data = [np.frombuffer(exr_file.channel(c, dtype), dtype=np.float32).reshape(size[1], size[0]) for c in channels]
    return np.stack(data, axis=-1)  # Combine into HxWxC format