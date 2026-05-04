import os
import sys

# python rename_recursive.py "oldstring" "newstring" "/full/path/to/your/folder"

def rename_recursive(root_path, old_string, new_string):
    # Walk the directory tree, bottom-up to safely rename folders
    for dirpath, dirnames, filenames in os.walk(root_path, topdown=False):
        # Rename files
        for filename in filenames:
            if old_string in filename:
                old_file = os.path.join(dirpath, filename)
                new_file = os.path.join(dirpath, filename.replace(old_string, new_string))
                os.rename(old_file, new_file)
                print(f"Renamed file: {old_file} -> {new_file}")

        # Rename directories
        for dirname in dirnames:
            if old_string in dirname:
                old_dir = os.path.join(dirpath, dirname)
                new_dir = os.path.join(dirpath, dirname.replace(old_string, new_string))
                os.rename(old_dir, new_dir)
                print(f"Renamed folder: {old_dir} -> {new_dir}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python rename_recursive.py <old_string> <new_string> <path>")
        sys.exit(1)

    old_string = sys.argv[1]
    new_string = sys.argv[2]
    root_path = sys.argv[3]

    if not os.path.isdir(root_path):
        print(f"Error: {root_path} is not a valid directory.")
        sys.exit(1)

    rename_recursive(root_path, old_string, new_string)
    print("Done.")
