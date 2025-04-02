#include <drjit/python.h>
#include <nanobind/stl/pair.h>
#include <mitsuba/python/python.h>
#include <mitsuba/plt/fwd.h>
#include <mitsuba/plt/sample_solve.h>

MI_PY_EXPORT(SampleSolve)
{
    MI_PY_IMPORT_TYPES()
    MI_IMPORT_PLT_BASIC_TYPES()
    MI_IMPORT_CORE_TYPES()

    nb::class_<PLTSamplePhaseData3f>(m, "PLTSamplePhaseData3f", D(PLTSamplePhaseData3f))
        .def_field(PLTSamplePhaseData3f, bsdf_sample, "bsdf_sample")
        .def_field(PLTSamplePhaseData3f, diffraction_lobe, "diffraction_lobe")
        .def_field(PLTSamplePhaseData3f, sampling_wavelengths, "sampling_wavelengths")
        .def(nb::init<BSDFSample3f, Vector2i, Wavelength>());
}