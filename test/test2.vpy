import vapoursynth as vs
from vapoursynth import core

src8 = core.lsmas.LWLibavSource(source='input2.mkv')
src16 = core.fmtc.bitdepth(src8, bits=16)

# Denoise
nr16 = core.nlm_ispc.NLMeans(src16, d=0, wmode=0, h=3)

# Deband
dbed = core.neo_f3kdb.Deband(nr16, 12, 72, 48, 48, 0, 0, output_depth=16).neo_f3kdb.Deband(24, 56, 32, 32, 0, 0, output_depth=16)
# AA
nr16Y = core.std.ShufflePlanes(nr16, 0, vs.GRAY)
aa_nr16Y = core.eedi2.EEDI2(nr16Y, field=1, mthresh=10, lthresh=20, vthresh=20, maxd=24, nt=50)
aa_nr16Y = core.fmtc.resample(aa_nr16Y, 1920, 1080, 0, -0.5).std.Transpose()
aa_nr16Y = core.eedi2.EEDI2(aa_nr16Y, field=1, mthresh=10, lthresh=20, vthresh=20, maxd=24, nt=50)
aa_nr16Y = core.fmtc.resample(aa_nr16Y, 1080, 1920, 0, -0.5).std.Transpose()
aaedY = core.rgvs.Repair(aa_nr16Y, nr16Y, 2)

# Merge AA and Deband
dbedY = core.std.ShufflePlanes(dbed, 0, vs.GRAY)
mergedY = core.std.MakeDiff(dbedY, aaedY, 0.9)
merged = core.std.ShufflePlanes([mergedY, dbed], [0,1,2], vs.YUV)

res = merged

res.set_output()
src8.set_output(1)
