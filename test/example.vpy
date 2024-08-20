from vapoursynth import core 

clip = core.bs.VideoSource('input.mkv')
clip = core.fmtc.bitdepth(clip, bits=16)
# def aa_process_eedi2(clip):
#     w = clip.width
#     h = clip.height
#     aa_clip = core.std.ShufflePlanes(clip, 0, vs.GRAY)
#     aa_clip = core.eedi2.EEDI2(aa_clip, field=1, mthresh=10, lthresh=20, vthresh=20, maxd=24, nt=50)
#     aa_clip = core.fmtc.resample(aa_clip, w, h, 0, -0.5).std.Transpose()
#     aa_clip = core.eedi2.EEDI2(aa_clip, field=1, mthresh=10, lthresh=20, vthresh=20, maxd=24, nt=50)
#     aa_clip = core.fmtc.resample(aa_clip, h, w, 0, -0.5).std.Transpose()
#     aaed = core.std.ShufflePlanes([aa_clip, clip], [0, 1, 2], vs.YUV)
#     aaed = core.rgvs.Repair(aaed, clip, 2)
#     return aaed


def aa_nnedi3(clip):
    w = clip.width
    h = clip.height
    aa_clip = core.std.ShufflePlanes(clip, 0, vs.GRAY)
    aa_clip = core.nnedi3.nnedi3(aa_clip, field=1, dh=True, nsize=3, nns=2, qual=2)
    aa_clip = core.fmtc.resample(aa_clip, w, h, 0, -0.5).std.Transpose()
    aa_clip = core.nnedi3.nnedi3(aa_clip, field=1, dh=True, nsize=3, nns=2, qual=2)
    aa_clip = core.fmtc.resample(aa_clip, h, w, 0, -0.5).std.Transpose()
    aaed = core.std.ShufflePlanes([aa_clip, clip], [0, 1, 2], vs.YUV)
    aaed = core.rgvs.Repair(aaed, clip, 2)
    return aaed
res = aa_nnedi3(clip)
diff = core.std.MakeDiff(clip, res).std.Expr(['x 32768 - 10 * 32768 +','32768'])
res.set_output(0)
clip.set_output(1)
diff.set_output(2)
