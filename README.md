# Macos_vapoursynth_plugins
A repository holding commonly used vapoursynth plugins built for Apple Silicon Macos.

## Usage
1. Download all files in this repo.
2. Unzip all of them.
3. Copy all .dylib to ```/usr/local/lib/vapoursynth/```
4. Enjoy!

## Common problem
1. error like
```
libc++abi: terminating due to uncaught exception of type VSException: Failed to load /usr/local/lib/vapoursynth/liblsmashsource.1.dylib. Error given: dlopen(/usr/local/lib/vapoursynth/liblsmashsource.1.dylib, 0x0005): Library not loaded: liblsmash.dylib
  Referenced from: <623AE20D-27FA-3D03-A2F7-8F697AB21A47> /usr/local/lib/vapoursynth/liblsmashsource.1.dylib
  Reason: tried: 'liblsmash.dylib' (no such file), '/System/Volumes/Preboot/Cryptexes/OSliblsmash.dylib' (no such file), 'liblsmash.dylib' (no such file), '/Users/a1/liblsmash.dylib' (no such file), '/System/Volumes/Preboot/Cryptexes/OS/Users/a1/liblsmash.dylib' (no such file), '/Users/a1/liblsmash.dylib' (no such file)
```
make sure you have installed the dependency, or/and you should manually set those missing dylibs by
```bash
sudo install_name_tool -change libxxhash.0.dylib /opt/homebrew/lib/libxxhash.dylib /usr/local/lib/vapoursynth/liblsmashsource.1.dylib
```
