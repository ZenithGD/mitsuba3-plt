import matplotlib.pyplot as plt
import mitsuba as mi
import drjit as dr
import numpy as np

def plot_spectra(ax, wavelengths, intensities, **kwargs):

    if ax is None:
        fig, ax = plt.subplots()

    #colours = np.array(mi.xyz_to_srgb(mi.cie1931_xyz(wavelengths)))

    ax.plot(wavelengths, intensities, **kwargs)

