#include <mitsuba/core/fwd.h>
#include <mitsuba/core/plugin.h>
#include <mitsuba/core/string.h>
#include <mitsuba/render/bsdf.h>
#include <mitsuba/render/ior.h>
#include <mitsuba/render/microfacet.h>
#include <mitsuba/render/sampler.h>
#include <mitsuba/render/texture.h>

#include <mitsuba/plt/diffractiongrating.h>
#include <mitsuba/plt/fwd.h>

NAMESPACE_BEGIN(mitsuba)

/**!
.. _bsdf-roughconductor:

Rough conductor material (:monosp:`roughconductor`)
---------------------------------------------------

.. pluginparameters::

 * - material
   - |string|
   - Name of the material preset, see :num:`conductor-ior-list`. (Default: none)

 * - eta, k
   - |spectrum| or |texture|
   - Real and imaginary components of the material's index of refraction.
(Default: based on the value of :monosp:`material`)
   - |exposed|, |differentiable|, |discontinuous|

 * - specular_reflectance
   - |spectrum| or |texture|
   - Optional factor that can be used to modulate the specular reflection
component. Note that for physical realism, this parameter should never be
touched. (Default: 1.0)
   - |exposed|, |differentiable|

 * - distribution
   - |string|
   - Specifies the type of microfacet normal distribution used to model the
surface roughness.

     - :monosp:`beckmann`: Physically-based distribution derived from Gaussian
random surfaces. This is the default.
     - :monosp:`ggx`: The GGX :cite:`Walter07Microfacet` distribution (also
known as Trowbridge-Reitz :cite:`Trowbridge19975Average` distribution) was
designed to better approximate the long tails observed in measurements of ground
surfaces, which are not modeled by the Beckmann distribution.

 * - alpha, alpha_u, alpha_v
   - |texture| or |float|
   - Specifies the roughness of the unresolved surface micro-geometry along the
tangent and bitangent directions. When the Beckmann distribution is used, this
parameter is equal to the
     **root mean square** (RMS) slope of the microfacets. :monosp:`alpha` is a
convenience parameter to initialize both :monosp:`alpha_u` and :monosp:`alpha_v`
to the same value. (Default: 0.1)
   - |exposed|, |differentiable|, |discontinuous|

 * - sample_visible
   - |bool|
   - Enables a sampling technique proposed by Heitz and D'Eon
:cite:`Heitz1014Importance`, which focuses computation on the visible parts of
the microfacet normal distribution, considerably reducing variance in some
cases. (Default: |true|, i.e. use visible normal sampling)

This plugin implements a realistic microfacet scattering model for rendering
rough conducting materials, such as metals.

.. subfigstart::
.. subfigure::
../../resources/data/docs/images/render/bsdf_roughconductor_copper.jpg :caption:
Rough copper (Beckmann, :math:`\alpha=0.1`)
.. subfigure::
../../resources/data/docs/images/render/bsdf_roughconductor_anisotropic_aluminium.jpg
   :caption: Vertically brushed aluminium (Anisotropic Beckmann,
:math:`\alpha_u=0.05,\ \alpha_v=0.3`)
.. subfigure::
../../resources/data/docs/images/render/bsdf_roughconductor_textured_carbon.jpg
   :caption: Carbon fiber using two inverted checkerboard textures for
``alpha_u`` and ``alpha_v``
.. subfigend::
    :label: fig-bsdf-roughconductor


Microfacet theory describes rough surfaces as an arrangement of unresolved
and ideally specular facets, whose normal directions are given by a
specially chosen *microfacet distribution*. By accounting for shadowing
and masking effects between these facets, it is possible to reproduce the
important off-specular reflections peaks observed in real-world measurements
of such materials.

This plugin is essentially the *roughened* equivalent of the (smooth) plugin
:ref:`conductor <bsdf-conductor>`. For very low values of :math:`\alpha`, the
two will be identical, though scenes using this plugin will take longer to
render due to the additional computational burden of tracking surface roughness.

The implementation is based on the paper *Microfacet Models
for Refraction through Rough Surfaces* by Walter et al.
:cite:`Walter07Microfacet` and it supports two different types of microfacet
distributions.

To facilitate the tedious task of specifying spectrally-varying index of
refraction information, this plugin can access a set of measured materials
for which visible-spectrum information was publicly available
(see the corresponding table in the :ref:`conductor <bsdf-conductor>`
reference).

When no parameters are given, the plugin activates the default settings,
which describe a 100% reflective mirror with a medium amount of roughness
modeled using a Beckmann distribution.

To get an intuition about the effect of the surface roughness parameter
:math:`\alpha`, consider the following approximate classification: a value of
:math:`\alpha=0.001-0.01` corresponds to a material with slight imperfections
on an otherwise smooth surface finish, :math:`\alpha=0.1` is relatively rough,
and :math:`\alpha=0.3-0.7` is **extremely** rough (e.g. an etched or ground
finish). Values significantly above that are probably not too realistic.


The following XML snippet describes a material definition for brushed aluminium:

.. tabs::
    .. code-tab:: xml
        :name: lst-roughconductor-aluminium

        <bsdf type="roughconductor">
            <string name="material" value="Al"/>
            <string name="distribution" value="ggx"/>
            <float name="alpha_u" value="0.05"/>
            <float name="alpha_v" value="0.3"/>
        </bsdf>

    .. code-tab:: python

        'type': 'roughconductor',
        'material': 'Al',
        'distribution': 'ggx',
        'alpha_u': 0.05,
        'alpha_v': 0.3

Technical details
*****************

All microfacet distributions allow the specification of two distinct
roughness values along the tangent and bitangent directions. This can be
used to provide a material with a *brushed* appearance. The alignment
of the anisotropy will follow the UV parameterization of the underlying
mesh. This means that such an anisotropic material cannot be applied to
triangle meshes that are missing texture coordinates.

Since Mitsuba 0.5.1, this plugin uses a new importance sampling technique
contributed by Eric Heitz and Eugene D'Eon, which restricts the sampling
domain to the set of visible (unmasked) microfacet normals. The previous
approach of sampling all normals is still available and can be enabled
by setting :monosp:`sample_visible` to :monosp:`false`. However this will lead
to significantly slower convergence.

When using this plugin, you should ideally compile Mitsuba with support for
spectral rendering to get the most accurate results. While it also works
in RGB mode, the computations will be more approximate in nature.
Also note that this material is one-sided---that is, observed from the
back side, it will be completely black. If this is undesirable,
consider using the :ref:`twosided <bsdf-twosided>` BRDF adapter.

In *polarized* rendering modes, the material automatically switches to a
polarized implementation of the underlying Fresnel equations.

 */

