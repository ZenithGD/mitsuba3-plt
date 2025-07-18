import mitsuba as mi
import drjit as dr

import numpy as np

from collections import namedtuple

from typing import List, Tuple, Sequence
from scripts.utils import spec_fma, spec_prod, spec_add

from mitsuba.ad.integrators.common import ADIntegrator, mis_weight

class PLTIntegrator(ADIntegrator):

    
    def __init__(self, arg : mi.Properties):
        """Initialize the PLT integrator. Performs a sample-solve approach to solve
        wave transport sampling rays from the detector and then evolving
        the distribution from the light source to the sensor.

        Args:
            arg (mi.Properties): The properties passed into the integrator.
            It accepts the following properties:

            - `max_depth` (default: 16): The maximum number of bounces.
            - `rr_depth` (default: 4): The depth at which to start performing
                Russian Roulette path termination.
            - `emissive_sourcing_area` (default: 1E-4): The solid angle of the 
                generalized ray sourced by emissive geometry (area sources)
            - `distant_sourcing_area` (default: 1E-7): The solid angle of the 
                generalized ray sourced by a distant source (environment maps or
                directional sources)
            - `max_angular_spread` (default: 1E-7): The max solid angle of the propagated
                generalized ray.
        """
        # path tracing props
        self.max_depth = arg.get("max_depth", def_value=16)
        self.rr_depth = arg.get("rr_depth", def_value=4)

        self.sample_pass_weight = arg.get("sample_pass_weight", def_value=False)

        # light coherence properties
        self.emissive_sourcing_area = arg.get("emissive_sourcing_area", def_value=1E-4)
        self.distant_sourcing_area = arg.get("distant_sourcing_area", def_value=1E-7)
        self.max_angular_spread = arg.get("max_angular_spread", def_value=1E-7)

        super().__init__(arg)

    @dr.syntax
    def plt_sample_phase(self, 
                         mode : dr.ADMode, 
                         scene : mi.Scene, 
                         sampler : mi.Sampler, 
                         ray : mi.Ray3f, 
                         depth : mi.UInt32,
                         δL : mi.Spectrum,
                         δaovs : List[mi.Float],
                         state_in : any,
                         active : mi.Bool) -> Tuple[dr.Local[mi.BounceData3f], mi.Float, List[mi.Float]]:
        
        # define internal state
        bounce_buffer : dr.Local[mi.BounceData3f] = dr.alloc_local(mi.BounceData3f, self.max_depth)

        # sampling wavelengths
        scale_wl = (mi.MI_CIE_MAX - 150 - mi.MI_CIE_MIN) + mi.MI_CIE_MIN
        (λs1, λs2, λs3, λs4) = [ sampler.next_1d() * scale_wl for i in range(4) ]
        if mi.is_spectral:
            wavelengths = mi.UnpolarizedSpectrum(λs1,λs2,λs3,λs4)
        else:
            wavelengths = mi.UnpolarizedSpectrum(λs1,λs2,λs3)

        # prepare loop state
        i = mi.UInt32(0)
        ray = mi.Ray3f(dr.detach(ray))
        α = mi.Spectrum(1.0)
        η = mi.Float(1.0)
        path_pdf = mi.Float(1.0)
        depth = mi.UInt32(0)
        active = mi.Bool(True)
        
        # cached information from previous bounce
        prev_si = dr.zeros(mi.SurfaceInteraction3f)
        prev_bsdf_pdf = mi.Float(1.0)
        prev_bsdf_delta = mi.Bool(True)
        last_nd_pdf = mi.Float(1.0)
        bsdf_ctx = mi.BSDFContext()

        # Additional debug info
        aovs = [ mi.Spectrum(0) ]

        opl = mi.Float(0.0)

        while active:

            # 1. Intersect with scene geometry
            si = scene.ray_intersect(
                ray,
                ray_flags=mi.RayFlags.All,
                coherent=(depth == 0))
            
            # 2. check if intersected geometry is an emitter,
            # terminate path if a light source is found and store its distribution.
            is_emitter = si.shape.is_emitter()

            # continue iteration?
            active_next = (depth + 1 < self.max_depth) & si.is_valid() # & ~is_emitter

            # 3. sample new direction with BSDF
            bsdf = si.bsdf(ray)
            sample_1 = sampler.next_1d()
            sample_2 = sampler.next_2d()
            lobe_sample_2 = sampler.next_2d()

            sd, bsdf_weight = bsdf.wbsdf_sample(
                bsdf_ctx, si, sample_1, sample_2, lobe_sample_2)

            bsdf_sample = sd.bsdf_sample

            # get information of the sampled interaction and update ray
            ray = si.spawn_ray(si.to_world(bsdf_sample.wo))
            pdf = bsdf_sample.pdf
            path_pdf *= pdf
            α[active_next] = bsdf_weight.L * α[active_next]
            η[active_next] = bsdf_sample.eta
            
            # 4.4 update current vertex information for next iteration
            prev_si = si
            prev_bsdf_pdf = bsdf_sample.pdf
            prev_bsdf_delta = mi.has_flag(bsdf_sample.sampled_type, mi.BSDFFlags.Delta)

            depth[si.is_valid()] += 1
            
            # 6. Russian roulette path termination
            α_max = dr.max(mi.unpolarized_spectrum(α))
            active_next &= α_max != 0
            rr_prob = dr.minimum(α_max * dr.sqr(η), 0.95)
            rr_active = depth >= self.rr_depth

            # Russian roulette correction
            rcp_thp = dr.rcp(dr.detach(rr_prob))
            α[rr_active] *= rcp_thp
            rr_continue = sampler.next_1d() < rr_prob
            active_next &= ~rr_active | rr_continue

            # store bounce data
            bounce = mi.BounceData3f(
                id=i,
                interaction=si,
                wi=-ray.d,
                wo=bsdf_sample.wo,
                bsdf_flags=bsdf_sample.sampled_type,
                rr_thp=rcp_thp,
                throughput=α,
                bsdf_weight=bsdf_weight.L,
                is_emitter=is_emitter,
                last_nd_pdf=last_nd_pdf,
                sampled_lobe=sd.diffraction_lobe,
                sampling_wavelengths=wavelengths,
                active=active
            )

            bounce_buffer.write(bounce, i, active)

            # update last delta information
            last_nd_pdf = dr.select(prev_bsdf_delta, last_nd_pdf, pdf)

            active = active_next
            i += 1
        
        aovs[0] = α
        return bounce_buffer, wavelengths, aovs

    @dr.syntax
    def plt_solve_phase(self,
                        mode : dr.ADMode, 
                        scene : mi.Scene, 
                        sampler : mi.Sampler,
                        depth : mi.UInt32,
                        δL : mi.Spectrum,
                        δaovs : List[mi.Float],
                        state_in : any,
                        active : mi.Bool,
                        bounce_buffer : dr.Local[mi.BounceData3f],
                        wavelength : mi.Float) -> Tuple[mi.Spectrum, mi.Bool, Sequence[mi.Float], List[mi.Float]]:
        
        # Solve data
        L = mi.Spectrum(0.0)

        i = mi.UInt32(0)

        while i < self.max_depth:
            # Accumulate both contributions
            # They are already weighted by their respective MIS weight

            # account for emissive geometry by replaying subpath
            L = spec_add(L, self.solve_replay_emissive(mode, 
                scene, 
                sampler, 
                depth, 
                δL, δaovs, 
                state_in, active, 
                bounce_buffer, wavelength, i))
            
            # perform NEE for this bounce
            L = spec_add(L, self.solve_replay_NEE(mode, 
                scene, 
                sampler, 
                depth, 
                δL, δaovs, 
                state_in, active, 
                bounce_buffer, wavelength, i))

            L = mi.Spectrum(L)
            
            # next bounce
            i += 1

        return (L, active, [], [])
    
    @dr.syntax
    def solve_replay_NEE(self, 
                           mode : dr.ADMode, 
                           scene : mi.Scene, 
                           sampler : mi.Sampler,
                           depth : mi.UInt32,
                           δL : mi.Spectrum,
                           δaovs : List[mi.Float],
                           state_in : any,
                           active : mi.Bool,
                           bounce_buffer : dr.Local[mi.BounceData3f],
                           wavelength : mi.Float,
                           bounce_idx : mi.UInt32) -> mi.Spectrum:
        """Solve forward transport with PLT, accounting for subpaths that end
        on geometry with non-emissive materials.

        Args:
            mode (dr.ADMode): The differentiation mode
            scene (mi.Scene): The scene to render
            sampler (mi.Sampler): The sampler
            depth (mi.UInt32): The initial depth of the path (usually 0)
            state_in (any): Input state
            active (mi.Bool): Active paths for SIMD modes
            bounce_buffer (dr.Local[mi.BounceData3f]): List of bounces from a backwards
            sampled path.
            wavelength (mi.Float): The hero wavelength of the path

        Returns:
            mi.Spectrum: The contribution of this light path
        """
        
        # assume very coherent light from the start. 
        # the coherence properties should come from the emitter
        coherence = mi.Coherence3f(mi.Float(1e-18), mi.Float(0.0))

        bounce = bounce_buffer.read(bounce_idx)
        bsdf_ctx = mi.BSDFContext()
        si = bounce.interaction

        active_em = bounce.active & mi.has_flag(bounce.bsdf_flags, mi.BSDFFlags.Smooth);

        ds, em_weight = scene.sample_emitter_direction(si, sampler.next_2d(), True, active_em)

        # enable AD and recompute contribution of the emitter sample
        with dr.resume_grad():
            # direction towards the emitter
            ds.d = dr.normalize(ds.p - si.p)

            em_val = scene.eval_emitter_direction(si, ds, active_em)
            em_weight = dr.select(ds.pdf != 0.0, em_val / ds.pdf, 0)

        wo = si.to_local(ds.d)

        # no need to recompute UV coordinates again, just get the bsdf
        bsdf = si.bsdf()
        sd = mi.PLTSamplePhaseData3f(
            dr.zeros(mi.BSDFSample3f), 
            bounce.sampled_lobe, 
            mi.Vector3f(0.0), 
            mi.Coherence3f(mi.Float(0.0), mi.Float(0.0)),
            bounce.sampling_wavelengths)
        bsdf_val = bsdf.wbsdf_eval(bsdf_ctx, si, wo, sd, bounce.active)
        bsdf_pdf = bsdf.wbsdf_pdf(bsdf_ctx, si, wo, sd, bounce.active)
        bsdf_val = bsdf_val.L

        mis_em = dr.select(ds.delta, 1.0, mis_weight(ds.pdf, bsdf_pdf))

        α = self.replay_path(mode, 
            scene, 
            sampler, 
            depth, 
            δL, 
            δaovs, 
            state_in, 
            bounce.active,
            bounce_buffer,
            coherence,
            wavelength, 
            bounce_idx)

        return em_weight * mis_em * bsdf_val * α
    
    # @dr.syntax
    # def source_PLT_beam(self,  
    #                     mode : dr.ADMode, 
    #                     scene : mi.Scene, 
    #                     Le : mi.Spectrum,
    #                     dir : mi.Vector3f,
    #                     is_environment : mi.Bool,
    #                     active : mi.Bool):

    #     beam = dr.select()

    
    @dr.syntax    
    def solve_replay_emissive(self, 
                                mode : dr.ADMode, 
                                scene : mi.Scene, 
                                sampler : mi.Sampler,
                                depth : mi.UInt32,
                                δL : mi.Spectrum,
                                δaovs : List[mi.Float],
                                state_in : any,
                                active : mi.Bool,
                                bounce_buffer : dr.Local[mi.BounceData3f],
                                wavelength : mi.Float,
                                bounce_idx : mi.UInt32) -> mi.Spectrum:
        """Solve forward transport with PLT, accounting for subpaths that end
        on geometry with non-emissive materials.

        Args:
            mode (dr.ADMode): The differentiation mode
            scene (mi.Scene): The scene to render
            sampler (mi.Sampler): The sampler
            depth (mi.UInt32): The initial depth of the path (usually 0)
            state_in (any): Input state
            active (mi.Bool): Active paths for SIMD modes
            bounce_buffer (dr.Local[mi.BounceData3f]): List of bounces from a backwards
            sampled path.
            wavelength (mi.Float): The hero wavelength of the path

        Returns:
            mi.Spectrum: The contribution of this light path
        """

        # assume very coherent light from the start. 
        # the coherence properties should come from the emitter
        coherence = mi.Coherence3f(mi.Float(1e-18), mi.Float(0.0))

        # 1. Read bounce and prepare light source info
        # Read bounce
        bounce = bounce_buffer.read(bounce_idx)
        prev_bounce = bounce_buffer.read(bounce_idx - 1, bounce_idx > 0)

        # Prepare information to evaluate emissive contribution
        prev_si = dr.select(
            bounce_idx > 0, 
            prev_bounce.interaction, 
            dr.zeros(mi.SurfaceInteraction3f))
        prev_bsdf_delta = dr.select(
            bounce_idx > 0, 
            mi.has_flag(prev_bounce.bsdf_flags, mi.BSDFFlags.Delta), 
            mi.Bool(True))
        
        ds = mi.DirectionSample3f(scene, bounce.interaction, prev_si)
        mis_bsdf = mis_weight(
            bounce.last_nd_pdf,
            scene.pdf_emitter_direction(prev_si, ds, ~prev_bsdf_delta)
        )

        # Emitted intensity with MIS weight
        Lem = mis_bsdf * ds.emitter.eval(bounce.interaction)

        # 2. Source ray based on hit type (env/area)
        is_environment = ds.emitter.is_environment()

        # 3. Replay path and evolve light distribution 
        α = self.replay_path(mode, 
            scene, 
            sampler, 
            depth, 
            δL, 
            δaovs, 
            state_in, 
            bounce.active,
            bounce_buffer,
            coherence,
            wavelength, 
            bounce_idx)
            
        Li = α * Lem

        # 4. Measure beam at sensor

        return self.measure(
            mode,
            scene, 
            sampler, 
            depth, 
            δL, 
            δaovs, 
            state_in, 
            bounce.active,
            bounce_buffer,
            wavelength,
            Li)

    @dr.syntax
    def replay_path(self,
                      mode : dr.ADMode, 
                      scene : mi.Scene, 
                      sampler : mi.Sampler,
                      depth : mi.UInt32,
                      δL : mi.Spectrum,
                      δaovs : List[mi.Float],
                      state_in : any,
                      active : mi.Bool,
                      bounce_buffer : dr.Local[mi.BounceData3f],
                      coherence : mi.Coherence3f,
                      wavelength : mi.Float,
                      bounce_idx : mi.UInt32) -> mi.Spectrum:
        """Compute the weight of this path and compute forward coherence transport
        The initial light distribution Lem will be evolved towards the sensor.

        Args:
            mode (dr.ADMode): The differentiation mode
            scene (mi.Scene): The scene to render
            sampler (mi.Sampler): The sampler
            depth (mi.UInt32): The initial depth of the path (usually 0)
            state_in (any): Input state
            active (mi.Bool): Active paths for SIMD modes
            bounce_buffer (dr.Local[mi.BounceData3f]): List of bounces from a backwards
            sampled path.
            wavelength (mi.Float): The hero wavelength of the path

        Returns:
            mi.Spectrum: The weight of this light path
        """
        bsdf_ctx = mi.BSDFContext(mi.TransportMode.Radiance)
        i = mi.Int32(bounce_idx - 1) 
        α = mi.Spectrum(1.0)

        while i >= 0:

            bidx = mi.UInt32(i) 

            # Read subpath bounce
            bounce = bounce_buffer[bidx]
            
            # propagate
            coherence.propagate(
                bounce.interaction.t, 
                bounce.interaction.is_valid())

            # Propagate beam and evolve distribution (TODO)
            bsdf = bounce.interaction.bsdf()

            # A: Correct way
            sd = mi.PLTSamplePhaseData3f(
                dr.zeros(mi.BSDFSample3f), 
                bounce.sampled_lobe, 
                mi.Vector3f(0.0), 
                coherence, 
                bounce.sampling_wavelengths)
            α[bounce.active] = bsdf.wbsdf_weight(bsdf_ctx, bounce.interaction, bounce.wo, sd).L * α[bounce.active]

            # B: Debug using information from sample pass
            #α[bounce.active] = bounce.bsdf_weight * α[bounce.active]
            
            # next bounce in forward path
            i -= 1

        return α

    @dr.syntax
    def measure(self,
                      mode : dr.ADMode, 
                      scene : mi.Scene, 
                      sampler : mi.Sampler,
                      depth : mi.UInt32,
                      δL : mi.Spectrum,
                      δaovs : List[mi.Float],
                      state_in : any,
                      active : mi.Bool,
                      bounce_buffer : dr.Local[mi.BounceData3f],
                      wavelength : mi.Float,
                      Li : mi.Spectrum) -> mi.Spectrum:
        
        # Propagate beam to camera (TODO)
        
        return Li
    
    @dr.syntax
    def sample(self,
               mode : dr.ADMode, 
               scene : mi.Scene, 
               sampler : mi.Sampler, 
               ray : mi.Ray3f, 
               depth : mi.UInt32,
               δL : mi.Spectrum,
               δaovs : List[mi.Float],
               state_in : any,
               active : mi.Bool) -> Tuple[mi.Spectrum, mi.Bool, Sequence[mi.Float], List[mi.Float]]:
        
        # Sample a path from the sensor towards a light source
        bounce_buffer, wavelength, sample_aovs = self.plt_sample_phase(
            mode, 
            scene, 
            sampler, 
            ray, 
            depth, 
            δL, 
            δaovs, 
            state_in, 
            active)

        # Solve forward PLT wave transport
        result, active, solve_aovs, state_out = self.plt_solve_phase(
            mode, 
            scene, 
            sampler, 
            depth, 
            δL, 
            δaovs, 
            state_in, 
            active, 
            bounce_buffer,
            wavelength)
    
        return (result, active, [], state_out)
    
mi.register_integrator("plt", lambda props: PLTIntegrator(props))