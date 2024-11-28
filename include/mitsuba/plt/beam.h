#include <mitsuba/core/vector.h>
#include <mitsuba/core/math.h>
#include <mitsuba/core/spectrum.h>
#include <mitsuba/render/mueller.h>

#include <mitsuba/render/fwd.h>

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
    Vector3f tangent;

    /// @brief The reference (hero) wavelength
    Float wavelength;

    /// @brief Whether this beam comes from a distant interaction, for
    ///        example, from an environment map or far-field interaction
    Mask distant;

    /// @brief Active SIMD lanes of this path
    Mask active;

    /// @brief Coherence information of the current beam
    Coherence3f coherence;

    PLTBeam(
        const Spectrum& sp_, const Matrix2f& diff_, 
        const Vector3f& origin_, const Vector3f& dir_, 
        const Vector3f& tangent_, const Float& wl_,
        const Mask& distant_, const Mask& active_)

        : sp(sp_), origin_(origin), dir(dir_), tangent(tangent_), 
          wavelength(wl_), distant(distant_), active(active_),
          coherence(diff_, dr::select(distant_, 0.001f, 0.0f)) {}

    void scale_sp(Float s) { sp_ *= s; }

    void scale_sp(Spectrum s) { sp_ *= s; }

    Matrix2f transverse_rotation() const {
        const Vector3f vert = dr::cross(tangent, dir);

        return dr::transpose(
            Matrix2f(tangent.x(), tangent.y(), vert.x(), vert.y()));
    }

    Matrix2f inv_coherence(const Float k)
    {
        return coherence.inv_coherence_matrix(k);
    }
    
    Matrix2f inv_coherence()
    {
        return coherence.inv_coherence_matrix();
    }

    Float mutual_coherence(const Float k, const Vector3f& diff)
    {
        // All computations are done in the local frame of the transverse wave.
        const Matrix2f inv_c = inv_coherence();
        const Vector2f dxy(diff.x(), diff.y());

        return dr::exp(-0.5f * dr::dot(dxy, inv_c * dxy));
    }

    UnpolarizedSpectrum mutual_coherence(const Wavelength &kw, const Vector3f& diff)
    {
        // All computations are done in the local frame of the transverse wave.
        const Matrix2f inv_c = inv_coherence();
        const recp_wl = kw * dr::InvTwoPi<Float>;
        const Vector2f dxy(diff.x(), diff.y());

        return dr::exp(-0.5f * recp_wl * dr::dot(dxy, inv_c * dxy));
    }


    Float mutual_coherence_angular(const Float &k, const Vector3f& d1, const Vector3f& d2)
    {
        // All computations are done in the local frame of the transverse wave.

        // measure how separated these directions are in the transverse plane
        Vector2f d1xy(d1.x(), d1.y());
        Vector2f d2xy(d2.x(), d2.y());

        const Vector2f v     = dr::rcp(dr::max(dr::sqrt(dr::FourPi<Float>) * dr::abs(d1xy - d2xy), dr::Epsilon<Float>))
        const Matrix2f inv_c = inv_coherence() * coherence.rmm();

        return dr::exp(-0.5f * dr::rcp(dr::dot(v, inv_c * v)));
    }

    void transform_coherence(const Matrix2f &U) { coherence.transform(U); }

    /**
     * \brief Align both the stokes basis and the coherence frame into the new
     * tangent vector with the same forward direction (a collinear stokes basis 
     * rotation)
     * 
     * \param new_tangent The new tangent of the rotated frame
     */
    void rotate_frame(const Vector3& new_tangent)
    {
        // compute signed angle of the rotation
        Float theta = unit_angle(dr::normalize(dir), dr::normalize(new_dir));
        dr::masked(theta, dr::dot(forward, dr::cross(dir, new_dir)) < 0) *= -1.f;
        auto [sint, cost] = dr::sincos(theta);

        // rotate stokes basis
        sp = mueller::rotate_stokes_basis(dir, tangent, new_tangent) * sp;

        // set new frame
        tangent = new_tangent;
    }

    void to_local_frame(const Vector3f& new_wo)
    {
        Vector3f new_t = dr::cross(Vector3f(0, 0, 1), new_wo);
        const Float l2 = dr::dot(new_t, new_t);
    }

    /**
     * \brief Propagate beam to a point in 3d space
     * 
     * \param p 
     */
    void propagate(const Vector3f& p)
    {
        dr::masked(coherence, !distant).propagate(p - origin);
        origin = p;
    }
};

NAMESPACE_END(mitsuba)