template <typename Float, typename Spectrum>
class RoughGrating final : public BSDF<Float, Spectrum> {
public:
    MI_IMPORT_BASE(BSDF, m_flags, m_components)
    MI_IMPORT_TYPES(Texture, MicrofacetDistribution, Sampler)
    MI_IMPORT_PLT_BASIC_TYPES()

    RoughGrating(const Properties &props) : Base(props) {
        std::string material = props.string("material", "none");
        if (props.has_property("eta") || material == "none") {
            m_eta = props.texture<Texture>("eta", 0.f);
            m_k   = props.texture<Texture>("k", 1.f);
            if (material != "none")
                Throw("Should specify either (eta, k) or material, not both.");
        } else {
            std::tie(m_eta, m_k) = complex_ior_from_file<Spectrum, Texture>(
                props.string("material", "Cu"));
        }

        if (props.has_property("distribution")) {
            std::string distr = string::to_lower(props.string("distribution"));
            if (distr == "beckmann")
                m_type = MicrofacetType::Beckmann;
            else if (distr == "ggx")
                m_type = MicrofacetType::GGX;
            else
                Throw("Specified an invalid distribution \"%s\", must be "
                      "\"beckmann\" or \"ggx\"!",
                      distr.c_str());
        } else {
            m_type = MicrofacetType::Beckmann;
        }

        m_sample_visible = props.get<bool>("sample_visible", true);

        if (props.has_property("alpha_u") || props.has_property("alpha_v")) {
            if (!props.has_property("alpha_u") ||
                !props.has_property("alpha_v"))
                Throw("Microfacet model: both 'alpha_u' and 'alpha_v' must be "
                      "specified.");
            if (props.has_property("alpha"))
                Throw("Microfacet model: please specify"
                      "either 'alpha' or 'alpha_u'/'alpha_v'.");
            m_alpha_u = props.texture<Texture>("alpha_u");
            m_alpha_v = props.texture<Texture>("alpha_v");
        } else {
            m_alpha_u = m_alpha_v = props.texture<Texture>("alpha", 0.1f);
        }

        if (props.has_property("specular_reflectance"))
            m_specular_reflectance =
                props.texture<Texture>("specular_reflectance", 1.f);

        m_flags = BSDFFlags::GlossyReflection | BSDFFlags::FrontSide;
        if (m_alpha_u != m_alpha_v)
            m_flags = m_flags | BSDFFlags::Anisotropic;

        // grating properties
        m_grating_angle = props.texture<Texture>("grating_angle", 0.0f);

        if (props.has_property("inv_period_x") ||
            props.has_property("inv_period_x")) {
            if (!props.has_property("inv_period_x") ||
                !props.has_property("inv_period_x"))
                Throw("Grating inv inv_period: both 'inv_period_x' and "
                      "'inv_period_x' must be specified.");
            if (props.has_property("inv_period"))
                Throw("Grating inv inv_period: please specify"
                      "either 'inv_period' or 'inv_period_x'/'inv_period_x'.");
            m_inv_period_x = props.texture<Texture>("inv_period_x");
            m_inv_period_y = props.texture<Texture>("inv_period_y");
        } else {
            m_inv_period_x = m_inv_period_y =
                props.texture<Texture>("inv_period", 0.1f);
        }
        m_height = props.texture<Texture>("height", 0.3f);
        m_lobes  = props.get<uint32_t>("lobes", 5);
        std::string lobe_type =
            props.get<std::string>("lobe_type", "rectangular");

        if (lobe_type == "rectangular") {
            m_lobe_type = DiffractionGratingType::Rectangular;
        } else if (lobe_type == "linear") {
            m_lobe_type = DiffractionGratingType::Linear;
        } else if (lobe_type == "sinusoidal") {
            m_lobe_type = DiffractionGratingType::Sinusoidal;
        } else {
            Throw("Grating surface type %s not supported!", lobe_type);
        }

        m_radial = props.get<bool>("radial", false);
        if (m_radial) {
            m_lobe_type = static_cast<DiffractionGratingType>(
                static_cast<uint32_t>(m_lobe_type) |
                static_cast<uint32_t>(DiffractionGratingType::Radial));
        }
        m_multiplier = props.texture<Texture>("multiplier", 1.0f);

        // Assume light is very coherent by default -> small angular spread
        m_coherence = props.get<ScalarFloat>("coherence", 1e-18f);

        m_components.clear();
        m_components.push_back(m_flags);
    }

    void traverse(TraversalCallback *callback) override {
        if (m_specular_reflectance)
            callback->put_object("specular_reflectance",
                                 m_specular_reflectance.get(),
                                 +ParamFlags::Differentiable);
        if (!has_flag(m_flags, BSDFFlags::Anisotropic))
            callback->put_object("alpha", m_alpha_u.get(),
                                 ParamFlags::Differentiable |
                                     ParamFlags::Discontinuous);
        else {
            callback->put_object("alpha_u", m_alpha_u.get(),
                                 ParamFlags::Differentiable |
                                     ParamFlags::Discontinuous);
            callback->put_object("alpha_v", m_alpha_v.get(),
                                 ParamFlags::Differentiable |
                                     ParamFlags::Discontinuous);
        }
        callback->put_object("eta", m_eta.get(),
                             ParamFlags::Differentiable |
                                 ParamFlags::Discontinuous);
        callback->put_object("k", m_k.get(),
                             ParamFlags::Differentiable |
                                 ParamFlags::Discontinuous);
        callback->put_object("inv_period_x", m_inv_period_x.get(),
                             ParamFlags::Differentiable |
                                 ParamFlags::Discontinuous);
        callback->put_object("inv_period_y", m_inv_period_y.get(),
                             ParamFlags::Differentiable |
                                 ParamFlags::Discontinuous);
        callback->put_object("height", m_height.get(),
                             ParamFlags::Differentiable |
                                 ParamFlags::Discontinuous);
        callback->put_object("grating_angle", m_grating_angle.get(),
                             ParamFlags::Differentiable |
                                 ParamFlags::Discontinuous);
        callback->put_object("m_multiplier", m_grating_angle.get(),
                             ParamFlags::Differentiable |
                                 ParamFlags::Discontinuous);
    }

