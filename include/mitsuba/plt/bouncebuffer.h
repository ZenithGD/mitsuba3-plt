#pragma once

#include <mitsuba/core/fwd.h>
#include <mitsuba/core/vector.h>
#include <mitsuba/core/ray.h>
#include <mitsuba/core/bsphere.h>

#include <mitsuba/render/fwd.h>
#include <mitsuba/render/bsdf.h>
#include <mitsuba/render/interaction.h>

NAMESPACE_BEGIN(mitsuba)


/**
 * \brief Structure that stores one bounce of some path traversing the scene.
 * 
 * A bounce data object contains all the necessary information to compute both forwards and backwards light transport.
 */
template <typename Float_, typename Spectrum_>
struct BounceData {
    using Float    = Float_;
    using Spectrum = Spectrum_;
    
    MI_IMPORT_TYPES()
    MI_IMPORT_OBJECT_TYPES()

    /// \brief The id of the vertex in the path (mainly for debug purposes)
    UInt32 id;

    /// \brief Information about the interaction at this vertex
    SurfaceInteraction3f interaction;

    /// \brief The incident and outgoing direction, from the camera's perspective
    Vector3f wi, wo;

    /// \brief Information about the type of interaction. This is a vectorized array
    ///        of BSDFFlags. Use has_flag(...) to query the information.
    UInt32 bsdf_flags;

    /// \brief The factor due to russian roulette early path termination.
    Float rr_thp;

    /// \brief The throughput of the path sampled from the camera up to this vertex.
    Spectrum throughput;

    /// \brief The weight of the sample used to get a new path direction.
    Spectrum bsdf_weight;

    /// \brief Whether this vertex is on an emitter.
    Mask is_emitter;

    /// \brief The PDF of the last non-delta interaction (otherwise would be 0, check the `bsdf_flags` field first!)
    Float last_nd_pdf;
    
    /// \brief Whether this vertex of the path belongs to an active path.
    Mask active;
    
    BounceData(
        const UInt32 id_,
        const SurfaceInteraction3f& it_, 
        const Vector3f& wi_, const Vector3f& wo_, const UInt32& bf_,
        const Float& rr_thp_, const Spectrum& throughput_, 
        const Spectrum& bsdf_weight_, const Mask& is_emitter_, 
        const Float& ld_, const Mask& active_)

        : id(id_),
          interaction(it_), 
          wi(wi_), wo(wo_),
          bsdf_flags(bf_), 
          rr_thp(rr_thp_),
          throughput(throughput_),
          bsdf_weight(bsdf_weight_),
          is_emitter(is_emitter_),
          last_nd_pdf(ld_), 
          active(active_) {}

    DRJIT_STRUCT(BounceData, id, interaction, wi, wo, 
        bsdf_flags, rr_thp, throughput, bsdf_weight, 
        is_emitter, last_nd_pdf, active);
};

template <typename Float, typename Spectrum>
extern std::ostream &operator<<(std::ostream &os,
    const BounceData<Float, Spectrum>& bd);

template <typename Float, typename Spectrum>
std::ostream &operator<<(std::ostream &os, const BounceData<Float, Spectrum>& bd) {
    os << "BounceData[" << std::endl
       << "  id = " << string::indent(bd.id) << "," << std::endl
       << "  wi = " << string::indent(bd.wi) << "," << std::endl
       << "  wo = " << string::indent(bd.wo) << "," << std::endl
       << "  bsdf_flags = " << string::indent(bd.bsdf_flags) << "," << std::endl
       << "  rr_thp = " << string::indent(bd.rr_thp) << "," << std::endl
       << "  throughput = " << string::indent(bd.throughput) << "," << std::endl
       << "  bsdf_weight = " << string::indent(bd.bsdf_weight) << "," << std::endl
       << "  is_emitter = " << string::indent(bd.is_emitter) << "," << std::endl
       << "  last_nd_pdf = " << string::indent(bd.last_nd_pdf) << "," << std::endl
       << "  active = " << string::indent(bd.active) << "," << std::endl 
       << "]";
    return os;
}
/**
 * \brief Structure that stores the bounces from a ray traced through the scene.
 * Works as a conventional stack.
 */
template <typename Float_, typename Spectrum_>
class BounceBuffer {
public:

    using Float    = Float_;
    using Spectrum = Spectrum_;
    using BounceDataTp = BounceData<Float, Spectrum>;

    MI_IMPORT_RENDER_BASIC_TYPES()
    MI_IMPORT_OBJECT_TYPES()

    /**
     * \brief Create a new bounce buffer. 
     * 
     * \param sensor_origin The origin of the backwards-traced ray.
     */
    BounceBuffer() 
        : m_bdata()
    {}
    
private:
    std::vector<BounceDataTp> m_bdata;
    Vector3f m_sensor_origin;
};

NAMESPACE_END(mitsuba)
