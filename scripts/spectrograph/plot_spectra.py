import matplotlib.pyplot as plt
import mitsuba as mi
import drjit as dr
import numpy as np

def plot_spectra(wavelengths, intensities):

    fig, ax = plt.subplots()

    #colours = np.array(mi.xyz_to_srgb(mi.cie1931_xyz(wavelengths)))

    ax.plot(wavelengths, intensities)
    ax.set_ylim(0, np.max(intensities) * 1.1)
    plt.show()