    /**
     * Note: Apart from PLT Integrator, this sampling routine will behave
     * as a conventional rough conductor.
     */
    std::pair<BSDFSample3f, Spectrum> sample(const BSDFContext &ctx,
                                             const SurfaceInteraction3f &si,
                                             Float /* sample1 */,
                                             const Point2f &sample2,
                                             Mask active) const override {
        MI_MASKED_FUNCTION(ProfilerPhase::BSDFSample, active);

        BSDFSample3f bs   = dr::zeros<BSDFSample3f>();
        Float cos_theta_i = Frame3f::cos_theta(si.wi);
        active &= cos_theta_i > 0.f;

        if (unlikely(!ctx.is_enabled(BSDFFlags::GlossyReflection) ||
                     dr::none_or<false>(active)))
            return { bs, 0.f };

        /* Construct a microfacet distribution matching the
        roughness values at the current surface position. */
        MicrofacetDistribution distr(m_type, m_alpha_u->eval_1(si, active),
                                     m_alpha_v->eval_1(si, active),
                                     m_sample_visible);

        // Sample M, the microfacet normal
        Normal3f m;
        std::tie(m, bs.pdf) = distr.sample(si.wi, sample2);

        // Perfect specular reflection based on the microfacet normal
        bs.wo                = reflect(si.wi, m);
        bs.eta               = 1.f;
        bs.sampled_component = 0;
        bs.sampled_type      = +BSDFFlags::GlossyReflection;

        // Ensure that this is a valid sample
        active &= (bs.pdf != 0.f) && Frame3f::cos_theta(bs.wo) > 0.f;

        UnpolarizedSpectrum weight;
        if (likely(m_sample_visible))
            weight = distr.smith_g1(bs.wo, m);
        else
            weight = distr.G(si.wi, bs.wo, m) * dr::dot(si.wi, m) /
                     (cos_theta_i * Frame3f::cos_theta(m));

        // Jacobian of the half-direction mapping
        bs.pdf /= 4.f * dr::dot(bs.wo, m);

        // Evaluate the Fresnel factor
        dr::Complex<UnpolarizedSpectrum> eta_c(m_eta->eval(si, active),
                                               m_k->eval(si, active));

        Spectrum F;
        if constexpr (is_polarized_v<Spectrum>) {
            /* Due to the coordinate system rotations for polarization-aware
            pBSDFs below we need to know the propagation direction of light.
            In the following, light arrives along `-wo_hat` and leaves along
            `+wi_hat`. */
            Vector3f wo_hat =
                         ctx.mode == TransportMode::Radiance ? bs.wo : si.wi,
                     wi_hat =
                         ctx.mode == TransportMode::Radiance ? si.wi : bs.wo;

            // Mueller matrix for specular reflection.
            F = mueller::specular_reflection(
                UnpolarizedSpectrum(dot(wo_hat, m)), eta_c);

            /* The Stokes reference frame vector of this matrix lies
            perpendicular to the plane of reflection. */
            Vector3f s_axis_in  = dr::cross(m, -wo_hat);
            Vector3f s_axis_out = dr::cross(m, wi_hat);

            // Singularity when the input & output are collinear with the normal
            Mask collinear = dr::all(s_axis_in == Vector3f(0));
            s_axis_in      = dr::select(collinear, Vector3f(1, 0, 0),
                                        dr::normalize(s_axis_in));
            s_axis_out     = dr::select(collinear, Vector3f(1, 0, 0),
                                        dr::normalize(s_axis_out));

            /* Rotate in/out reference vector of F s.t. it aligns with the
            implicit Stokes bases of -wo_hat & wi_hat. */
            F = mueller::rotate_mueller_basis(
                F, -wo_hat, s_axis_in, mueller::stokes_basis(-wo_hat), wi_hat,
                s_axis_out, mueller::stokes_basis(wi_hat));
        } else {
            F = fresnel_conductor(UnpolarizedSpectrum(dr::dot(si.wi, m)),
                                  eta_c);
        }

        /* If requested, include the specular reflectance component */
        if (m_specular_reflectance)
            weight *= m_specular_reflectance->eval(si, active);

        return { bs, (F * weight) & active };
    }

    std::tuple<Vector3f, Float, Float, Vector2i, Mask>
    sample_diffract(const Vector2f &sample2, const SurfaceInteraction3f &si,
                    Normal3f &n, const Float &wl, Mask active) const {
        // new frame along normal to compute diffracted direction
        // in that frame
        Frame3f normalFrame(n);
        Vector3f wi_local = normalFrame.to_local(si.wi);
        // std::cout << wi << ";" << wi_local << std::endl;

        // sample lobe and diffract in local frame
        DiffractionGrating3f grating(
            m_grating_angle->eval_1(si),
            Vector2f(
                m_inv_period_x->eval_1(si, active), 
                m_inv_period_y->eval_1(si, active)),
            m_height->eval_1(si, active), 
            m_lobes, 
            m_lobe_type,
            m_multiplier->eval_1(si, active), 
            si.uv);

        auto [lobe, pdf_xy] =
            grating.sample_lobe(sample2, wi_local, wl * 1e-3f);

        Float intensity = grating.lobe_intensity(lobe, wi_local, wl);

        // std::cout << lobe << std::endl;

        auto [wo_local, active_diff] = grating.diffract(wi_local, lobe, wl * 1e-3f);
        // std::cout << wo_local << std::endl;

        Vector3f wo = normalFrame.to_world(wo_local);
        return { wo, pdf_xy.x() * pdf_xy.y(), intensity, lobe, active & active_diff };
    }

