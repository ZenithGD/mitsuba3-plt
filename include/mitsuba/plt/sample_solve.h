#pragma once
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
     * diffraction grating, this will contain a 0-vector.
     */
    Vector2i diffraction_lobe;

    /**
     * @brief The direction of the center lobe of a diffractive interaction. 
     * If the interaction didn't involve a diffraction grating, 
     * this will contain a 0-vector. This is required for the rough grating.
     */
    Vector3f center_lobe;

    /**
     * @brief Wavelength(s) driving the sampling process.
     * First wavelength is assumed to be the hero wavelength
     */
    Wavelength sampling_wavelengths;

    // add more data here if needed...

    PLTSamplePhaseData(const BSDFSample3f &sp, const Vector2i& lobe, 
        const Vector3f& clobe, const Wavelength& wl)
        : bsdf_sample(sp), diffraction_lobe(lobe), center_lobe(clobe), sampling_wavelengths(wl)
    {}

    DRJIT_STRUCT(PLTSamplePhaseData, bsdf_sample, diffraction_lobe, center_lobe, sampling_wavelengths)
};

NAMESPACE_END(mitsuba)
