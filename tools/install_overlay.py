#!/usr/bin/env python3
"""Install NEW files only. Default is a dry run; never overwrite a different file."""
import argparse
import hashlib
import json
from pathlib import Path
import os
import tempfile

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--apply",action="store_true")
    args=parser.parse_args()
    repo=args.repo.resolve()
    if not (repo/"yellowstone_midway"/"project.godot").exists() or not (repo/"yellowstone_python").is_dir():
        parser.error("--repo must be the Yellowstone repository root")
    source=Path(__file__).resolve().parents[1]/"overlay"
    candidates=[]
    for path in sorted(source.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        relative=path.relative_to(source)
        target=repo/relative
        if not target.resolve().is_relative_to(repo):
            raise RuntimeError(f"path escapes repository through a symlink: {relative}")
        data=path.read_bytes()
        if target.exists():
            if not target.is_file() or target.read_bytes()!=data:
                raise FileExistsError(f"Refusing to overwrite changed/existing file: {relative}")
        else:
            candidates.append((relative,target,data))
    report={"mode":"apply" if args.apply else "dry-run", "new_files":[str(c[0]) for c in candidates],"existing_files_modified":0}
    print(json.dumps(report,indent=2))
    if not args.apply:
        return
    created=[]
    try:
        for relative,target,data in candidates:
            target.parent.mkdir(parents=True,exist_ok=True)
            # Exclusive creation prevents a race from clobbering a local edit.
            with target.open("xb") as stream:
                created.append(target)
                stream.write(data)
    except BaseException:
        for target in reversed(created):
            target.unlink(missing_ok=True)
        raise

if __name__=="__main__":
    main()