    std::pair<PLTSamplePhaseData3f, GeneralizedRadiance3f>
    wbsdf_sample(const BSDFContext &ctx, const SurfaceInteraction3f &si,
                 Float sample1, const Point2f &sample2,
                 const Point2f &lobe_sample2, Mask active) const override {
        MI_MASKED_FUNCTION(ProfilerPhase::BSDFSample, active);

        BSDFSample3f bs   = dr::zeros<BSDFSample3f>();
        Float cos_theta_i = Frame3f::cos_theta(si.wi);
        active &= cos_theta_i > 0.f;

        if (unlikely(!ctx.is_enabled(BSDFFlags::GlossyReflection) ||
                     dr::none_or<false>(active))) {

            UnpolarizedSpectrum(0.0f);
            if constexpr (is_spectral_v<Spectrum>) {
                PLTSamplePhaseData<Float, Spectrum> sd(
                    bs, 
                    Vector2i(0, 0), 
                    Vector3f(0, 0, 0), 
                    Coherence<Float, Spectrum>(Float(0.0f), Float(0.0f)), 
                    si.wavelengths);
                return { sd, GeneralizedRadiance3f(0.0f) };
            } else {
                PLTSamplePhaseData<Float, Spectrum> sd(
                    bs, 
                    Vector2i(0, 0), 
                    Vector3f(0, 0, 0), 
                    Coherence<Float, Spectrum>(Float(0.0f), Float(0.0f)), 
                    UnpolarizedSpectrum(0.0));
                return { sd, GeneralizedRadiance3f(0.0f) };
            }
        }
        /* Construct a microfacet distribution matching the
           roughness values at the current surface position. */
        MicrofacetDistribution distr(m_type, m_alpha_u->eval_1(si, active),
                                     m_alpha_v->eval_1(si, active),
                                     m_sample_visible);

        // Sample M, the microfacet normal
        Normal3f m;
        std::tie(m, bs.pdf) = distr.sample(si.wi, sample2);

        // Diffract along the normal
        // The sampled lobe pdf must be provided as well
        Float grating_pdf, intensity;
        Vector2i lobe;
        Mask active_diffracted;
        Vector3f reflection_dir = reflect(si.wi, m);
        // TODO: loop for each wavelength

        Float wavelength;
        if constexpr (is_spectral_v<Spectrum>) {
            wavelength = si.wavelengths[0];
        } else {
            // Use sample 1 for random wavelength sample
            wavelength =
                sample1 * (MI_CIE_MAX - 150.0f - MI_CIE_MIN) + MI_CIE_MIN;
        }

        std::tie(bs.wo, grating_pdf, intensity, lobe, active_diffracted) =
            sample_diffract(lobe_sample2, si, m, wavelength, active);
        bs.eta               = 1.f;
        bs.sampled_component = 0;
        bs.sampled_type      = +BSDFFlags::GlossyReflection;

        // Ensure that this is a valid sample
        active &= (bs.pdf != 0.f) && Frame3f::cos_theta(bs.wo) > 0.f;

        bs.pdf *= grating_pdf;

        UnpolarizedSpectrum weight;
        if (likely(m_sample_visible))
            weight = distr.smith_g1(reflection_dir, m);
        else
            weight = distr.G(si.wi, reflection_dir, m) * dr::dot(si.wi, m) /
                     (cos_theta_i * Frame3f::cos_theta(m));

        // Jacobian of the half-direction mapping
        bs.pdf /= 4.f * dr::dot(reflection_dir, m);

        // Evaluate the Fresnel factor
        dr::Complex<UnpolarizedSpectrum> eta_c(m_eta->eval(si, active),
                                               m_k->eval(si, active));

        Spectrum F;
        if constexpr (is_polarized_v<Spectrum>) {
            /* Due to the coordinate system rotations for polarization-aware
               pBSDFs below we need to know the propagation direction of light.
               In the following, light arrives along `-wo_hat` and leaves along
               `+wi_hat`. */
            Vector3f wo_hat = ctx.mode == TransportMode::Radiance
                                  ? reflection_dir
                                  : si.wi,
                     wi_hat = ctx.mode == TransportMode::Radiance
                                  ? si.wi
                                  : reflection_dir;

            // Mueller matrix for specular reflection.
            F = mueller::specular_reflection(
                UnpolarizedSpectrum(dot(wo_hat, m)), eta_c);

            /* The Stokes reference frame vector of this matrix lies
               perpendicular to the plane of reflection. */
            Vector3f s_axis_in  = dr::cross(m, -wo_hat);
            Vector3f s_axis_out = dr::cross(m, wi_hat);

            // Singularity when the input & output are collinear with the normal
            Mask collinear = dr::all(s_axis_in == Vector3f(0));
            s_axis_in      = dr::select(collinear, Vector3f(1, 0, 0),
                                        dr::normalize(s_axis_in));
            s_axis_out     = dr::select(collinear, Vector3f(1, 0, 0),
                                        dr::normalize(s_axis_out));

            /* Rotate in/out reference vector of F s.t. it aligns with the
               implicit Stokes bases of -wo_hat & wi_hat. */
            F = mueller::rotate_mueller_basis(
                F, -wo_hat, s_axis_in, mueller::stokes_basis(-wo_hat), wi_hat,
                s_axis_out, mueller::stokes_basis(wi_hat));
        } else {
            F = fresnel_conductor(UnpolarizedSpectrum(dr::dot(si.wi, m)),
                                  eta_c);
        }

        /* If requested, include the specular reflectance component */
        if (m_specular_reflectance)
            weight *= m_specular_reflectance->eval(si, active);

        if constexpr (is_spectral_v<Spectrum>) {
            PLTSamplePhaseData3f sd(
                bs, 
                lobe, 
                reflection_dir, 
                Coherence3f(Float(0.0f), Float(0.0f)),
                si.wavelengths);

            return { sd, (F * weight * intensity * m_multiplier->eval_1(si, active)) & active };
        } else {
            PLTSamplePhaseData3f sd(
                bs, 
                lobe, 
                reflection_dir,
                Coherence3f(Float(0.0f), Float(0.0f)),        
                UnpolarizedSpectrum(wavelength));

            return { sd, (F * weight * intensity * m_multiplier->eval_1(si, active)) & active };
        }
    }

