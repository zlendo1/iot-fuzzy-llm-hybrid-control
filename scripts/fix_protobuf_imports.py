#!/usr/bin/env python
"""Post-process generated protobuf files to use relative imports.

grpc_tools.protoc generates absolute imports by default (e.g., 'import common_pb2'),
which don't work when the modules are imported as 'src.interfaces.rpc.generated.lifecycle_pb2'.

This script converts absolute imports to relative imports:
  Before: import common_pb2 as common__pb2
  After:  from . import common_pb2 as common__pb2
"""

import re
import sys
from pathlib import Path


def fix_imports_in_directory(gen_dir: Path) -> int:
    modified_count = 0

    for py_file in gen_dir.glob("*_pb2.py"):
        content = py_file.read_text()
        new_content = re.sub(
            r"^import (\w+_pb2) as (\w+)$",
            r"from . import \1 as \2",
            content,
            flags=re.MULTILINE,
        )
        if new_content != content:
            py_file.write_text(new_content)
            print(f"  Fixed: {py_file.name}")
            modified_count += 1

    for grpc_file in gen_dir.glob("*_pb2_grpc.py"):
        content = grpc_file.read_text()
        new_content = re.sub(
            r"^import (\w+_pb2) as (\w+)$",
            r"from . import \1 as \2",
            content,
            flags=re.MULTILINE,
        )
        if new_content != content:
            grpc_file.write_text(new_content)
            print(f"  Fixed: {grpc_file.name}")
            modified_count += 1

    return modified_count


if __name__ == "__main__":
    gen_dir = Path("src/interfaces/rpc/generated")

    if not gen_dir.exists():
        print(f"Error: {gen_dir} does not exist")
        sys.exit(1)

    print(f"Fixing imports in {gen_dir}...")
    count = fix_imports_in_directory(gen_dir)

    if count > 0:
        print(f"✓ Fixed {count} files")
        sys.exit(0)
    else:
        print("✓ No files needed fixing")
        sys.exit(0)
