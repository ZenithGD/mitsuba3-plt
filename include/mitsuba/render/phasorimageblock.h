#pragma once

#include <mitsuba/core/fwd.h>
#include <mitsuba/core/logger.h>
#include <mitsuba/core/object.h>
#include <mitsuba/core/vector.h>
#include <mitsuba/render/fwd.h>
#include <drjit/dynamic.h>
#include <drjit/tensor.h>

NAMESPACE_BEGIN(mitsuba)

template <typename Float, typename Spectrum>
class MI_EXPORT_LIB PhasorImageBlock : public Object {

    // Represent both the spectral amplitude and phase distribution.
    // No polarization state here
    using ComplexSpectrum = dr::Complex<UnpolarizedSpectrum>
    
    public:
        MI_IMPORT_TYPES(ReconstructionFilter)

        ~PhasorImageBlock();

        PhasorImageBlock(
            const ScalarVector2f& size,
            const ScalarPoint2i &offset,
            const uint32_t channel_count,
            const ReconstructionFilter *rfilter = nullptr,
            bool border = std::is_scalar_v<Float>,
            bool normalize = false,
            bool coalesce = dr::is_jit_v<Float>,
            bool compensate = false,
            bool warn_negative = std::is_scalar_v<Float>,
            bool warn_invalid = std::is_scalar_v<Float>);

        /// Clear the image block contents to zero.
        void clear();

        void put_block(const PhasorImageBlock *block);

        void put(
            const Point2f& pos,
            const Wavelength &wavelengths,
            const Spectrum &amplitude,
            const UnpolarizedSpectrum &phase,
            Float alpha = 1.f,
            Float weight = 1.f,
            Mask active = true) 
        {

            DRJIT_MARK_USED(wavelengths);

            // Create a phasor from amplitude and phase
            UnpolarizedSpectrum spec_u = unpolarized_spectrum(amplitude);
            ComplexSpectrum phasor(spec_u, phase);

            Color3f rgb;
            if constexpr (is_spectral_v<Spectrum>)
                rgb = spectrum_to_srgb(spec_u, wavelengths, active);
            else if constexpr (is_monochromatic_v<Spectrum>)
                rgb = spec_u.x();
            else
                rgb = spec_u;

            Float values[5] = { rgb.x(), rgb.y(), rgb.z(), 0, 0 };

            if (m_channel_count == 4) {
                values[3] = weight;
            } else if (m_channel_count == 5) {
                values[3] = alpha;
                values[4] = weight;
            } else {
                Throw("ImageBlock::put(): non-standard image block configuration! (AOVs?)");
            }

            put(pos, values, active);
        }
};

MI_EXTERN_CLASS(PhasorImageBlock)
NAMESPACE_END(mitsuba)