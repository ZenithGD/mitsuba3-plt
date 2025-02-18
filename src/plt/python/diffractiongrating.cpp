#include <mitsuba/plt/diffractiongrating.h>
#include <mitsuba/python/python.h>

MI_PY_EXPORT(DiffractionGratingType) {
    auto e = nb::enum_<DiffractionGratingType>(m, "DiffractionGratingType",
            nb::is_arithmetic(), D(DiffractionGratingType))
        .def_value(DiffractionGratingType, Sinusoidal)
        .def_value(DiffractionGratingType, Rectangular)
        .def_value(DiffractionGratingType, Linear)
        .def_value(DiffractionGratingType, Radial);
}