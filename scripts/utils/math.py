import drjit as dr
import mitsuba as mi

def sph_to_dir(theta, phi):
    """Map spherical to Euclidean coordinates"""
    st, ct = dr.sincos(theta)
    sp, cp = dr.sincos(phi)

    return mi.Vector3f(cp * st, sp * st, ct)

def dir_to_sph(v):
    theta = dr.atan2(v.y, v.x)
    phi = dr.acos(v.z / dr.norm(v))
    return theta, phi

def scalar_sph_to_dir(theta, phi):
    """Map spherical to Euclidean coordinates"""
    st, ct = dr.sincos(theta)
    sp, cp = dr.sincos(phi)

    return mi.ScalarVector3f(cp * st, sp * st, ct)
