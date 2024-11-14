import tkinter as tk
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

import mitsuba as mi
import drjit as dr

mi.set_variant("cuda_ad_rgb")

import argparse

from gui import MitsubaViewer

def main(args):
    
    app = ttkb.Window()
    style = ttkb.Style("darkly")
    app.title("Mitsuba 3 viewer tool")

    gui = MitsubaViewer(app)
    gui.display()

    app.mainloop()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Mitsuba GUI viewer and helper tool.")
    args = parser.parse_args()
    main(args)