from threading import Thread

import pytest

import mitsuba as mi
import drjit as dr

def test01_phasor_film_create():
    
    phasor_film = {
        'type': 'phasorfilm',
        'width': 1920,
        'height': 1080
    }