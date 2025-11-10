import os
import sys
import argparse
import subprocess
from pathlib import Path


def _test_single_dylib(dylib_path: Path) -> (bool, str):
    """
    Tests a single dylib in a controlled subprocess.
    """
    env = os.environ.copy()

    env["DYLD_FALLBACK_LIBRARY_PATH"] = ""

    command = [
        sys.executable,
        "-c",
        f"import ctypes; print('Loading via ctypes...'); ctypes.CDLL('{dylib_path.resolve()}')",
    ]

    try:
        result = subprocess.run(
            command,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return True, (result.stdout + result.stderr).strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()


def verify_bundle(bundle_dir: Path):
    """
    Verifies that all dylibs in the 'lib' subdir are self-contained by loading them
    in a restricted environment that disables system fallback paths.
    """
    if not bundle_dir.is_dir():
        print(f"❌ Error: Bundle directory not found at '{bundle_dir}'")
        return 1

    lib_dir = bundle_dir / "lib"
    if not lib_dir.is_dir():
        print(
            f"❌ Error: 'lib' subdirectory not found in '{bundle_dir}'. Invalid bundle."
        )
        return 1

    dylib_files = sorted(list(lib_dir.glob("*.dylib")))
    if not dylib_files:
        print(f"ℹ️ No .dylib files found in '{lib_dir}'. Nothing to verify.")
        return 0

    print(f"--- Verifying Bundle at: {bundle_dir} (Strict rpath Mode) ---\n")

    success_count = 0
    failure_count = 0

    for dylib_path in dylib_files:
        print(f"[*] Testing: {dylib_path.name}")

        is_ok, message = _test_single_dylib(dylib_path)

        if is_ok:
            print("  ✅ OK: Library loaded successfully using its embedded rpath.")
            success_count += 1
        else:
            print(
                "  ❌ FAILED: Could not load library. The bundle is likely not self-contained."
            )
            print("     --- dyld Error ---")
            for line in message.splitlines():
                print(f"       {line}")
            print("     ------------------")
            failure_count += 1
        print("-" * 30)

    print("\n--- Verification Summary ---")
    print(f"Total libraries tested: {len(dylib_files)}")
    print(f"  Success: {success_count}")
    print(f"  Failures: {failure_count}")

    if failure_count > 0:
        print(
            "\n❌ Verification failed. Check the dyld errors above to see which dependencies are missing or have incorrect paths."
        )
        return 1
    else:
        print(
            "\n✅ All checks passed! The bundle is correctly configured and self-contained."
        )
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Verify a macOS dylib bundle is self-contained by testing its rpaths in a restricted environment.",
    )
    parser.add_argument(
        "bundle_path",
        type=Path,
        help="Path to the root directory of the bundle to verify.",
    )
    args = parser.parse_args()

    exit_code = verify_bundle(args.bundle_path)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
