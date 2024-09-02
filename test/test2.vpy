import vapoursynth as vs
from vapoursynth import core
import mvsfunc as mvf
import havsfunc as haf
import vsutil
import vsTAAmbk as taa


class cfg:
    enable_dehalo = False
    enable_denoise = True
    enable_deband = True
    enable_AA = True
    enable_AI = False

    source_path = 'input2.mkv'

    # Placeholder for width and height
    width = None
    height = None

    # Parameters for each process
    dehalo_params = {
        'rx': 2.5,
        'ry': 2.5,
        'darkstr': 0.4,
        'format': vs.YUV420P10,
        'matrix_s': "709"
    }
    
    deband_params = {
        'output_depth': 16,
        'ref_thr': 0.55,
        'ref_elast': 1.6,
        'planes': [0, 1, 2]
    }
    
    antialiasing_params = {
        'field': 1,
        'mthresh': 10,
        'lthresh': 20,
        'vthresh': 20,
        'maxd': 24,
        'nt': 50
    }

configure = cfg()

def generate_line_mask_uv(clip):
    clipU = core.std.ShufflePlanes(clip, 1, vs.GRAY)
    clipV = core.std.ShufflePlanes(clip, 2, vs.GRAY)

    maskU = core.std.Prewitt(clipU, planes=[0], scale=9)
    maskV = core.std.Prewitt(clipV, planes=[0], scale=11)

    maskMerge = core.akarin.Expr([maskU, maskV], expr="x y max")

    threshold = 75
    thresholded_mask = core.std.Binarize(maskMerge, threshold=threshold)

    open_kernel = [1, 1, 1, 1, 1,
                1, 1, 1, 1, 1,
                1, 1, 1, 1, 1,
                1, 1, 1, 1, 1,
                1, 1, 1, 1, 1]

    opened_mask = core.std.Convolution(thresholded_mask, matrix=open_kernel)

    close_kernel = [1, 1, 1, 1, 1,
                    1, 1, 1, 1, 1,
                    1, 1, 1, 1, 1,
                    1, 1, 1, 1, 1,
                    1, 1, 1, 1, 1]

    cleaned_mask = core.std.Convolution(opened_mask, matrix=close_kernel)
    
    return cleaned_mask

def generate_line_mask_y(clip):
    clipY = vsutil.get_y(clip)

    maskY = core.std.Prewitt(clipY, planes=[0], scale=0.1)

    maskMerge = maskY

    threshold = 255
    thresholded_mask = core.std.Binarize(maskMerge, threshold=threshold)

    open_kernel = [1, 1, 1, 1, 1,
                1, 1, 1, 1, 1,
                1, 1, 1, 1, 1,
                1, 1, 1, 1, 1,
                1, 1, 1, 1, 1]

    opened_mask = core.std.Convolution(thresholded_mask, matrix=open_kernel)

    close_kernel = [1, 1, 1, 1, 1,
                    1, 1, 1, 1, 1,
                    1, 1, 1, 1, 1,
                    1, 1, 1, 1, 1,
                    1, 1, 1, 1, 1]

    cleaned_mask = core.std.Convolution(opened_mask, matrix=close_kernel)
    
    cleaned_mask = cleaned_mask.std.Inflate()
    
    cleaned_mask = cleaned_mask.std.Deflate()
    cleaned_mask = cleaned_mask.std.Deflate()
    cleaned_mask = cleaned_mask.std.Deflate()
    
    ret = core.akarin.Expr(cleaned_mask, "x 3 /")
    
    return ret

def load_source(filepath):
    """Loads and resizes the video source into 16bit"""
    clip = core.lsmas.LWLibavSource(filepath)
    if configure.width is None or configure.height is None:
        configure.width = clip.width
        configure.height = clip.height
    return  clip

def dehalo(clip):
    """Applies a dehalo filter to reduce halo artifacts."""
    params = configure.dehalo_params
    luma = vsutil.get_y(clip)
    l_mask = haf.FineDehalo(luma, showmask=4)
    mask_outer = vsutil.iterate(l_mask, core.std.Maximum, 2).std.Inflate()
    mask_inner = vsutil.iterate(mask_outer, core.std.Minimum, 3)
    r_mask = core.akarin.Expr([mask_outer, mask_inner], 'x y -')
    dering = haf.DeHalo_alpha(clp=clip, rx=params['rx'], ry=params['ry'], darkstr=params['darkstr'])
    dering_merged = core.std.MaskedMerge(clip, dering, r_mask)
    dering_merged = mvf.LimitFilter(dering_merged, clip, thr=3.0, elast=4.0)
    dehalod = core.resize.Bicubic(clip=dering_merged, width=configure.width, height=configure.height, format=params['format'], matrix_s=params['matrix_s'])
    return dehalod

def deband(clip, ref_clip):
    """Reduces banding artifacts with f3kdb debanding."""
    params = configure.deband_params
    debanded = core.neo_f3kdb.Deband(clip, 12, 72, 48, 48, 0, 0, output_depth=params['output_depth']).neo_f3kdb.Deband(24, 64, 32, 32, 0, 0, output_depth=params['output_depth'])
    return mvf.LimitFilter(debanded, ref_clip, thr=params['ref_thr'], elast=params['ref_elast'], planes=params['planes'])

