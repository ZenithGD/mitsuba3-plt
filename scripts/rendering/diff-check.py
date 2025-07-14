import argparse
import matplotlib.pyplot as plt
import numpy as np

import OpenEXR
import Imath

from utils import *
import flip_evaluator as flip

def main(args):
    img1 = read_exr(args.img1)
    img2 = read_exr(args.img2)

    fig, axes = plt.subplots(1, 4)

    axes[0].set_title("Image 1")
    axes[1].set_title("Image 2")
    axes[2].set_title("Difference (clamped)")
    axes[3].set_title("FLIP image metric")

    # FLIP
    FLIP_err_map, mean_FLIP_error, parameters = flip.evaluate(img1, img2, "HDR")

    im0 = axes[0].imshow(np.mean(img1, axis=2), )#vmin=0, vmax=1)
    im1 = axes[1].imshow(np.mean(img2, axis=2), )#vmin=0, vmax=1)
    im2 = axes[2].imshow(np.mean(img1 - img2, axis=2), cmap='seismic')
    im3 = axes[3].imshow(FLIP_err_map, cmap='magma', vmin=0, vmax=1)

    fig.suptitle(f"RMSE = {np.sqrt(np.mean(np.square(np.mean(img1 - img2, axis=2))))}")

    fig.colorbar(im0, ax=axes[0], orientation='horizontal')
    fig.colorbar(im1, ax=axes[1], orientation='horizontal')
    fig.colorbar(im2, ax=axes[2], orientation='horizontal')
    fig.colorbar(im3, ax=axes[3], orientation='horizontal')

    for ax in axes:
        ax.axis('off')
    
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Show the difference between two images")
    parser.add_argument("img1", help="First image")
    parser.add_argument("img2", help="Second image")

    main(parser.parse_args())