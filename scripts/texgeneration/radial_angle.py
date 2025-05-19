import argparse

import scipy.special as sp
import matplotlib.pyplot as plt
import numpy as np
import mitsuba as mi
import drjit as dr
import time

mi.set_variant("cuda_ad_rgb_polarized")

def main(args):

    X, Y = np.meshgrid(np.arange(args.sizex), np.arange(args.sizey))

    rx = X - args.centerx
    ry = Y - args.centery

    angle = np.atan2(ry, rx)
    # limit to 0...1 range
    angle = (angle + np.pi) / (2.0 * np.pi)

    bitmap = mi.Bitmap(array=angle, pixel_format=mi.Bitmap.PixelFormat.Y)
    mi.util.write_bitmap(args.outfile, bitmap)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generates a texture where channels correspond to the grating angle")
    parser.add_argument("outfile", type=str, help="The output texture")
    
    parser.add_argument("--sizex", "-sx", type=float, help="Width of the texture", default=256)
    parser.add_argument("--sizey", "-sy", type=float, help="Height of the texture", default=256)

    parser.add_argument("--centerx", "-cx", type=float, help="UV U coordinate of the center in (0,1)")
    parser.add_argument("--centery", "-cy", type=float, help="UV V coordinate of the center in (0,1)")

    args = parser.parse_args()
    main(args)