def antialiasing(clip):
    """Applies anti-aliasing to improve edge smoothness."""
    # params = configure.antialiasing_params
    clipY = core.std.ShufflePlanes(clip, 0, vs.GRAY)
    # aa_clipY = core.eedi2.EEDI2(clipY, field=params['field'], mthresh=params['mthresh'], lthresh=params['lthresh'], vthresh=params['vthresh'], maxd=params['maxd'], nt=params['nt'])
    # aa_clipY = core.fmtc.resample(aa_clipY, configure.width, configure.height, 0, -0.5).std.Transpose()
    # aa_clipY = core.eedi2.EEDI2(aa_clipY, field=params['field'], mthresh=params['mthresh'], lthresh=params['lthresh'], vthresh=params['vthresh'], maxd=params['maxd'], nt=params['nt'])
    # aa_clipY = core.fmtc.resample(aa_clipY, configure.height, configure.width, 0, -0.5).std.Transpose()
    aa_clip = taa.TAAmbk(clip, aatype=1, aatypeu=None, aatypev=None, preaa=0, strength=0, cycle=0, mtype=1, mclip=None,
           mthr=None, mthr2=None, mlthresh=None, mpand=(1, 0), txtmask=0, txtfade=0, thin=0, dark=0.0, sharp=0,
           aarepair=0, postaa=None, src=None, stabilize=0, down8=True, showmask=0, opencl=False, opencl_device=0)
    aa_clipY = core.std.ShufflePlanes(aa_clip, 0, vs.GRAY)
    return core.rgvs.Repair(aa_clipY, clipY, 2)


def merge_aa_deband(aaedY, debanded):
    """Merges anti-aliased and debanded clips."""
    dbedY = core.std.ShufflePlanes(debanded, 0, vs.GRAY)
    mergedY = mvf.LimitFilter(dbedY, aaedY, thr=1.0, elast=1.5)
    merged = core.std.ShufflePlanes([mergedY, debanded], [0, 1, 2], vs.YUV)
    return core.resize.Bicubic(clip=merged, width=configure.width, height=configure.height, format=vs.YUV420P10, matrix_s="709")

def show_diff(clipA, clipB):
    '''Compare 2 Video Clips'''
    clipA = core.resize.Bicubic(clip=clipA, width=configure.width, height=configure.height, format=vs.YUV420P10, matrix_s="709")
    clipB = core.resize.Bicubic(clip=clipB, width=configure.width, height=configure.height, format=vs.YUV420P10, matrix_s="709")
    return core.std.MakeDiff(clipA, clipB)

def output(output_list):
    '''Set Output automatically'''
    for index, clip in enumerate(output_list):
        clip.set_output(index)

def main():
    cliporg = load_source(configure.source_path)
    clip1 = cliporg
    
    line_mask_uv = generate_line_mask_uv(clip1)
    line_mask_uv = core.resize.Bicubic(clip=line_mask_uv, width=configure.width, height=configure.height, format=vs.YUV420P16, matrix_s="709")
    
    cliporg = core.resize.Bicubic(clip=cliporg, width=configure.width, height=configure.height, format=vs.YUV420P10, matrix_s="709")
    cliporg = core.fmtc.bitdepth(cliporg, bits=16)
    
    clip1 = core.resize.Bicubic(clip=clip1, width=configure.width, height=configure.height, format=vs.YUV420P10, matrix_s="709")
    clip1 = core.fmtc.bitdepth(clip1, bits=16)
    pre_denoised = mvf.BM3D(clip1, sigma=3.0, profile1="fast")
    
    denoised = core.nlm_ispc.NLMeans(clip=cliporg, h=10.5, wmode=3, d=0)
    denoised = mvf.LimitFilter(denoised, clip1,  thr=3, elast=2)
    denoised = core.resize.Bicubic(clip=denoised, width=configure.width, height=configure.height, format=vs.YUV420P16, matrix_s="709")
    
    line_mask_y = generate_line_mask_y(denoised)
    line_mask_y = core.resize.Bicubic(clip=line_mask_y, width=configure.width, height=configure.height, format=vs.YUV420P16, matrix_s="709")
    
    line_mask = core.akarin.Expr([line_mask_y, line_mask_uv], expr="x y max")

    denoised = core.std.MaskedMerge(clipa = denoised, clipb=pre_denoised, mask = line_mask, first_plane=True)
    
    dbed = deband(denoised, denoised) if configure.enable_deband else denoised
    aaedY = antialiasing(denoised) if configure.enable_AA else vsutil.get_y(dbed)
    merged = merge_aa_deband(aaedY, dbed)
    dehalod = dehalo(merged) if configure.enable_dehalo else merged
    

    diff = show_diff(dehalod, clip1)
    
    outputs = [dehalod, merged, denoised, line_mask, line_mask_uv,line_mask_y, clip1, diff]
    
    output(outputs)

main()
