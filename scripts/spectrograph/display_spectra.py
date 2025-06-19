import mitsuba as mi
import drjit as dr

import argparse

import numpy as np
import matplotlib.pyplot as plt

def main(args):
    
    fig, ax = plt.subplots(args.amount)

    for i, ax in enumerate(ax):
        ax[i].imshow()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Display spectra in a stacked image")
    parser.add_argument("indir", help="The input folder with all the results")
    parser.add_argument("--amount", help="The amount of spectra to display")

    main(parser.parse_args())