# Macos_vapoursynth_plugins
A repository holding commonly used vapoursynth plugins built for Apple Silicon Macos.

SIMD plugins are ported with sse2neon. I will open pull requests for some of the ported plugins, but not for all (especially those using VCL2(vectorclass version2)). 

## Usage
1. Download all files in this repo.
2. Unzip all of them.
3. Copy all .dylib files to ```/usr/local/lib/vapoursynth/```
4. Enjoy!

## Common problem
1. For errors like
```
libc++abi: terminating due to uncaught exception of type VSException: Failed to load /usr/local/lib/vapoursynth/liblsmashsource.1.dylib. Error given: dlopen(/usr/local/lib/vapoursynth/liblsmashsource.1.dylib, 0x0005): Library not loaded: liblsmash.dylib
  Referenced from: <623AE20D-27FA-3D03-A2F7-8F697AB21A47> /usr/local/lib/vapoursynth/liblsmashsource.1.dylib
  Reason: tried: 'liblsmash.dylib' (no such file), '/System/Volumes/Preboot/Cryptexes/OSliblsmash.dylib' (no such file), 'liblsmash.dylib' (no such file), '/Users/a1/liblsmash.dylib' (no such file), '/System/Volumes/Preboot/Cryptexes/OS/Users/a1/liblsmash.dylib' (no such file), '/Users/a1/liblsmash.dylib' (no such file)
```
make sure you have installed the dependency, or/and you should manually set those missing dylibs using the fix_missing_dylibs.py.
```bash
python fix_missing_dylibs.py /Users/a1/Downloads/liblsmashsource.1.dylib 
Automatically fixed libxxhash.0.dylib to /opt/homebrew/lib/libxxhash.0.dylib
Automatically fixed liblsmash.dylib to /usr/local/lib/liblsmash.dylib
All dependencies are correctly configured.
```

The script automatically looks for missing dylibs in ```/usr/local/lib``` and ```/opt/homebrew/lib```. You will need to manually configure missing dylibs if they are not there.
