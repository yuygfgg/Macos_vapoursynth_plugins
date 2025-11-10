import sys
import shutil
import subprocess
import argparse
import regex as re
from pathlib import Path
from collections import deque

OTOOL_RE = re.compile(r"^\s*(@[^\s]+|/.+?)\s+\(compatibility version")
SYSTEM_PATHS = ("/usr/lib/", "/System/Library/")


def ask_user_to_bundle(path):
    while True:
        prompt = (
            f"  -> Found dependency: {path}\n"
            f"     Bundle this library? (y/n, or Ctrl+C to skip current file): "
        )
        answer = input(prompt).lower().strip()
        if answer in ["y", "yes"]:
            return True
        if answer in ["n", "no"]:
            return False
        print("Invalid input. Please enter 'y' or 'n'.")


def is_system_lib(path):
    return any(path.startswith(p) for p in SYSTEM_PATHS)


def run_command(cmd, check=True):
    if "-change" not in cmd:
        print(f"  > Executing: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, check=check, capture_output=True, text=True, encoding="utf-8"
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        # Gracefully handle "no change" errors
        if check and "no change" in e.stderr:
            return e.stderr
        print(f"Error executing command: {' '.join(cmd)}", file=sys.stderr)
        print(f"Stderr: {e.stderr}", file=sys.stderr)
        raise


def get_potential_dependencies(file_path, process_all=False):
    """Returns a dict of {resolved_path: original_path}."""
    dependencies = {}
    try:
        output = run_command(["otool", "-L", str(file_path)])
        for line in output.splitlines():
            match = OTOOL_RE.match(line)
            if match:
                original_path_str = match.group(1)
                if original_path_str != str(
                    file_path
                ) and not original_path_str.startswith("@"):
                    if process_all or not is_system_lib(original_path_str):
                        resolved_path = Path(original_path_str).resolve()
                        dependencies[resolved_path] = original_path_str
    except Exception as e:
        print(
            f"Warning: Could not process dependencies for {file_path}. Error: {e}",
            file=sys.stderr,
        )
    return dependencies


def discover_dependencies_for_file(start_file, process_all, global_processed_deps):
    to_process = deque([start_file.resolve()])

    # Transactional state
    local_deps_to_bundle = {}  # {resolved_path: original_path}
    local_deps_to_skip = {}  # {resolved_path: original_path}
    # Tree mapping source to its direct dependencies
    local_dependency_tree = {}  # {resolved_source: {resolved_dep: original_dep}}

    local_processed_in_this_run = set()

    while to_process:
        current_source_resolved = to_process.popleft()

        # Get dependencies for the current source file
        dependencies_of_current = get_potential_dependencies(
            current_source_resolved, process_all
        )

        # Ensure the current source file has an entry in the tree, even if it has no dependencies.
        if current_source_resolved not in local_dependency_tree:
            local_dependency_tree[current_source_resolved] = {}

        for dep_resolved, dep_original in dependencies_of_current.items():
            local_dependency_tree[current_source_resolved][dep_resolved] = dep_original

            # Skip processing only if it has been seen before (either globally or in this specific run).
            if (
                dep_resolved in global_processed_deps
                or dep_resolved in local_processed_in_this_run
            ):
                continue

            local_processed_in_this_run.add(dep_resolved)

            if ask_user_to_bundle(dep_original):
                print(f"    [+] Queued for bundling: {Path(dep_original).name}")
                local_deps_to_bundle[dep_resolved] = dep_original
                to_process.append(dep_resolved)
            else:
                print(f"    [-] Skipping: {Path(dep_original).name}")
                local_deps_to_skip[dep_resolved] = dep_original

    return local_deps_to_bundle, local_deps_to_skip, local_dependency_tree


def main():
    parser = argparse.ArgumentParser(
        description="Recursively find, copy, and fix rpaths for macOS dylibs.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "input_path", type=Path, help="Path to a dylib file or a directory of dylibs."
    )
    parser.add_argument(
        "output_dir", type=Path, help="Directory to store the bundled libraries."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Manually process all dylibs, including system libraries.",
    )
    args = parser.parse_args()

    if not args.input_path.exists():
        sys.exit(f"Error: Input path '{args.input_path}' does not exist.")

    lib_dir = args.output_dir / "lib"
    support_dir = args.output_dir / "support"
    lib_dir.mkdir(parents=True, exist_ok=True)
    support_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directories created at '{args.output_dir}'")

    initial_files = (
        sorted(list(args.input_path.glob("*.dylib")))
        if args.input_path.is_dir()
        else [args.input_path]
    )

    print("\n--- Starting Interactive Dependency Discovery ---")

    files_to_bundle = set()
    skipped_initial_files = set()
    all_dependencies_to_bundle = {}  # {resolved: original}
    global_skipped_deps = {}  # {resolved: original}
    global_processed_deps = set()  # Set of resolved paths
    master_dependency_tree = {}  # {resolved_source: {resolved_dep: original_dep}}

    for initial_file in initial_files:
        try:
            print(f"\n--- Processing initial file: {initial_file.name} ---")

            master_dependency_tree[initial_file.resolve()] = {}

            deps_to_bundle_for_this, deps_to_skip_for_this, dep_tree_for_this = (
                discover_dependencies_for_file(
                    initial_file, args.all, global_processed_deps
                )
            )

            all_dependencies_to_bundle.update(deps_to_bundle_for_this)
            global_skipped_deps.update(deps_to_skip_for_this)

            # Merge the dependency trees.
            for source, deps in dep_tree_for_this.items():
                if source not in master_dependency_tree:
                    master_dependency_tree[source] = {}
                master_dependency_tree[source].update(deps)

            global_processed_deps.update(deps_to_bundle_for_this.keys())
            global_processed_deps.update(deps_to_skip_for_this.keys())

            files_to_bundle.add(initial_file)
            print(f"--- Finished processing {initial_file.name} ---")

        except KeyboardInterrupt:
            print(
                f"\n\n*** User interrupted processing for {initial_file.name}. Skipping this file. ***\n"
            )
            skipped_initial_files.add(initial_file)
            try:
                import termios

                termios.tcflush(sys.stdin, termios.TCIOFLUSH)
            except (ImportError, termios.error):
                pass
            continue

    print(
        f"\n--- Discovery Complete. {len(all_dependencies_to_bundle)} unique dependencies will be bundled. ---"
    )

    if not files_to_bundle and not all_dependencies_to_bundle:
        sys.exit("\nNo files to bundle. Exiting.")

    print("\n--- Copying Files ---")
    for f in files_to_bundle:
        shutil.copy(f, lib_dir)
    for resolved_path in all_dependencies_to_bundle.keys():
        shutil.copy(resolved_path, support_dir)

    print("\n--- Patching Dependencies and IDs ---")
    files_in_lib_dir = [lib_dir / f.name for f in files_to_bundle]
    files_in_support_dir = [
        support_dir / r.name for r in all_dependencies_to_bundle.keys()
    ]

    # Create reverse maps for finding original paths from copied paths
    copied_path_to_original_resolved = {
        **{lib_dir / f.name: f.resolve() for f in files_to_bundle},
        **{support_dir / r.name: r for r in all_dependencies_to_bundle.keys()},
    }

    # Set the ID for all support libraries
    for lib in files_in_support_dir:
        new_id = f"@rpath/{lib.name}"
        run_command(["install_name_tool", "-id", new_id, str(lib)])

    # Patch the dependencies for ALL copied files (initial and support)
    for copied_file_path in files_in_lib_dir + files_in_support_dir:
        original_resolved_path = copied_path_to_original_resolved.get(copied_file_path)

        # Check if this file has any dependencies recorded in our tree
        if original_resolved_path in master_dependency_tree:
            print(f"Patching dependencies for: {copied_file_path.name}")
            # Iterate only through the direct dependencies of this specific file
            for dep_resolved, dep_original in master_dependency_tree[
                original_resolved_path
            ].items():
                # Check if this dependency was actually bundled
                if dep_resolved in all_dependencies_to_bundle:
                    new_path = f"@rpath/{dep_resolved.name}"
                    print(f"  Changing '{dep_original}' -> '{new_path}'")
                    run_command(
                        [
                            "install_name_tool",
                            "-change",
                            dep_original,
                            new_path,
                            str(copied_file_path),
                        ],
                        check=False,
                    )

    print("\n--- Adding Rpath Search Paths (only where needed) ---")
    for copied_file_path in files_in_lib_dir + files_in_support_dir:
        original_resolved_path = copied_path_to_original_resolved.get(copied_file_path)
        # Add rpath only if the file has bundled dependencies
        if original_resolved_path in master_dependency_tree and any(
            dep in all_dependencies_to_bundle
            for dep in master_dependency_tree[original_resolved_path]
        ):
            rpath = (
                "@loader_path/../support"
                if copied_file_path.parent.name == "lib"
                else "@loader_path/."
            )
            print(f"Adding rpath '{rpath}' to {copied_file_path.name}")
            run_command(
                ["install_name_tool", "-add_rpath", rpath, str(copied_file_path)]
            )
        else:
            print(
                f"Skipping rpath for {copied_file_path.name} (no bundled dependencies)"
            )

    print("\n\n--- Bundling Complete! ---")
    print(f"Processed libraries are in: {lib_dir}")
    print(f"Bundled dependencies are in: {support_dir}")
    if skipped_initial_files:
        print(
            "\n--- The following initial files were skipped by user interruption (Ctrl+C) ---"
        )
        for f in sorted(list(skipped_initial_files)):
            print(f"  - {f.name}")
    if global_skipped_deps:
        print(
            "\n--- The following dependencies were manually skipped (answered 'n') ---"
        )
        print(
            "Your application will expect to find them on the user's system at runtime:"
        )
        for dep_original in sorted(global_skipped_deps.values()):
            print(f"  - {dep_original}")


if __name__ == "__main__":
    main()