    Spectrum eval(const BSDFContext &ctx, const SurfaceInteraction3f &si,
                  const Vector3f &wo, Mask active) const override {
        MI_MASKED_FUNCTION(ProfilerPhase::BSDFEvaluate, active);

        Float cos_theta_i = Frame3f::cos_theta(si.wi),
              cos_theta_o = Frame3f::cos_theta(wo);

        active &= cos_theta_i > 0.f && cos_theta_o > 0.f;

        if (unlikely(!ctx.is_enabled(BSDFFlags::GlossyReflection) ||
                     dr::none_or<false>(active)))
            return 0.f;

        // Calculate the half-direction vector
        Vector3f H = dr::normalize(wo + si.wi);

        /* Construct a microfacet distribution matching the
           roughness values at the current surface position. */
        MicrofacetDistribution distr(m_type, m_alpha_u->eval_1(si, active),
                                     m_alpha_v->eval_1(si, active),
                                     m_sample_visible);

        // Evaluate the microfacet normal distribution
        Float D = distr.eval(H);

        active &= D != 0.f;

        // Evaluate Smith's shadow-masking function
        Float G = distr.G(si.wi, wo, H);

        // Evaluate the full microfacet model (except Fresnel)
        UnpolarizedSpectrum result = D * G / (4.f * Frame3f::cos_theta(si.wi));

        // Evaluate the Fresnel factor
        dr::Complex<UnpolarizedSpectrum> eta_c(m_eta->eval(si, active),
                                               m_k->eval(si, active));

        Spectrum F;
        if constexpr (is_polarized_v<Spectrum>) {
            /* Due to the coordinate system rotations for polarization-aware
               pBSDFs below we need to know the propagation direction of light.
               In the following, light arrives along `-wo_hat` and leaves along
               `+wi_hat`. */
            Vector3f wo_hat = ctx.mode == TransportMode::Radiance ? wo : si.wi,
                     wi_hat = ctx.mode == TransportMode::Radiance ? si.wi : wo;

            // Mueller matrix for specular reflection.
            F = mueller::specular_reflection(
                UnpolarizedSpectrum(dot(wo_hat, H)), eta_c);

            /* The Stokes reference frame vector of this matrix lies
               perpendicular to the plane of reflection. */
            Vector3f s_axis_in  = dr::cross(H, -wo_hat);
            Vector3f s_axis_out = dr::cross(H, wi_hat);

            // Singularity when the input & output are collinear with the normal
            Mask collinear = dr::all(s_axis_in == Vector3f(0));
            s_axis_in      = dr::select(collinear, Vector3f(1, 0, 0),
                                        dr::normalize(s_axis_in));
            s_axis_out     = dr::select(collinear, Vector3f(1, 0, 0),
                                        dr::normalize(s_axis_out));

            /* Rotate in/out reference vector of F s.t. it aligns with the
               implicit Stokes bases of -wo_hat & wi_hat. */
            F = mueller::rotate_mueller_basis(
                F, -wo_hat, s_axis_in, mueller::stokes_basis(-wo_hat), wi_hat,
                s_axis_out, mueller::stokes_basis(wi_hat));
        } else {
            F = fresnel_conductor(UnpolarizedSpectrum(dr::dot(si.wi, H)),
                                  eta_c);
        }

        /* If requested, include the specular reflectance component */
        // if (m_specular_reflectance)
        //     result *= m_specular_reflectance->eval(si, active);

        return (F * result) & active;
    }

