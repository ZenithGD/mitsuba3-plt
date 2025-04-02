#include <mitsuba/render/fwd.h>
#include <mitsuba/plt/fwd.h>
#include <mitsuba/plt/plt.h>
#include <mitsuba/render/bsdf.h>

NAMESPACE_BEGIN(mitsuba)

template <typename Float_, typename Spectrum_>
struct PLTSamplePhaseData
{
    using Float = Float_;
    using Spectrum = Spectrum_;

    MI_IMPORT_TYPES()
    MI_IMPORT_OBJECT_TYPES()
    MI_IMPORT_PLT_BASIC_TYPES()
    
    /// @brief The sample object generated in the sample stage
    BSDFSample3f bsdf_sample;

    /**
     * @brief The diffraction lobe. If the interaction didn't involve a 
     * diffraction grating, this will contain a 0-vector.w
     */
    Vector2i diffraction_lobe;

    /**
     * @brief Wavelength(s) driving the sampling process.
     * First wavelength is assumed to be the hero wavelength
     */
    Wavelength sampling_wavelengths;

    // add more data here if needed...
};

NAMESPACE_END(mitsuba)
