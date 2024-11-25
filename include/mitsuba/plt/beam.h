#include <mitsuba/core/vector.h>
#include <mitsuba/core/math.h>
#include <mitsuba/core/spectrum.h>

#include <mitsuba/render/fwd.h>

#include <mitsuba/plt/fwd.h>
#include <mitsuba/plt/plt.h>

NAMESPACE_BEGIN(mitsuba)

template <typename Float_, typename Spectrum_>
struct PLTBeam {
    using Float    = Float_;
    using Spectrum = Spectrum_;

    MI_IMPORT_TYPES()
    MI_IMPORT_OBJECT_TYPES()
    MI_IMPORT_PLT_BASIC_TYPES()

    /// @brief Stokes parameters (only in polarized modes!)
    Spectrum sp;

    /// @brief The origin of the ray
    Vector3f origin;

    /// @brief The direction of forward propagation of this beam.
    Vector3f dir;

    /// @brief The direction of horizontal linear propagation
    Vector3f t;

    /// @brief Whether this beam comes from a distant interaction, for
    ///        example, from an environment map or far-field interaction
    Mask distant;
};

NAMESPACE_END(mitsuba)