    GeneralizedRadiance3f wbsdf_eval(const BSDFContext &ctx,
                                     const SurfaceInteraction3f &si,
                                     const Vector3f &wo,
                                     const PLTSamplePhaseData3f &sd,
                                     Mask active) const override {
        MI_MASKED_FUNCTION(ProfilerPhase::BSDFEvaluate, active);

        Float cos_theta_i = Frame3f::cos_theta(si.wi),
              cos_theta_o = Frame3f::cos_theta(wo);

        active &= cos_theta_i > 0.f && cos_theta_o > 0.f;

        if (unlikely(!ctx.is_enabled(BSDFFlags::GlossyReflection) ||
                     dr::none_or<false>(active)))
            return 0.f;

        // Calculate the half-direction vector
        Vector3f H = dr::normalize(wo + si.wi);

        /* Construct a microfacet distribution matching the
        roughness values at the current surface position. */
        MicrofacetDistribution distr(m_type, m_alpha_u->eval_1(si, active),
                                     m_alpha_v->eval_1(si, active),
                                     m_sample_visible);

        // instantiate grating model
        DiffractionGrating3f grating(
            m_grating_angle->eval_1(si),
            Vector2f(
                m_inv_period_x->eval_1(si, active), 
                m_inv_period_y->eval_1(si, active)),
            m_height->eval_1(si, active), 
            m_lobes, 
            m_lobe_type,
            m_multiplier->eval_1(si, active), 
            si.uv);

        Vector3f reflection_dir = reflect(si.wi);

        // fallback in RGB mode
        if constexpr (!is_spectral_v<Spectrum>) {

            // Restrict to the peak wavelength of the RGB channels' SRF
            Spectrum result(0.0);
            dr::Array<Float, 3> wavelengths;
            wavelengths[0] = sd.sampling_wavelengths[0];
            wavelengths[1] = sd.sampling_wavelengths[1];
            wavelengths[2] = sd.sampling_wavelengths[2];

            auto a =
                2 * dr::sqrt(m_alpha_u->eval_1(si) * m_alpha_v->eval_1(si));

            // exhaustive search of the lobes
            for (int lx = -((int) m_lobes) / 2; lx < (int) m_lobes / 2 + 1;
                 lx++) {
                for (int ly = -((int) m_lobes) / 2; ly < (int) m_lobes / 2 + 1;
                     ly++) {
                    Vector2i lobe(lx, ly);

                    for (int i = 0; i < 3; i++) {
                        auto wl = wavelengths[i];
                        Float k = dr::TwoPi<Float> / (wl * 1e-3f);

                        Float lobe_intensity =
                            grating.lobe_intensity(lobe, si.wi, wl * 1e-3f);

                        Vector3f center_dir;
                        Mask lobe_active;
                        std::tie(center_dir, lobe_active) =
                            grating.diffract(si.wi, lobe, wl * 1e-3f);

                        auto colour        = xyz_to_srgb(cie1931_xyz(wl));
                        Float lobes_result = dr::select(
                            lobe_active &
                                dr::abs(dr::unit_angle(center_dir, wo)) < a,
                            lobe_intensity, 0.0);

                        // angular coherence between the center direction and the reflected dir
                        // TODO: admit anisotropic coherence information
                        Coherence3f coh(m_coherence, 1.0f);
                        Float angle_offset = dr::abs(dr::unit_angle(reflection_dir, center_dir));
                        Float inv_det = dr::select(dr::isnan(coh.inv_coherence_det(k)), 0.0f, coh.inv_coherence_det(k));
                        Float angular_coh = dr::exp(-0.5f * angle_offset * inv_det * angle_offset);
                        angular_coh = dr::select(dr::isnan(angular_coh), 0.0f, angular_coh);
                        // std::cout << "l:" << lobe << ", angular:" << angular_coh << std::endl;

                        auto r = lobes_result * colour * angular_coh;

                        result += Spectrum(r);
                    }

                    // // evaluate microfacet distribution considering the
                    // internal
                    // // shading frame
                    // Vector3f center_dir;
                    // Mask lobe_active;
                    // std::tie(center_dir, lobe_active) =
                    // grating.diffract(si.wi, lobe, wl);

                    // // microfacet distribution is symmetric along the
                    // z-vector => operate in local frame Frame3f
                    // center_dir_frame(center_dir); Float D =
                    // distr.eval(center_dir_frame.to_local(wo));

                    // active &= (D != 0.f);

                    // // Evaluate Smith's shadow-masking function
                    // Float G = distr.G(si.wi, wo, H);

                    // // Evaluate the full microfacet model (except Fresnel)
                    // UnpolarizedSpectrum lobe_result =
                    //     D * G / (4.f * Frame3f::cos_theta(si.wi));
                }
            }
            // Evaluate the Fresnel factor
            dr::Complex<UnpolarizedSpectrum> eta_c(m_eta->eval(si, active),
                                                   m_k->eval(si, active));

            Spectrum F;
            if constexpr (is_polarized_v<Spectrum>) {
                /* Due to the coordinate system rotations for
                polarization-aware pBSDFs below we need to know
                the propagation direction of light. In the
                following, light arrives along `-wo_hat` and
                leaves along
                `+wi_hat`. */
                Vector3f wo_hat =
                             ctx.mode == TransportMode::Radiance ? wo : si.wi,
                         wi_hat =
                             ctx.mode == TransportMode::Radiance ? si.wi : wo;

                // Mueller matrix for specular reflection.
                F = mueller::specular_reflection(
                    UnpolarizedSpectrum(dot(wo_hat, H)), eta_c);

                /* The Stokes reference frame vector of this matrix
                lies
                perpendicular to the plane of reflection. */
                Vector3f s_axis_in  = dr::cross(H, -wo_hat);
                Vector3f s_axis_out = dr::cross(H, wi_hat);

                // Singularity when the input & output are collinear with the
                // normal
                Mask collinear = dr::all(s_axis_in == Vector3f(0));
                s_axis_in      = dr::select(collinear, Vector3f(1, 0, 0),
                                            dr::normalize(s_axis_in));
                s_axis_out     = dr::select(collinear, Vector3f(1, 0, 0),
                                            dr::normalize(s_axis_out));

                /* Rotate in/out reference vector of F s.t. it aligns
                with
                the implicit Stokes bases of -wo_hat & wi_hat. */
                F = mueller::rotate_mueller_basis(
                    F, -wo_hat, s_axis_in, mueller::stokes_basis(-wo_hat),
                    wi_hat, s_axis_out, mueller::stokes_basis(wi_hat));
            } else {
                F = fresnel_conductor(UnpolarizedSpectrum(dr::dot(si.wi, H)),
                                      eta_c);
            }

            if (m_specular_reflectance)
                result *= m_specular_reflectance->eval(si);

            return F * result;

        } else {
            UnpolarizedSpectrum result(0.0);
            auto wavelengths = si.wavelengths;

            auto a =
                2 * dr::sqrt(m_alpha_u->eval_1(si) * m_alpha_v->eval_1(si));

            // exhaustive search of the lobes
            for (int lx = -((int) m_lobes) / 2; lx < (int) m_lobes / 2 + 1;
                 lx++) {
                for (int ly = -((int) m_lobes) / 2; ly < (int) m_lobes / 2 + 1;
                     ly++) {
                    Vector2i lobe(lx, ly);

                    for (int i = 0; i < dr::size_v<decltype(wavelengths)>;
                         i++) {
                        auto wl = wavelengths[i];
                        Float k = dr::TwoPi<Float> / (wl * 1e-3f);

                        Float lobe_intensity =
                            grating.lobe_intensity(lobe, si.wi, wl * 1e-3f);

                        Vector3f center_dir;
                        Mask lobe_active;
                        std::tie(center_dir, lobe_active) =
                            grating.diffract(si.wi, lobe, wl * 1e-3f);

                        // angular coherence between the center direction and the reflected dir
                        // TODO: admit anisotropic coherence information
                        Coherence3f coh(m_coherence, 1.0f);
                        Float angle_offset = dr::abs(dr::unit_angle(reflection_dir, center_dir));
                        Float inv_det = dr::select(dr::isnan(coh.inv_coherence_det(k)), 0.0f, coh.inv_coherence_det(k));
                        Float angular_coh = dr::exp(-0.5f * angle_offset * inv_det * angle_offset);
                        angular_coh = dr::select(dr::isnan(angular_coh), 0.0f, angular_coh);

                        // std::cout << "angular_coh:" << angular_coh << std::endl;

                        Float lobes_result = dr::select(
                            lobe_active &
                                dr::abs(dr::unit_angle(center_dir, wo)) < a,
                            lobe_intensity * angular_coh, 0.0);

                        result[i] += lobes_result;
                    }

                    // // evaluate microfacet distribution considering the
                    // internal
                    // // shading frame
                    // Vector3f center_dir;
                    // Mask lobe_active;
                    // std::tie(center_dir, lobe_active) =
                    // grating.diffract(si.wi, lobe, wl);

                    // // microfacet distribution is symmetric along the
                    // z-vector => operate in local frame Frame3f
                    // center_dir_frame(center_dir); Float D =
                    // distr.eval(center_dir_frame.to_local(wo));

                    // active &= (D != 0.f);

                    // // Evaluate Smith's shadow-masking function
                    // Float G = distr.G(si.wi, wo, H);

                    // // Evaluate the full microfacet model (except Fresnel)
                    // UnpolarizedSpectrum lobe_result =
                    //     D * G / (4.f * Frame3f::cos_theta(si.wi));
                }
            }
            // Evaluate the Fresnel factor
            dr::Complex<UnpolarizedSpectrum> eta_c(m_eta->eval(si, active),
                                                   m_k->eval(si, active));

            Spectrum F;
            if constexpr (is_polarized_v<Spectrum>) {
                /* Due to the coordinate system rotations for
                polarization-aware pBSDFs below we need to know
                the propagation direction of light. In the
                following, light arrives along `-wo_hat` and
                leaves along
                `+wi_hat`. */
                Vector3f wo_hat =
                             ctx.mode == TransportMode::Radiance ? wo : si.wi,
                         wi_hat =
                             ctx.mode == TransportMode::Radiance ? si.wi : wo;

                // Mueller matrix for specular reflection.
                F = mueller::specular_reflection(
                    UnpolarizedSpectrum(dot(wo_hat, H)), eta_c);

                /* The Stokes reference frame vector of this matrix
                lies
                perpendicular to the plane of reflection. */
                Vector3f s_axis_in  = dr::cross(H, -wo_hat);
                Vector3f s_axis_out = dr::cross(H, wi_hat);

                // Singularity when the input & output are collinear with the
                // normal
                Mask collinear = dr::all(s_axis_in == Vector3f(0));
                s_axis_in      = dr::select(collinear, Vector3f(1, 0, 0),
                                            dr::normalize(s_axis_in));
                s_axis_out     = dr::select(collinear, Vector3f(1, 0, 0),
                                            dr::normalize(s_axis_out));

                /* Rotate in/out reference vector of F s.t. it aligns
                with
                the implicit Stokes bases of -wo_hat & wi_hat. */
                F = mueller::rotate_mueller_basis(
                    F, -wo_hat, s_axis_in, mueller::stokes_basis(-wo_hat),
                    wi_hat, s_axis_out, mueller::stokes_basis(wi_hat));
            } else {
                F = fresnel_conductor(UnpolarizedSpectrum(dr::dot(si.wi, H)),
                                      eta_c);
            }

            if (m_specular_reflectance)
                result *= m_specular_reflectance->eval(si);

            return F * result;
        }
    }

