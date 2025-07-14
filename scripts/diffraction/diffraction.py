import mitsuba as mi
import drjit as dr
import time
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # Import required for 3D plotting

from matplotlib.widgets import Slider

from utils import *

# initialize variant
mi.set_variant("cuda_ad_rgb_polarized")

nlobesx = 9
nlobesy = 9
diff_times = []
int_times = []
wi = sph_to_dir(dr.deg2rad(45), 0.0)

def compute_metrics(periodx, periody, angle, h, wi, wl):
    global diff_times, int_times

    grtype = mi.DiffractionGratingType.Sinusoidal
    grating = mi.DiffractionGrating3f(
        angle, 
        mi.Vector2f(periodx, periody), 
        h, 15, grtype, 1, 
        mi.Vector2f(0.0))

    diffr_timer, intensity_timer = 0, 0

    # show diffraction directions w.r.t wavelength and lobe
    ldirs = np.zeros((nlobesx, nlobesy, 3))
    intensities = np.zeros((nlobesx, nlobesy))

    lobes_x = np.arange(nlobesx) - nlobesx // 2
    lobes_y = np.arange(nlobesy) - nlobesy // 2
    lobes_xv, lobes_yv = np.meshgrid(lobes_x, lobes_y)
    lobes_xv = lobes_xv.ravel()
    lobes_yv = lobes_yv.ravel()
    
    lobevec = mi.Vector2i(dr.cuda.Int(lobes_xv), dr.cuda.Int(lobes_yv))
        
    start = time.perf_counter_ns()
    ddiff, active = grating.diffract(
        wi, 
        lobevec, 
        wl)
    
    ddiff[~active] = mi.Vector3f(0.0)

    # print(np.array(lobevec))
    # ddiff = diffract_manual(wi, lobevec, wl, mi.Vector2f(periodx, periody))
    secs = time.perf_counter_ns() - start
    diffr_timer += secs
    
    start = time.perf_counter_ns()
    intensity = grating.lobe_intensity(lobevec, wi, wl)
    secs = time.perf_counter_ns() - start


    intensity_timer += secs

    ldirs = np.array(ddiff * intensity).T
    intensities = np.array(intensity).reshape(nlobesx, nlobesy)

    t_diff = diffr_timer*1e-3/(nlobesx * nlobesy)
    t_int = intensity_timer*1e-3/(nlobesx * nlobesy)
    print(f"avg time diffract = {t_diff:.5f} us.")
    print(f"avg time intensity = {t_int:.5f} us.")

    diff_times.append(t_diff)
    int_times.append(t_int)
    return ldirs, intensities

def plot_metrics(ax1, ax2, ldirs, intensities):
    ax1.set_title("Diffraction lobes (scaled)")
    ax2.set_title("Diffraction intensities")

    visualize_grating_3d(wi, ldirs, ax=ax1)

    visualize_lobe_intensity(intensities, ax=ax2, normalize=True)

# initial plot
fig = plt.figure()
ax1 = fig.add_subplot(1, 2, 1, projection='3d')
ax2 = fig.add_subplot(1, 2, 2)

# wavelength in micrometers
px = 0.4
py = 0.5
angle = 0
h = 0.05
wl = 0.4
ldirs, intensities = compute_metrics(
    periodx=px, 
    periody=py, 
    angle=angle, 
    h=h,
    wi=wi,
    wl=float(wl))

plot_metrics(ax1, ax2, ldirs, intensities)

axs1 = fig.add_axes([0.1, 0.06, 0.3, 0.05])

x_slider = Slider(
    ax=axs1,
    label='Inv period (X)',
    valmin=0.001,
    valmax=1,
    valinit=0.4,
)

axs2 = fig.add_axes([0.6, 0.06, 0.3, 0.05])

y_slider = Slider(
    ax=axs2,
    label='Inv period (Y)',
    valmin=0.001,
    valmax=1,
    valinit=0.4,
)

axs3 = fig.add_axes([0.1, 0.02, 0.3, 0.05])

h_slider = Slider(
    ax=axs3,
    label='Grating height',
    valmin=0.01,
    valmax=1.5,
    valinit=0.01,
)

axs4 = fig.add_axes([0.6, 0.02, 0.3, 0.05])

wl_slider = Slider(
    ax=axs4,
    label='Wavelength',
    valmin=0.1,
    valmax=1.5,
    valinit=0.4,
)

def update_px(val):
    global px, py, angle, wi, h, wl

    # clear previous plot
    ax1.cla()
    ax2.cla()

    px = float(val)
    
    ldirs, intensities = compute_metrics(
        periodx=float(val), 
        periody=py, 
        angle=angle, 
        h=h,
        wi=wi,
        wl=float(wl))

    plot_metrics(ax1, ax2, ldirs, intensities)


def update_py(val):
    global px, py, angle, wi, h, wl

    # clear previous plot
    ax1.cla()
    ax2.cla()

    py = float(val)
    
    ldirs, intensities = compute_metrics(
        periodx=px, 
        periody=float(val), 
        angle=angle, 
        h=h,
        wi=wi,
        wl=float(wl))

    plot_metrics(ax1, ax2, ldirs, intensities)


def update_h(val):
    global px, py, angle, wi, h, wl

    # clear previous plot
    ax1.cla()
    ax2.cla()

    h = float(val)
    
    ldirs, intensities = compute_metrics(
        periodx=px, 
        periody=py, 
        angle=angle, 
        h=float(val),
        wi=wi,
        wl=float(wl))

    plot_metrics(ax1, ax2, ldirs, intensities)

def update_wl(val):
    global px, py, angle, wi, h, wl

    # clear previous plot
    ax1.cla()
    ax2.cla()

    wl = float(val)

    ldirs, intensities = compute_metrics(
        periodx=px, 
        periody=py, 
        angle=angle, 
        h=h,
        wi=wi,
        wl=float(val))

    plot_metrics(ax1, ax2, ldirs, intensities)

x_slider.on_changed(update_px)
y_slider.on_changed(update_py)
h_slider.on_changed(update_h)
wl_slider.on_changed(update_wl)

plt.show()

print("done. ")
print(f"diff time: {np.mean(diff_times)} +- {np.std(diff_times)} us")
print(f"int time: {np.mean(int_times)} +- {np.std(int_times)} us")