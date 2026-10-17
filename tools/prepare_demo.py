#!/usr/bin/env python3
"""Assemble the isolated Godot demo from new scripts and synthetic elevation inputs."""
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"overlay"/"yellowstone_python"))
from yellowstone_python.park_runtime.terrain_pack import main as prepare_terrain

def main():
    source=ROOT/"overlay"/"yellowstone_midway"
    target=ROOT/"demo"
    for folder in ("scripts","scenes","tests"):
        if (source/folder).exists():
            shutil.copytree(source/folder,target/folder,dirs_exist_ok=True)
    output=target/"data"/"park_demo"
    if not (output/"catalog.json").exists():
        sys.argv=["terrain_pack","--demo","--out",str(output)]
        prepare_terrain()
    print("Godot project:",target)

if __name__=="__main__":
    main()
