#include <mitsuba/python/python.h>
#include <mitsuba/plt/fwd.h>
#include <mitsuba/plt/bouncebuffer.h>
#include <mitsuba/render/bsdf.h>
#include <drjit/python.h>

MI_PY_EXPORT(BounceData) {
    
    MI_PY_IMPORT_TYPES()
    MI_IMPORT_CORE_TYPES()
    MI_IMPORT_PLT_BASIC_TYPES()

    auto it =
        nb::class_<BounceData3f>(m, "BounceData3f", D(BounceData))
            .def_field(BounceData3f, id, "id")
            .def_field(BounceData3f, interaction, "interaction")
            .def_field(BounceData3f, wi, "wi")
            .def_field(BounceData3f, wo, "wo")
            .def_field(BounceData3f, bsdf_flags, "bsdf_flags")
            .def_field(BounceData3f, rr_thp, "id")
            .def_field(BounceData3f, throughput, "throughput")
            .def_field(BounceData3f, bsdf_weight, "bsdf_weight")
            .def_field(BounceData3f, last_nd_pdf, "last_nd_pdf")
            .def_field(BounceData3f, active, "active")
            .def_field(BounceData3f, is_emitter, "is_emitter")

            .def(nb::init<UInt32, SurfaceInteraction3f, Vector3f, Vector3f, UInt32,
                          Float, Spectrum, Spectrum, Mask, Float, Mask>(),
                 "id"_a, "interaction"_a, "wi"_a, "wo"_a, "bsdf_flags"_a,
                 "rr_thp"_a, "throughput"_a, "bsdf_weight"_a, "is_emitter"_a,
                 "last_nd_pdf"_a, "active"_a, D(BounceData, BounceData));
            // .def_repr(BounceData3f);

    MI_PY_DRJIT_STRUCT(it, BounceData3f, id, interaction, wi, wo, bsdf_flags, 
        rr_thp, throughput, bsdf_weight, is_emitter, last_nd_pdf, active)
}

MI_PY_EXPORT(BounceBuffer) {
    
    MI_PY_IMPORT_TYPES()
    MI_IMPORT_PLT_BASIC_TYPES()

    nb::class_<BounceBuffer3f>(m, "BounceBuffer", D(BounceBuffer))
        .def(nb::init<>(), D(BounceBuffer, BounceBuffer));
    // .def("read_last_bounce", &BounceBuffer3f::read_last_bounce,
    //      D(BounceBuffer, read_last_bounce))
    // .def("pop_bounce", &BounceBuffer3f::pop_bounce,
    //      D(BounceBuffer, pop_bounce))
    // .def("push_bounce", &BounceBuffer3f::push_bounce,
    //      "it"_a, "wi"_a, "bsdf_flags"_a, "contrib"_a, "ndpdf"_a, "active"_a,
    //      D(BounceBuffer, push_bounce));
}