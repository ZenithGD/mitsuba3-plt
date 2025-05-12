import argparse

import scipy.special as sp
import matplotlib.pyplot as plt
import pandas as pd

import numpy as np
import mitsuba as mi
import drjit as dr
import time

def main(args):

    X = np.meshgrid(np.arange(args.sx))
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generates a texture where channels correspond to the grating angle")
    parser.add_argument("outfile", type=str, help="The output texture")
    
    parser.add_argument("--sizex", "-sx", type=float, help="Width of the texture", default=256)
    parser.add_argument("--sizey", "-sy", type=float, help="Height of the texture", default=256)

    parser.add_argument("--centerx", "-cx", type=float, help="UV U coordinate of the center in (0,1)")
    parser.add_argument("--centery", "-cy", type=float, help="UV V coordinate of the center in (0,1)")

    args = parser.parse_args()
    main(args)

