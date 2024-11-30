#include <mitsuba/python/python.h>
#include <mitsuba/plt/plt.h>
#include <mitsuba/plt/fwd.h>
#include <drjit/python.h>

MI_PY_EXPORT(Coherence) {
    MI_PY_IMPORT_TYPES()
    MI_IMPORT_PLT_BASIC_TYPES()
    MI_IMPORT_CORE_TYPES()
    
    auto it = nb::class_<Coherence3f>(m, "Coherence3f", D(Coherence))
        // Members
        .def_field(Coherence3f, dmat, D(Coherence, dmat))
        .def_field(Coherence3f, opl, D(Coherence, opl))

        // Methods
        .def(nb::init<>(), D(Coherence, Coherence))
        .def(nb::init<const Coherence3f &>(), "Copy constructor")
        .def(nb::init<Float, Float>(),
             "diffusivity"_a, "l"_a,
             D(Coherence, Coherence, 2))
        .def(nb::init<Float, Float>(),
             "diffm"_a, "l"_a,
             D(Coherence, Coherence, 3))
        .def("rmm", &Coherence3f::rmm, D(Coherence, rmm))
        .def("propagate", &Coherence3f::propagate, "rd"_a, "mask"_a, "Propagate")
        .def("inv_coherence_matrix",nb::overload_cast<Float>(&Coherence3f::inv_coherence_matrix, nb::const_), 
            "k"_a, D(Coherence, inv_coherence_matrix))
        .def("inv_coherence_matrix",nb::overload_cast<>(&Coherence3f::inv_coherence_matrix, nb::const_), 
            D(Coherence, inv_coherence_matrix, 2))
        .def("inv_coherence_det",nb::overload_cast<Float>(&Coherence3f::inv_coherence_det, nb::const_), 
            "k"_a, D(Coherence, inv_coherence_det))
        .def("inv_coherence_det",nb::overload_cast<>(&Coherence3f::inv_coherence_det, nb::const_), 
            D(Coherence, inv_coherence_det, 2))
        .def("transform", &Coherence3f::transform, "mat"_a, "mask"_a = true, D(Coherence, transform))
        .def_repr(Coherence3f);

    MI_PY_DRJIT_STRUCT(it, Coherence3f, dmat, opl)
}

MI_PY_EXPORT(GeneralizedRadiance) {
    MI_PY_IMPORT_TYPES()
    MI_IMPORT_PLT_BASIC_TYPES()
    MI_IMPORT_CORE_TYPES()

    auto it = nb::class_<GeneralizedRadiance3f>(m, "GeneralizedRadiance3f", D(GeneralizedRadiance))
        // Members
        .def_field(GeneralizedRadiance3f, L, D(GeneralizedRadiance, L))
        .def_field(GeneralizedRadiance3f, L1, D(GeneralizedRadiance, L1))
        .def_field(GeneralizedRadiance3f, L2, D(GeneralizedRadiance, L2))
        .def_field(GeneralizedRadiance3f, L3, D(GeneralizedRadiance, L3))
        .def_field(GeneralizedRadiance3f, coherence, D(GeneralizedRadiance, coherence))
        // Methods
        .def(nb::init<>(), D(GeneralizedRadiance, GeneralizedRadiance))
        .def(nb::init<const GeneralizedRadiance3f &>(), "Copy constructor")
        .def(nb::init<Spectrum>(),
             "L_"_a, D(GeneralizedRadiance, GeneralizedRadiance, 2))
        .def_repr(GeneralizedRadiance3f);

    MI_PY_DRJIT_STRUCT(it, GeneralizedRadiance3f, L, L1, L2, L3, coherence)
}

MI_PY_EXPORT(PLTInteraction){
    MI_PY_IMPORT_TYPES()
    MI_IMPORT_PLT_BASIC_TYPES()
MI_IMPORT_CORE_TYPES()

    auto it = nb::class_<PLTInteraction3f>(m, "PLTInteraction3f", D(PLTInteraction))
        // Members
        .def_field(PLTInteraction3f, sp_coherence, D(PLTInteraction, sp_coherence))
        .def_field(PLTInteraction3f, t, D(PLTInteraction, t))
        // Methods
        .def(nb::init<>(), D(PLTInteraction, PLTInteraction))
        .def(nb::init<const PLTInteraction3f &>(), "Copy constructor")
        .def_repr(PLTInteraction3f);

    MI_PY_DRJIT_STRUCT(it, PLTInteraction3f, sp_coherence, t)
}