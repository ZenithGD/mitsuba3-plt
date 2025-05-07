import drjit as dr
import mitsuba as mi
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # Import required for 3D plotting


def sph_to_dir(theta, phi):
    """Map spherical to Euclidean coordinates"""
    st, ct = dr.sincos(theta)
    sp, cp = dr.sincos(phi)
    return mi.Vector3f(cp * st, sp * st, ct)

def visualize_grating_3d(wi, ldirs, ax=None):
    """Visualize a diffraction grating

    Args:
        wi (mi.Vector3f): The incident direction
        ldirs (np.array): The set of diffracted directions (n * 3)
        ax (axis, optional): An optional axis object to plot. Defaults to None.
    """

    if ax is None:
        fig, ax = plt.subplots()

    # plot incident direction wi (from camera)
    ax.quiver(0, 0, 0, wi[0], wi[1], wi[2], color="r")
    ax.set_xlim3d(-1, 1)
    ax.set_ylim3d(-1, 1)
    ax.set_zlim3d(-1, 1)

    zs = np.zeros(ldirs.shape[0])
    ax.quiver(zs, zs, zs, 
            np.ravel(ldirs[:, 0]),
            np.ravel(ldirs[:, 1]),
            np.ravel(ldirs[:, 2]))
    ax.set_xlabel('X axis')
    ax.set_ylabel('Y axis')
    ax.set_zlabel('Z axis')
    return ax

def visualize_lobe_intensity(intensities, ax=None, normalize=False):
    """Visualize the intensity of each diffraction lobe.

    Args:
        wi (mi.Vector3f): The incident direction
        ldirs (np.array): The set of diffracted directions (nx * ny * 3)
        ax (axis, optional): An optional axis object to plot. Defaults to None.
    """

    if ax is None:
        fig, ax = plt.subplots()

    nlobesx = intensities.shape[0]
    nlobesy = intensities.shape[1]

    it = intensities
    if normalize:
        print(f"Normalizing grid by 1/{np.sum(it):2f}")
        it = it / np.sum(it)

    # show diffraction efficiencies
    im = ax.imshow(it)
    lx = np.arange(nlobesx) - nlobesx // 2
    ly = np.arange(nlobesy) - nlobesy // 2
    # Show all ticks and label them with the respective list entries
    ax.set_xticks(np.arange(len(lx)), labels=lx)
    ax.set_yticks(np.arange(len(ly)), labels=ly)
    # Loop over data dimensions and create text annotations.
    for i in range(len(lx)):
        for j in range(len(ly)):
            text = ax.text(j, i, f"{it[i, j]:.3f}",
                        ha="center", va="center", color="w")

    return ax