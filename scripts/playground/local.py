
import drjit as dr
import mitsuba as mi

# initialize variant
mi.set_variant("cuda_ad_rgb")

# A function returning results in the range 0..9
def f(i: mi.UInt32) -> mi.UInt32:
    return (i * 16) % 10

@dr.syntax
def g(n: mi.UInt32):
    # Create zero-initialized buffer of type 'drjit.Local[mi.UInt32]'
    hist = dr.alloc_local(mi.UInt32, 10, value=dr.zeros(mi.UInt32))

    # Fill histogram
    i = mi.UInt32(0)
    while i < n:        # <-- symbolic loop
        hist[f(i)] += 1 # <-- read+write with computed index
        i += 1

    # Get the largest histogram entry
    i, maxval = mi.UInt32(0), mi.UInt32(0)
    while i < 10:
        maxval = dr.maximum(maxval, hist[i])
        i += 1
    return maxval

print(g(100))