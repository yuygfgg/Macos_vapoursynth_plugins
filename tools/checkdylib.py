import ctypes
import subprocess
import sys
import os
import re

def load_dylib(dylib_path):
    try:
        ctypes.CDLL(dylib_path)
        print("All dependencies are correctly configured.")
        return True, None
    except OSError as e:
        error_message = str(e)

        # Use regex to parse the missing library name
        match = re.search(r'Library not loaded: (.+)', error_message)
        if match:
            missing_dep = match.group(1).strip()
            # missing_name = os.path.basename(missing_dep)
            return False, missing_dep
        else:
            return False, None

def find_dependency(missing_name):
    missing_name = os.path.basename(missing_name)
    search_paths = ['/opt/homebrew/lib', '/usr/local/lib']
    for path in search_paths:
        possible_path = os.path.join(path, missing_name)
        if os.path.exists(possible_path):
            return possible_path
    return None

def fix_dependency(dylib_path, missing_dep):
    found_path = find_dependency(missing_dep)
    if found_path:
        try:
            subprocess.run(['install_name_tool', '-change', missing_dep, found_path, dylib_path], check=True)
            print(f"Automatically fixed {missing_dep} to {found_path}")
        except subprocess.CalledProcessError as e:
            print(f"Fix failed: {e}")
    else:
        print(f"Could not automatically find {missing_dep}. Please enter the path manually.")
        new_path = input(f"Enter the correct location for {missing_dep}: ").strip()
        if os.path.exists(new_path):
            try:
                subprocess.run(['install_name_tool', '-change', missing_dep, new_path, dylib_path], check=True)
                print(f"Fixed {missing_dep} to {new_path}")
            except subprocess.CalledProcessError as e:
                print(f"Fix failed: {e}")
        else:
            print(f"Path {new_path} does not exist.")

def check_and_fix_dylib(dylib_path):
    while True:
        success, missing_dep = load_dylib(dylib_path)
        if success:
            break
        if missing_dep is None:
            print("Failed to parse missing dependency, exiting.")
            break
        fix_dependency(dylib_path, missing_dep)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python check_and_fix_dylib.py <dylib_path>")
        sys.exit(1)

    dylib_path = sys.argv[1]
    check_and_fix_dylib(dylib_path)
