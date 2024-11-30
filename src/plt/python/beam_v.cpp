#include <drjit/python.h>
#include <mitsuba/plt/beam.h>
#include <mitsuba/plt/fwd.h>
#include <mitsuba/python/python.h>
#include <mitsuba/render/bsdf.h>

MI_PY_EXPORT(PLTBeam) {

    MI_PY_IMPORT_TYPES()
    MI_IMPORT_CORE_TYPES()
    MI_IMPORT_PLT_BASIC_TYPES()

    auto it =
        nb::class_<PLTBeam3f>(m, "PLTBeam3f", D(PLTBeam))
            .def_field(PLTBeam3f, sp, "sp")
            .def_field(PLTBeam3f, origin, "origin")
            .def_field(PLTBeam3f, dir, "dir")
            .def_field(PLTBeam3f, tangent, "tangent")
            .def_field(PLTBeam3f, distant, "distant")
            .def_field(PLTBeam3f, coherence, "coherence")
            .def_field(PLTBeam3f, active, "active")

            .def(nb::init<Spectrum, Matrix2f, Vector3f, Vector3f, Vector3f,
                          Mask, Mask>(),
                 "sp"_a, "diff"_a, "origin"_a, "dir"_a, "tangent"_a,
                 "distant"_a, "active"_a, D(PLTBeam, PLTBeam))
            .def("scale_sp", nb::overload_cast<Float>(&PLTBeam3f::scale_sp),
                 "s"_a, D(PLTBeam, scale_sp))
            .def("scale_sp",
                 nb::overload_cast<UnpolarizedSpectrum>(&PLTBeam3f::scale_sp),
                 "s"_a, D(PLTBeam, scale_sp, 2))
            .def("transverse_rotation", &PLTBeam3f::transverse_rotation,
                 D(PLTBeam, transverse_rotation))
            .def("inv_coherence",
                 nb::overload_cast<Float>(&PLTBeam3f::inv_coherence), "k"_a,
                 D(PLTBeam, inv_coherence))
            .def("inv_coherence",
                 nb::overload_cast<>(&PLTBeam3f::inv_coherence),
                 D(PLTBeam, inv_coherence, 2))
            .def("mutual_coherence",
                 nb::overload_cast<const Wavelength&, const Vector3f&>(
                     &PLTBeam3f::mutual_coherence), "kw"_a,
                 "diff"_a, D(PLTBeam, mutual_coherence))
            .def("mutual_coherence",
                 nb::overload_cast<const Float&, const Vector3f&>(
                     &PLTBeam3f::mutual_coherence), "k"_a,
                 "diff"_a, D(PLTBeam, mutual_coherence, 2))
            .def("mutual_coherence_angular",
                     &PLTBeam3f::mutual_coherence_angular, "d1"_a, "d2"_a, D(PLTBeam, mutual_coherence_angular))
            .def("transform_coherence", &PLTBeam3f::transform_coherence, "U"_a,
                 D(PLTBeam, transform_coherence))
            .def("rotate_frame", &PLTBeam3f::rotate_frame, "new_tangent"_a,
                 D(PLTBeam, rotate_frame))
            .def("create_local_frame", &PLTBeam3f::create_local_frame, "new_wo"_a,
                 D(PLTBeam, create_local_frame))
            .def("propagate", &PLTBeam3f::propagate, "p"_a,
                 D(PLTBeam, propagate));
    // .def_repr(PLTBeam3f);

    MI_PY_DRJIT_STRUCT(it, PLTBeam3f, sp, origin, dir, tangent, distant, active, coherence)
}
