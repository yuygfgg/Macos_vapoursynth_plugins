# Macos_vapoursynth_plugins
A repository holding commonly used vapoursynth plugins and tools built for Apple Silicon Macos. AI models are not included.

SIMD plugins are ported with sse2neon. I will open pull requests for some of the ported plugins, but not for all (especially those using VCL2(vectorclass version2), which I simply replace the VCL2 folder with my own version and fix missing functions by copy & pasting and thus pollute the code).

libakarin is using dynamic link to meet github requirement of <25 MB.

Vapoursynth: https://github.com/yuygfgg/vapoursynth-classic, X265: [https://github.com/yuygfgg/x265](https://github.com/yuygfgg/x265-Yuuki-Asuna)
