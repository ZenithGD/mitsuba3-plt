#pragma once

#include <mitsuba/core/fwd.h>
// #include <mitsuba/core/spectrum.h>
#include <mitsuba/core/traits.h>

NAMESPACE_BEGIN(mitsuba)

template <typename Float, typename Spectrum> struct PLTInteraction;
template <typename Float, typename Spectrum> struct GeneralizedRadiance;
template <typename Float, typename Spectrum> class Coherence;
template <typename Float, typename Spectrum> class DiffractionGrating;
template <typename Float, typename Spectrum> struct BounceData;
template <typename Float, typename Spectrum> struct PLTBeam;
template <typename Float, typename Spectrum> struct PLTSamplePhaseData;

template <typename Float_, typename Spectrum_> struct PLTAliases {
    using Float                     = Float_;
    using Spectrum                  = Spectrum_;

    using PLTInteraction3f      = PLTInteraction<Float, Spectrum>;
    using Coherence3f           = Coherence<Float, Spectrum>;
    using GeneralizedRadiance3f = GeneralizedRadiance<Float, Spectrum>;
    using DiffractionGrating3f  = DiffractionGrating<Float, Spectrum>;
    using BounceData3f          = BounceData<Float, Spectrum>;
    using PLTBeam3f             = PLTBeam<Float, Spectrum>;
    using PLTSamplePhaseData3f  = PLTSamplePhaseData<Float, Spectrum>;
};

#define MI_IMPORT_PLT_BASIC_TYPES()                                            \
    using PLTAliases            = mitsuba::PLTAliases<Float, Spectrum>;        \
    using Coherence3f           = typename PLTAliases::Coherence3f;            \
    using GeneralizedRadiance3f = typename PLTAliases::GeneralizedRadiance3f;  \
    using PLTInteraction3f      = typename PLTAliases::PLTInteraction3f;       \
    using DiffractionGrating3f  = typename PLTAliases::DiffractionGrating3f;   \
    using BounceData3f          = typename PLTAliases::BounceData3f;           \
    using PLTBeam3f             = typename PLTAliases::PLTBeam3f;              \
    using PLTSamplePhaseData3f  = typename PLTAliases::PLTSamplePhaseData3f;        
            

#define MI_IMPORT_PLT_TYPES_MACRO(x) using x = typename PLTAliases::x;

#define MI_IMPORT_PLT_TYPES(...)                         \
    MI_IMPORT_PLT_BASIC_TYPES()                          \
    DRJIT_MAP(MI_IMPORT_PLT_TYPES_MACRO, __VA_ARGS__)


NAMESPACE_END(mitsuba)