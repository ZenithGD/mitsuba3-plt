import mitsuba as mi
import drjit as dr

import numpy as np

from typing import List, Tuple, Sequence

from mitsuba.ad.integrators.common import ADIntegrator, mis_weight

class MISPathIntegrator(ADIntegrator):
    
    def __init__(self, arg : mi.Properties):
        
        self.max_depth = arg.get("max_depth", def_value=16)
        self.rr_depth = arg.get("rr_depth", def_value=4)
        super().__init__(arg)

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
        
        # 1. configure loop state

        # copy data locally
        ray = mi.Ray3f(dr.detach(ray))
        α = mi.Spectrum(1.0)
        result = mi.Spectrum(0.0)
        η = mi.Float(1.0)
        depth = mi.UInt32(0)
        active = mi.Bool(True)

        # cached information from previous bounce
        prev_si = dr.zeros(mi.SurfaceInteraction3f)
        prev_bsdf_pdf = mi.Float(1.0)
        prev_bsdf_delta = mi.Bool(True)
        bsdf_ctx = mi.BSDFContext()
        
        # 2. Loop until termination
        while active:
            
            # 2.1 Intersect with scene geometry
            si = scene.ray_intersect(
                ray, 
                ray_flags= mi.RayFlags.All,
                coherent= depth == 0 )
            
            # 2.2 Direct emission
            ds = mi.DirectionSample3f(scene, si, prev_si)
            mis_bsdf = mis_weight(
                prev_bsdf_pdf,
                scene.pdf_emitter_direction(prev_si, ds, ~prev_bsdf_delta)
            )

            # add the direct emission term into the result
            #result += α * ds.emitter.eval(si) * mis_bsdf

            # continue iteration?
            is_emitter = si.shape.is_emitter()
            active_next = (depth + 1 < self.max_depth) & si.is_valid() & ~is_emitter

            # 2.3 Emitter sampling
            bsdf = si.bsdf(ray)
            active_em = active_next & mi.has_flag(bsdf.flags(), mi.BSDFFlags.Smooth);

            ds, em_weight = scene.sample_emitter_direction(si, sampler.next_2d(), True, active_em)
            active_em &= ds.pdf != 0.0
           
            # enable AD and recompute contribution of the emitter sample
            with dr.resume_grad():
                # direction towards the emitter
                ds.d = dr.normalize(ds.p - si.p)

                em_val = scene.eval_emitter_direction(si, ds, active_em)
                em_weight = dr.select(ds.pdf != 0.0, em_val / ds.pdf, 0)

            wo = si.to_local(ds.d)
            
            # evaluate BSDF with the emitter sampling direction 
            # and sample new direction
            sample_1 = sampler.next_1d()
            sample_2 = sampler.next_2d()

            bsdf_val, bsdf_pdf, bsdf_sample, bsdf_weight = bsdf.eval_pdf_sample(
                bsdf_ctx, si, wo, sample_1, sample_2)
            
            # compute MIS emitter sampling contribution and add to result
            # with delta interactions, only the bsdf term will contribute
            mis_em = dr.select(ds.delta, 1.0, mis_weight(ds.pdf, bsdf_pdf))

            result += α * bsdf_val * em_weight * mis_em

            # 2.5 BSDF sampling
            ray = si.spawn_ray(si.to_world(bsdf_sample.wo))

            with dr.resume_grad():
                ray = dr.detach(ray)

                wo_2 = si.to_local(ray.d)
                bsdf_val_2, bsdf_pdf_2 = bsdf.eval_pdf(bsdf_ctx, si, wo_2, active)
                bsdf_weight[bsdf_pdf_2 > 0.0] = bsdf_val_2 / dr.detach(bsdf_pdf_2)
            
            # update loop variables
            α *= bsdf_weight
            η *= bsdf_sample.eta

            # update current vertex information for next iteration
            prev_si = si
            prev_bsdf_pdf = bsdf_sample.pdf
            prev_bsdf_delta = mi.has_flag(bsdf_sample.sampled_type, mi.BSDFFlags.Delta)

            # 2.6 stopping criterion
            depth[si.is_valid()] += 1

            α_max = dr.max(α)
            active_next &= α_max != 0
            rr_prob = dr.minimum(α_max * dr.sqr(η), 0.95)
            rr_active = depth >= self.rr_depth

            α[rr_active] *= dr.rcp(dr.detach(rr_prob))
            rr_continue = sampler.next_1d() < rr_prob
            active_next &= ~rr_active | rr_continue

            active = active_next

        return (result, active, [], [])
    
mi.register_integrator("mispath", lambda props: MISPathIntegrator(props))