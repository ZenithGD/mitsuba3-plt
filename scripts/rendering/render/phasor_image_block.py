import mitsuba as mi
import drjit as dr

class PhasorImageBlock(mi.Object):

    def __init__(self, 
        size: mi.ScalarVector2u,
        offset: mi.ScalarPoint2i,
        channel_count: mi.ScalarUInt32,
        rfilter: mi.ReconstructionFilter,
        border: bool = False,
        normalize: bool = False,
        compensate: bool = False,
        warn_negative: bool = False,
        warn_invalid: bool = False 
    ):

        super().__init__()

        self.m_offset = offset
        self.m_size = size
        self.m_channel_count = channel_count


        self.m_rfilter = rfilter
        self.m_border = border
        self.m_border_size = 0 if self.m_rfilter is None else self.m_rfilter.border_size()
        self.m_data = None 

        if warn_negative and dr.is_jit_v:
            mi.Log(mi.LogLevel.Warning, "Border is disabled in JIT variants!")

        self.m_normalize = normalize
        self.m_compensate = compensate

        self.m_warn_negative = warn_negative
        self.m_warn_invalid = warn_invalid
        
        if warn_negative and dr.is_jit_v:
            mi.Log(mi.LogLevel.Warning, "Warn negative is disabled in JIT variants!")

        if warn_invalid and dr.is_jit_v:
            mi.Log(mi.LogLevel.Warning, "Warn invalid is disabled in JIT variants!")

        # initialize data
        self.clear()

    
    def clear(self):
        del self.m_data

        # determine shape tuple of the tensor
        size_ext = self.m_size + 2 * self.m_border_size
        flat_size = self.m_channel_count * dr.prod(size_ext)
        shape = tuple(list(size_ext) + [self.m_channel_count])

        # allocate tensor data
        self.m_data = mi.TensorXf(dr.zeros(mi.Complex2f, flat_size), )