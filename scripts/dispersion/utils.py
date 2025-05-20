import drjit as dr
import mitsuba as mi

import numpy as np
import matplotlib.pyplot as plt

from scripts.utils import sph_to_dir

def plot_dispersion(angles, values, show_360=False, show_sp=False, **kwargs):
    
    if show_sp:
        values_np = np.array(values)
    else:
        values_np = np.array(mi.unpolarized_spectrum(values))

    print(values_np.shape)
    if values_np.shape[-1] == 1:
        # collapsed dimension, repeat for all angles
        values_np = np.repeat(values_np, angles.shape[0], axis=-1)

    angles_np = np.array(angles)

    if show_sp:
        # Plot values for spherical coordinates (upper hemisphere)
        fig, axs = plt.subplots(1, 4, figsize=(8, 4), subplot_kw={'projection': 'polar'})

        # for each stokes parameter create dispersion plot
        for i, ax in enumerate(axs):
            ax.set_thetamin(-180 if show_360 else -90)
            ax.set_thetamax(180 if show_360 else 90)
            ax.set_theta_offset(np.pi / 2.0)
            ax.set_rlim(0, np.max(np.where(np.isnan(values_np[i]), 0.5, values_np[i])) * 1.2)

            # Extract channels of BRDF values
            values_r = values_np[i, 0, 0]
            values_g = values_np[i, 0, 1]
            values_b = values_np[i, 0, 2]
                
            # plot red, green, blue separately
            ax.plot(angles_np, values_r, '-r')
            ax.plot(angles_np, values_g, '-g')
            ax.plot(angles_np, values_b, '-b')

            if kwargs["title"]:
                ax.set_title(f"S{i}")

        if kwargs["title"]:
            fig.suptitle(kwargs['title'])
    else:

        # Extract channels of BRDF values
        values_r = values_np[0]
        values_g = values_np[1]
        values_b = values_np[2]

        # Plot values for spherical coordinates (upper hemisphere)
        fig, ax = plt.subplots(figsize=(8, 4), subplot_kw={'projection': 'polar'})
        ax.set_thetamin(-180 if show_360 else -90)
        ax.set_thetamax(180 if show_360 else 90)
        ax.set_theta_offset(np.pi / 2.0)
        ax.set_rlim(0, np.max(values_np) + 0.2)

        # plot red, green, blue separately
        ax.plot(angles_np, values_r, '-r')
        ax.plot(angles_np, values_g, '-g')
        ax.plot(angles_np, values_b, '-b')

        if kwargs["title"]:
            fig.suptitle(kwargs['title'])