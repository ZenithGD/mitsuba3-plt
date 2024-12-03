import mitsuba as mi
import drjit as dr

import numpy as np

def stokes_to_bitmaps(bitmap : mi.Bitmap):
    """Generate a bitmap for each one of the stokes components

    Args:
        bitmap (mi.Bitmap): The bitmap containing all stokes parameters

    Returns:
        tuple: A bitmap for each stokes parameter (s0, s1, s2, s3)
    """

    val = np.array(bitmap, copy=False)

    print(val.shape)

    L  = val[:,:,3]
    s0 = val[:,:,3:6]
    s1 = val[:,:,6:9]
    s2 = val[:,:,9:12]
    s3 = val[:,:,12:15]

    L_b  = mi.Bitmap(L).convert(srgb_gamma=True)
    s0_b = mi.Bitmap(s0)
    s1_b = mi.Bitmap(s1)
    s2_b = mi.Bitmap(s2)
    s3_b = mi.Bitmap(s3)

    return L_b, (s0_b, s1_b, s2_b, s3_b)

def plot_stokes_component(ax, image):
    # Convert the image into a TensorXf for manipulation
    data = mi.TensorXf(image)[:, :, 0]
    plot_minmax = 0.05 * max(dr.max(data, axis=None), dr.max(-data, axis=None)).array[0] # Arbitrary scale for colormap
    img = ax.imshow(data, cmap='coolwarm', vmin=-plot_minmax, vmax=+plot_minmax)
    ax.set_xticks([]); ax.set_yticks([])
    return img

def spec_fma(a, b, c):
    if mi.is_polarized:
        return a * b + c
    else:
        return dr.fmadd(a, b, c)
    
def spec_prod(a, b):
    if mi.is_polarized:
        return a * b
    else:
        return dr.mul(a, b)
    
def spec_add(a, b):
    if mi.is_polarized:
        return a + b
    else:
        return dr.add(a, b)