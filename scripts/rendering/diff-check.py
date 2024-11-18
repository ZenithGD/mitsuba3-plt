import argparse
import matplotlib.pyplot as plt
import imageio.v3 as iio
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

def main(args):
    img1 = read_exr(args.img1)
    img2 = read_exr(args.img2)

    fig, axes = plt.subplots(1, 3)

    axes[0].set_title("Image 1")
    axes[1].set_title("Image 2")
    axes[2].set_title("Difference")

    im0 = axes[0].imshow(np.clip(np.mean(img1, axis=2), 0, 1))
    im1 = axes[1].imshow(np.clip(np.mean(img2, axis=2), 0, 1))
    im2 = axes[2].imshow(np.clip(np.mean(img1 - img2, axis=2), 0, 1))

    fig.suptitle(f"RMSE = {np.sqrt(np.mean(np.square(img1 - img2)))}")

    fig.colorbar(im0, ax=axes[0], orientation='vertical')
    fig.colorbar(im1, ax=axes[1], orientation='vertical')
    fig.colorbar(im2, ax=axes[2], orientation='vertical')

    plt.show()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Show the difference between two images")
    parser.add_argument("img1", help="First image")
    parser.add_argument("img2", help="Second image")

    main(parser.parse_args())