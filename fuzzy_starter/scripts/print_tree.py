import os
import sys

def print_tree(root_dir):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for name in dirnames + filenames:
            path = os.path.join(dirpath, name)
            rel_path = os.path.relpath(path, root_dir)
            print(rel_path)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <relative_path>")
        sys.exit(1)

    root = sys.argv[1]
    print_tree(root)