    Float pdf(const BSDFContext &ctx, const SurfaceInteraction3f &si,
              const Vector3f &wo, Mask active) const override {
        MI_MASKED_FUNCTION(ProfilerPhase::BSDFEvaluate, active);

        Float cos_theta_i = Frame3f::cos_theta(si.wi),
              cos_theta_o = Frame3f::cos_theta(wo);

        // Calculate the half-direction vector
        Vector3f m = dr::normalize(wo + si.wi);

        /* Filter cases where the micro/macro-surface don't agree on the side.
           This logic is evaluated in smith_g1() called as part of the eval()
           and sample() methods and needs to be replicated in the probability
           density computation as well. */
        active &= cos_theta_i > 0.f && cos_theta_o > 0.f &&
                  dr::dot(si.wi, m) > 0.f && dr::dot(wo, m) > 0.f;

        if (unlikely(!ctx.is_enabled(BSDFFlags::GlossyReflection) ||
                     dr::none_or<false>(active)))
            return 0.f;

        /* Construct a microfacet distribution matching the
           roughness values at the current surface position. */
        MicrofacetDistribution distr(m_type, m_alpha_u->eval_1(si, active),
                                     m_alpha_v->eval_1(si, active),
                                     m_sample_visible);

        Float result;
        if (likely(m_sample_visible))
            result =
                distr.eval(m) * distr.smith_g1(si.wi, m) / (4.f * cos_theta_i);
        else
            result = distr.pdf(si.wi, m) / (4.f * dr::dot(wo, m));

        return dr::select(active, result, 0.f);
    }

    Float wbsdf_pdf(const BSDFContext &ctx, const SurfaceInteraction3f &si,
                    const Vector3f &wo, const PLTSamplePhaseData3f &sd,
                    Mask active) const override {
        MI_MASKED_FUNCTION(ProfilerPhase::BSDFEvaluate, active);

        // instantiate grating model
        DiffractionGrating3f grating(
            m_grating_angle->eval_1(si),
            Vector2f(
                m_inv_period_x->eval_1(si, active), 
                m_inv_period_y->eval_1(si, active)),
            m_height->eval_1(si, active), 
            m_lobes, 
            m_lobe_type,
            m_multiplier->eval_1(si, active), 
            si.uv);

        Float k;
        if constexpr (is_spectral_v<Spectrum>) {
            k = dr::TwoPi<Float> / (si.wavelengths[0] * 1e-3f);
        } else {
            k = dr::TwoPi<Float> / (sd.sampling_wavelengths[0] * 1e-3f);
        }

        return grating.alpha(si.wi, k);
    }

