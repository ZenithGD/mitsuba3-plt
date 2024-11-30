#include <mitsuba/core/vector.h>
#include <mitsuba/core/math.h>
#include <mitsuba/core/spectrum.h>
#include <mitsuba/render/mueller.h>
#include <drjit/math.h>
#include <drjit/sphere.h>

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

    /// @brief Whether this beam comes from a distant interaction, for
    ///        example, from an environment map or far-field interaction
    Mask distant;

    /// @brief Coherence information of the current beam
    Coherence3f coherence;

    /// @brief Active SIMD lanes of this path
    Mask active;

    PLTBeam(
        const Spectrum& sp_, const Matrix2f& diff_, 
        const Vector3f& origin_, const Vector3f& dir_, 
        const Vector3f& tangent_, const Mask& distant_, 
        const Mask& active_ = true)

        : sp(sp_), origin(origin_), dir(dir_), tangent(tangent_), 
          distant(distant_), active(active_),
          coherence(diff_, dr::select(distant_, 0.001f, 0.0f)) {}

    void scale_sp(Float s) { sp *= s; }

    void scale_sp(UnpolarizedSpectrum s) { sp *= s; }

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

    Float mutual_coherence(const Float& k, const Vector3f& diff)
    {
        // All computations are done in the local frame of the transverse wave.
        const Matrix2f inv_c = inv_coherence();
        const Vector2f dxy(diff.x(), diff.y());

        return dr::exp(-0.5f * dr::dot(dxy, inv_c * dxy));
    }

    Spectrum mutual_coherence(const Wavelength &kw, const Vector3f& diff)
    {
        // All computations are done in the local frame of the transverse wave.
        if constexpr (is_spectral_v<Spectrum>) {
            const Matrix2f inv_c = inv_coherence();
            const Wavelength recp_wl = kw * dr::InvTwoPi<Float>;
            const Vector2f dxy(diff.x(), diff.y());

            return dr::exp(-0.5f * recp_wl * dr::dot(dxy, inv_c * dxy));
        }
        else {
            Throw("Can't compute mutual coherence in non-spectral variants!");
        }
    }


    Float mutual_coherence_angular(const Vector3f& d1, const Vector3f& d2)
    {
        // All computations are done in the local frame of the transverse wave.

        // measure how separated these directions are in the transverse plane
        Vector2f d1xy(d1.x(), d1.y());
        Vector2f d2xy(d2.x(), d2.y());

        const Vector2f v =
            dr::rcp(dr::maximum(dr::sqrt(dr::FourPi<Float>) * dr::abs(d1xy - d2xy),
                            dr::Epsilon<Float>));
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
    void rotate_frame(const Vector3f& new_tangent)
    {
        if constexpr (is_polarized_v<Spectrum>) {
            // compute signed angle of the rotation
            Float theta = dr::unit_angle(dr::normalize(tangent), dr::normalize(new_tangent));
            dr::masked(theta, dr::dot(dir, dr::cross(tangent, new_tangent)) < 0) *= -1.f;
            auto [sint, cost] = dr::sincos(theta);

            // rotate stokes basis
            sp = mueller::rotate_stokes_basis(dir, tangent, new_tangent) * sp;

            // set new frame
            tangent = new_tangent;
        }
        else {
            Throw("Can't rotate frame in unpolarized mode!");
        }
    }

    void create_local_frame(const Vector3f& new_wo)
    {
        Vector3f new_t = dr::cross(Vector3f(0, 0, 1), new_wo);
        const Float l2 = dr::dot(new_t, new_t);

        Vector3f t, s;
        std::tie(s, t) = coordinate_system(new_wo);
        new_t = dr::select(l2 > dr::Epsilon<Float>, new_t / dr::sqrt(l2), t);
    }

    /**
     * \brief Propagate beam to a point in 3d space
     * 
     * \param p 
     */
    void propagate(const Vector3f& p)
    {
        coherence.propagate(dr::norm(p - origin), !distant);
        origin = p;
    }

    static PLTBeam3f plt_source_beam_distant(const Vector3f& dir, 
        const Float& solid_angle, const UnpolarizedSpectrum& Le,
        const Wavelength& wavelengths, const Float& max_beam_omega,
        const Mask& force_fully_coherent)
    {
        Float sa = dr::min(solid_angle, max_beam_omega);
        const Matrix2f diff =
            dr::select(force_fully_coherent, 1e-9f * dr::identity<Matrix2f>(),
                       sa * dr::identity<Matrix2f>());

        Vector3f t, b;
        std::tie(s, t) = coordinate_system(new_wo);

        return PLTBeam3f(Le, diff, Vector3f(0.0), dir, t, true);
    }


    DRJIT_STRUCT(PLTBeam, sp, origin, dir, tangent, distant, active, coherence)
};

NAMESPACE_END(mitsuba)