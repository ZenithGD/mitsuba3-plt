import mitsuba as mi
import drjit as dr

import numpy as np

from collections import namedtuple

from typing import List, Tuple, Sequence

from mitsuba.ad.integrators.common import ADIntegrator, mis_weight

class PLTIntegrator(ADIntegrator):

    
    def __init__(self, arg : mi.Properties):
        self.max_depth = arg.get("max_depth", def_value=16)
        self.rr_depth = arg.get("rr_depth", def_value=4)
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

        # hero wavelength
        wavelength = mi.sample_arbitrary_spectrum(sampler.next_1d(), 360, 830)

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
            active_next = (depth + 1 < self.max_depth) & si.is_valid() & ~is_emitter

            # 3. sample new direction with BSDF
            bsdf = si.bsdf(ray)
            sample_1 = sampler.next_1d()
            sample_2 = sampler.next_2d()

            bsdf_sample, bsdf_weight = bsdf.sample(
                bsdf_ctx, si, sample_1, sample_2)
             
            # get information of the sampled interaction and update ray
            ray = si.spawn_ray(si.to_world(bsdf_sample.wo))
            pdf = bsdf_sample.pdf
            path_pdf *= pdf
            α[active_next] *= bsdf_weight
            η[active_next] = bsdf_sample.eta
            
            # 4.4 update current vertex information for next iteration
            prev_si = si
            prev_bsdf_pdf = bsdf_sample.pdf
            prev_bsdf_delta = mi.has_flag(bsdf_sample.sampled_type, mi.BSDFFlags.Delta)

            depth[si.is_valid()] += 1
            
            # 6. Russian roulette path termination
            α_max = dr.max(α)
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
                bsdf_weight=bsdf_weight,
                is_emitter=is_emitter,
                last_nd_pdf=last_nd_pdf,
                active=active
            )

            bounce_buffer.write(bounce, i, active)

            # update last delta information
            last_nd_pdf = dr.select(prev_bsdf_delta, last_nd_pdf, pdf)

            active = active_next
            i += 1
        
        aovs[0] = α
        return bounce_buffer, wavelength, aovs

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

        # loop = mi.Loop(name="PLT Path tracer (solve phase)",
        #                state=lambda:(L, i, bounce_buffer))
        
        # loop.set_max_iterations(self.max_depth)

        i = mi.UInt32(0)

        while i < self.max_depth:

            # TODO: account for environment lights (distant sources)
            L += self.solve_replay_miss(mode, 
                scene, 
                sampler, 
                depth, 
                δL, δaovs, 
                state_in, active, 
                bounce_buffer, wavelength, i)

            # account for emissive geometry
            L += self.solve_replay_emissive(mode, 
                scene, 
                sampler, 
                depth, 
                δL, δaovs, 
                state_in, active, 
                bounce_buffer, wavelength, i)
            
            # # perform NEE for this bounce
            # L += self.solve_replay_NEE(mode, 
            #     scene, 
            #     sampler, 
            #     depth, 
            #     δL, δaovs, 
            #     state_in, active, 
            #     bounce_buffer, wavelength, i)

            # next bounce
            i += 1

        return (L, active, [], [])
    
    @dr.syntax
    def solve_replay_miss(self, 
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
        """Solve forward transport with PLT, accounting for subpaths that miss an
        emissive area light source.

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
        
        return mi.Spectrum(0.0)
    
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

        return mi.Spectrum(0.0)
    
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

        # Read bounce
        bounce = bounce_buffer.read(bounce_idx, bounce_idx > 0)
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

        mis_bsdf = dr.select(~bounce.is_emitter & (mi.UInt32(bounce_idx) > 0), mis_bsdf, 1)

        # Emitted intensity with MIS weight
        Lem = ds.emitter.eval(bounce.interaction, bounce.active & bounce.is_emitter) * mis_bsdf

        Li = self.replay_path(mode, 
            scene, 
            sampler, 
            depth, 
            δL, 
            δaovs, 
            state_in, 
            bounce.active,
            bounce_buffer,
            wavelength, 
            bounce_idx, 
            Lem)

        # return self.__measure(
        #     mode,
        #     scene, 
        #     sampler, 
        #     depth, 
        #     δL, 
        #     δaovs, 
        #     state_in, 
        #     bounce.active,
        #     bounce_buffer,
        #     wavelength,
        #     Li,
        #     bounce.rr_weight)

        return Li

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
                      wavelength : mi.Float,
                      bounce_idx : mi.UInt32,
                      Lem : mi.Spectrum) -> mi.Spectrum:
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
        
        Li = Lem
        bsdf_ctx = mi.BSDFContext()
        i = mi.Int32(bounce_idx - 1) 
        α = mi.Spectrum(1.0)

        while i >= 0:

            bidx = mi.UInt32(i) 

            # Read subpath bounce
            bounce = bounce_buffer[bidx]

            # Propagate beam and evolve distribution (TODO)

            # Get BSDF and update path contribution
            evaluate_bounce = ~bounce.interaction.shape.is_emitter() \
                & bounce.interaction.is_valid() \
                & ~mi.has_flag(bounce.bsdf_flags, mi.BSDFFlags.Delta)
            
            bsdf = bounce.interaction.bsdf()
            α = dr.select(bounce.active, 
                           α * bounce.bsdf_weight, #bsdf.eval(bsdf_ctx, bounce.interaction, bounce.wo, bounce.active & evaluate_bounce), 
                           α)

            # next bounce in forward path
            i -= 1

        Li *= α

        return Li 

    @dr.syntax
    def __measure(self,
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
                      Li : mi.Spectrum,
                      path_mod : mi.Float) -> mi.Spectrum:
        
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