    std::pair<Spectrum, Float> eval_pdf(const BSDFContext &ctx,
                                        const SurfaceInteraction3f &si,
                                        const Vector3f &wo,
                                        Mask active) const override {
        MI_MASKED_FUNCTION(ProfilerPhase::BSDFEvaluate, active);

        Float cos_theta_i = Frame3f::cos_theta(si.wi),
              cos_theta_o = Frame3f::cos_theta(wo);

        // Calculate the half-direction vector
        Vector3f H = dr::normalize(wo + si.wi);

        /* Filter cases where the micro/macro-surface don't agree on the side.
           This logic is evaluated in smith_g1() called as part of the eval()
           and sample() methods and needs to be replicated in the probability
           density computation as well. */
        active &= cos_theta_i > 0.f && cos_theta_o > 0.f &&
                  dr::dot(si.wi, H) > 0.f && dr::dot(wo, H) > 0.f;

        if (unlikely(!ctx.is_enabled(BSDFFlags::GlossyReflection) ||
                     dr::none_or<false>(active)))
            return { 0.f, 0.f };

        /* Construct a microfacet distribution matching the
           roughness values at the current surface position. */
        MicrofacetDistribution distr(m_type, m_alpha_u->eval_1(si, active),
                                     m_alpha_v->eval_1(si, active),
                                     m_sample_visible);

        // Evaluate the microfacet normal distribution
        Float D = distr.eval(H);

        active &= D != 0.f;

        // Evaluate Smith's shadow-masking function
        Float smith_g1_wi = distr.smith_g1(si.wi, H);
        Float G           = smith_g1_wi * distr.smith_g1(wo, H);

        // Evaluate the full microfacet model (except Fresnel)
        UnpolarizedSpectrum value = D * G / (4.f * Frame3f::cos_theta(si.wi));

        // Evaluate the Fresnel factor
        dr::Complex<UnpolarizedSpectrum> eta_c(m_eta->eval(si, active),
                                               m_k->eval(si, active));

        Spectrum F;
        if constexpr (is_polarized_v<Spectrum>) {
            /* Due to the coordinate system rotations for polarization-aware
               pBSDFs below we need to know the propagation direction of light.
               In the following, light arrives along `-wo_hat` and leaves along
               `+wi_hat`. */
            Vector3f wo_hat = ctx.mode == TransportMode::Radiance ? wo : si.wi,
                     wi_hat = ctx.mode == TransportMode::Radiance ? si.wi : wo;

            // Mueller matrix for specular reflection.
            F = mueller::specular_reflection(
                UnpolarizedSpectrum(dot(wo_hat, H)), eta_c);

            /* The Stokes reference frame vector of this matrix lies
               perpendicular to the plane of reflection. */
            Vector3f s_axis_in  = dr::cross(H, -wo_hat);
            Vector3f s_axis_out = dr::cross(H, wi_hat);

            // Singularity when the input & output are collinear with the normal
            Mask collinear = dr::all(s_axis_in == Vector3f(0));
            s_axis_in      = dr::select(collinear, Vector3f(1, 0, 0),
                                        dr::normalize(s_axis_in));
            s_axis_out     = dr::select(collinear, Vector3f(1, 0, 0),
                                        dr::normalize(s_axis_out));

            /* Rotate in/out reference vector of F s.t. it aligns with the
               implicit Stokes bases of -wo_hat & wi_hat. */
            F = mueller::rotate_mueller_basis(
                F, -wo_hat, s_axis_in, mueller::stokes_basis(-wo_hat), wi_hat,
                s_axis_out, mueller::stokes_basis(wi_hat));
        } else {
            F = fresnel_conductor(UnpolarizedSpectrum(dr::dot(si.wi, H)),
                                  eta_c);
        }

        // If requested, include the specular reflectance component
        // if (m_specular_reflectance)
        //     value *= m_specular_reflectance->eval(si, active);

        Float pdf;
        if (likely(m_sample_visible))
            pdf = D * smith_g1_wi / (4.f * cos_theta_i);
        else
            pdf = distr.pdf(si.wi, H) / (4.f * dr::dot(wo, H));

        return { F * value & active, dr::select(active, pdf, 0.f) };
    }

    std::string to_string() const override {
        std::ostringstream oss;
        oss << "RoughGrating[" << std::endl
            << "  distribution = " << m_type << "," << std::endl
            << "  sample_visible = " << m_sample_visible << "," << std::endl
            << "  alpha_u = " << string::indent(m_alpha_u) << "," << std::endl
            << "  alpha_v = " << string::indent(m_alpha_v) << "," << std::endl;
        if (m_specular_reflectance)
            oss << "  specular_reflectance = "
                << string::indent(m_specular_reflectance) << "," << std::endl;
        oss << "  eta = " << string::indent(m_eta) << "," << std::endl
            << "  k = " << string::indent(m_k) << std::endl
            << "]";
        return oss.str();
    }

    MI_DECLARE_CLASS()
private:
    /// Specifies the type of microfacet distribution
    MicrofacetType m_type;
    /// Anisotropic roughness values
    ref<Texture> m_alpha_u, m_alpha_v;
    /// Importance sample the distribution of visible normals?
    bool m_sample_visible;
    /// Relative refractive index (real component)
    ref<Texture> m_eta;
    /// Relative refractive index (imaginary component).
    ref<Texture> m_k;
    /// Specular reflectance component
    ref<Texture> m_specular_reflectance;

    /// Physical grating model parameters

    /// @brief Period of the grating in um.
    ref<Texture> m_inv_period_x, m_inv_period_y;

    /// @brief Height of the grating in um.
    ref<Texture> m_height;

    /// @brief Angle of the grating.
    ref<Texture> m_grating_angle;

    /// @brief Type of grating phase function.
    DiffractionGratingType m_lobe_type;

    /// @brief Total number of diffraction lobes. Should be an odd number.
    uint32_t m_lobes;

    /// @brief Whether the grating rotates w.r.t the UV center (0.5, 0.5).
    bool m_radial;

    /// @brief Assume isotropic coherence information
    Float m_coherence;

    /// @brief Scaling factor for outgoing radiance.
    ref<Texture> m_multiplier;
};

MI_IMPLEMENT_CLASS_VARIANT(RoughGrating, BSDF)
MI_EXPORT_PLUGIN(RoughGrating, "Rough grating")
NAMESPACE_END(mitsuba)
