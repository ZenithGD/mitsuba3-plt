#include <drjit/python.h>
#include <nanobind/stl/pair.h>
#include <mitsuba/python/python.h>
#include <mitsuba/plt/fwd.h>
#include <mitsuba/plt/diffractiongrating.h>

MI_PY_EXPORT(DiffractionGrating) {
    
    MI_PY_IMPORT_TYPES()
    MI_IMPORT_PLT_BASIC_TYPES()
    MI_IMPORT_CORE_TYPES()

    nb::class_<DiffractionGrating3f>(m, "DiffractionGrating3f",
                                   D(DiffractionGrating))
        .def(nb::init<Float, const Vector2f &, Float, uint32_t,
                      DiffractionGratingType, Float, Vector2f>(),
             "grating_angle"_a, "inv_period"_a, "q"_a, "lobes"_a, "type"_a,
             "multiplier"_a, "uv"_a, D(DiffractionGrating, DiffractionGrating))
        .def("is_1D_grating", &DiffractionGrating3f::is_1D_grating,
             D(DiffractionGrating, is_1D_grating))
        .def("alpha", &DiffractionGrating3f::alpha, "wi"_a, "k"_a,
             D(DiffractionGrating, alpha))
        .def("sample_lobe", &DiffractionGrating3f::sample_lobe, "sample2"_a,
             "wi"_a, "wl"_a, D(DiffractionGrating, sample_lobe))
        .def("diffract", &DiffractionGrating3f::diffract, "wi"_a, "lobe"_a,
             "wl"_a, D(DiffractionGrating, diffract))
        .def("lobe_intensity", &DiffractionGrating3f::lobe_intensity, "lobe"_a,
             "wi"_a, "wl"_a, D(DiffractionGrating, lobe_intensity));
}