#pragma once

#include <mitsuba/core/frame.h>
#include <mitsuba/core/fwd.h>
#include <mitsuba/core/math.h>
#include <mitsuba/core/spectrum.h>
#include <mitsuba/core/vector.h>

#include <mitsuba/plt/plt.h>

NAMESPACE_BEGIN(mitsuba)

enum class DiffractionGratingType : uint32_t {
    Sinusoidal  = 0x00,
    Rectangular = 0x01,
    Linear      = 0x02,
    Radial      = 0x10,

    TypeMask = 0xF,
};

MI_DECLARE_ENUM_OPERATORS(DiffractionGratingType)

static constexpr int diffractionGratingsMaxLobes = 9;

/**
 * \brief Diffraction grating model
 *
 * \tparam Float
 * \tparam Spectrum
 */
template <typename Float, typename Spectrum> class DiffractionGrating {
public:
    MI_IMPORT_CORE_TYPES()
    MI_IMPORT_TYPES()

    /**
     * \brief Construct a new Diffraction Grating object
     *
     * \param grating_angle The orientation of the grating
     * \param inv_period The inverse period of the grating, in um^(-1)
     * \param q The height of the grating, in um
     * \param lobes The number of lobes to consider for sampling. 7 lobes is
     * probably enough for most applications
     * \param type The type of grating (linear, sinusoidal or rectangular)
     * \param multiplier A factor that multiplies the lobe intensity.
     * \param uv The UV coordinates from which the grating originates
     */
    DiffractionGrating(const Float grating_angle, const Vector2f &inv_period,
                       const Float q, const uint32_t lobes,
                       const DiffractionGratingType type,
                       const Float multiplier = 1.0f,
                       Vector2f uv            = Vector2f(0.0f))
        : m_inv_period(inv_period), m_q(q), m_lobe_count(lobes), m_type(type),
          m_multiplier(multiplier) {
        // compute grating direction vector
        if ((m_type & DiffractionGratingType::Radial) == 0) {
            // linear grating, direction following grating angle
            m_grating_dir = Vector2f(cos(grating_angle), sin(grating_angle));
        } else {
            // radial grating following UV vector + rotation angle
            const Vector2f radial = dr::normalize(uv - Vector2f(0.5f, 0.5f));
            m_grating_dir = Matrix2f(cos(grating_angle), sin(grating_angle),
                                     -sin(grating_angle), cos(grating_angle)) *
                            Vector2f(radial.x(), -radial.y());
        }
    }

    /**
     * Return whether the grating is only 1 dimensional or has gratings in both
     * U and V dimensions.
     */
    Mask is_1D_grating() { return m_inv_period.y() < dr::Epsilon<Float>; }

    /**
     * Return the far field "roughness" of the material
     */
    Float alpha(const Vector3f &wi, const Float k) const {
        Float cos_theta_i = Frame<Float>::cos_theta(wi);
        Float a           = dr::square(cos_theta_i * m_q * k);

        return dr::exp(-a);
    }

    /**
     * Construct a shading frame aligned with the grating direction.
     */
    Frame3f shadingFrame(const Vector3f &n) const {
        Vector3f bit = dr::cross(n, m_grating_dir);

        return Frame3f(n, m_grating_dir, bit);
    }

    /**
     * \brief Given a 2D uniform sample, an inciding direction and wavelength,
     * sample a lobe and its pdf.
     *
     * \param sample2 The random sample to compute a lobe
     * \param wi The incident direction
     * \param wl The sampling wavelength (normally the hero wavelength of the
     * beam)
     * \return std::pair<Vector2i, Vector2f> The integer lobe index in both
     * dimensions and its PDF
     */
    std::pair<Vector2i, Vector2f>
    sample_lobe(const Vector2f &sample2, const Vector3f &wi, const Float wl) {
        // compute intensity of each lobe;
        Float intensities[diffractionGratingsMaxLobes];
        Float total = 0.0f;

        for (uint32_t l = 0; l < m_lobe_count / 2 + 1; ++l) {
            Float li = lobe_intensity(Vector2i(l, 0), wi, wl);
            if (l == 0) {
                li /= 2.0f;
            }
            total += li;
            intensities[l] = li;
        }

        // choose lobe based on its probability
        // TODO: Study if these loops can be vectorized more with drjit.
        Float cdf(0.0f);
        Vector2f pdf(0.0f);
        Vector2i lobe(0);
        Vector2f rn       = (sample2 - 0.5f) * 2.0f;
        Vector2f rnd_sign = dr::sign(rn);

        for (uint32_t l = 0; l < m_lobe_count / 2 + 1; ++l) {
            Float p = intensities[l] / total;

            Mask s1 = dr::abs(rn.x()) > cdf;
            Mask s2 = dr::abs(rn.y()) > cdf;

            pdf = Vector2f(
                dr::select(s1, dr::select(l == 0, p, p / 2.0f), pdf.x()),
                dr::select(s2, dr::select(l == 0, p, p / 2.0f), pdf.y()));

            lobe = Vector2f(dr::select(s1, l, lobe.x()),
                            dr::select(s2, l, lobe.y()));

            // std::cout << pdf << "(" << pdf.x() * pdf.y() << ")" << "," <<
            // lobe << std::endl;

            cdf += p;
        }

        lobe *= rnd_sign;

        return std::make_pair<Vector2i, Vector2f>(std::move(lobe),
                                                  std::move(pdf));
    }

    /**
     * \brief Given a diffraction lobe, return its pdf with respect to the total
     * intensity distribution.
     *
     * \param lobe The diffraction lobe indices
     * \param wi The incident direction
     * \param wl The sampling wavelength (normally the hero wavelength of the
     * beam)
     * \return std::pair<Vector2i, Vector2f> The integer lobe index in both
     * dimensions and its PDF
     */
    Float lobe_pdf(const Vector2i &lobe, const Vector3f &wi, const Float wl) {

        // Allocate dynamic array of intensities
        dr::DynamicArray<Float> intensities =
            dr::zeros<dr::DynamicArray<Float>>(diffractionGratingsMaxLobes);

        // Accumulate total intensity and scatter values
        Float total = dr::zeros<Float>();
        Float ix(0.0f), iy(0.0f);
        for (uint32_t l = 0; l <= m_lobe_count / 2; ++l) {
            Float li = lobe_intensity(Vector2i(l, 0), wi, wl);
            if (l == 0)
                li *= 0.5f;
            total += li;

            // if lobe matches then assign to pdf
            // incrementally fills the pdf values without needing to gather the intensity afterwards
            // for pdf computation
            ix = dr::select(dr::abs(lobe.x()) == l, li, ix);
            iy = dr::select(dr::abs(lobe.y()) == l, li, iy);
        }

        Float pdf_x = ix / total;
        Float pdf_y = iy / total;

        return pdf_x * pdf_y;
    }

    /**
     * \brief Compute the outwards diffracted direction for a specific
     * diffraction lobe
     *
     * \param wi
     * \param lobe
     * \param wl
     * \return Vector3f
     */
    std::pair<Vector3f, Mask> diffract(const Vector3f &wi, const Vector2i &lobe,
                                       const Float wl) {
        Vector2f wi_xy   = Vector2f(wi.x(), wi.y()), wi_zz(wi.z(), wi.z());
        const Vector2f p = dr::sqrt(dr::square(wi_xy) + dr::square(wi_zz));
        const Vector2f sin_i(
            dr::select(p.x() > dr::Epsilon<Float>, wi.x() / p.x(), 0.0f),
            dr::select(p.y() > dr::Epsilon<Float>, wi.y() / p.y(), 0.0f));

        // Here we operate on a different reciprocal lattice basis
        Float cos_g = m_grating_dir.x();
        Float sin_g = m_grating_dir.y();
        Vector2f lobe_rotated(cos_g * lobe.x() - sin_g * lobe.y(),
                              sin_g * lobe.x() + cos_g * lobe.y());

        const Vector2f sin_o = wl * lobe_rotated * m_inv_period - sin_i;
        const Float a = sin_o.x(), b = sin_o.y();
        const Float m = (dr::square(a) - 1) / (dr::square(a * b) - 1);
        const Float q = 1 - dr::square(b) * m;

        // diffracted directions
        Vector3f diff(a * dr::sqrt(dr::maximum(0.0f, q)), b * dr::sqrt(m),
                      dr::sqrt(dr::maximum(0.0f, 1 - dr::square(a) * q -
                                                     dr::square(b) * m)));

        return { diff, dr::all(dr::abs(sin_o) <= 1.0f) };
    }

    Float lobe_intensity(const Vector2i &lobe, const Vector3f &wi,
                         const Float wl) {
        DiffractionGratingType gtype = DiffractionGratingType(
            uint32_t(m_type) & uint32_t(DiffractionGratingType::TypeMask));

        // k = 2pi / lambda, abs(z) returns the angle of the diffracted lobe
        const Float a = dr::FourPi<Float> * m_q / (wl * dr::abs(wi.z()));
        Float ix, iy;
        Float lx = static_cast<Float>(lobe.x());
        Float ly = static_cast<Float>(lobe.y());

        switch (gtype) {
            case DiffractionGratingType::Sinusoidal:
                ix = dr::select(lobe.x() == 0, 1.0,
                                dr::square(math::bessel_j(a, lobe.x())));

                iy = dr::select(
                    is_1D_grating(), ix,
                    dr::select(lobe.y() == 0, 1.0,
                               dr::square(math::bessel_j(a, lobe.y()))));

                break;
            case DiffractionGratingType::Rectangular:
                ix = dr::select(
                    lobe.x() == 0, 1.0,
                    dr::sin(a / 2.0f) *
                        math::sinc<Float>(dr::Pi<Float> * lx / 2.0f));
                iy = dr::select(is_1D_grating(), ix,
                                dr::select(lobe.y() == 0, 1.0,
                                           dr::sin(a / 2.0f) *
                                               math::sinc<Float>(dr::Pi<Float> *
                                                                 ly / 2.0f)));

                break;
            default:
                ix = dr::select(lobe.x() == 0, 1, 1.f / dr::sqrt(dr::abs(lx)));

                iy = dr::select(
                    is_1D_grating(), ix,
                    dr::select(lobe.y() == 0, 1, 1.f / dr::sqrt(dr::abs(ly))));

                break;
        }
        return m_multiplier * ix * iy;
    }

private:
    /// \brief The normalized direction of the grating in local coordinate
    /// space.
    Vector2f m_grating_dir;

    /// \brief The inverse period of the grating
    Vector2f m_inv_period;

    /// @brief Height scale of the grating
    Float m_q;

    /// @brief Number of diffraction lobes
    uint32_t m_lobe_count         = 5;
    DiffractionGratingType m_type = DiffractionGratingType::Sinusoidal;

    Float m_multiplier = 1.0f;
};

NAMESPACE_END(mitsuba)