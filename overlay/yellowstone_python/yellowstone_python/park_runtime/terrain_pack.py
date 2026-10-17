"""Compile paged elevation INPUTS, never scene meshes or simulated trajectories.

Each root is processed independently. Raw input can be an out-of-core NumPy memmap.
NoData is rejected rather than silently rendered as sea level. All samples are
heights relative to the explicitly declared vertical origin, in meters.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import os
import tempfile
import numpy as np
from .contracts import identifier, finite

SCHEMA = "yellowstone.terrain_tiles.v1"

def _write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")

def triangle_sample(grid, u, v):
    n = grid.shape[0]
    ix = np.clip(np.floor(u).astype(np.int64), 0, n-2)
    iz = np.clip(np.floor(v).astype(np.int64), 0, n-2)
    fx, fz = u-ix, v-iz
    a, b, c, d = grid[iz, ix], grid[iz, ix+1], grid[iz+1, ix], grid[iz+1, ix+1]
    return np.where(fx+fz <= 1, a+fx*(b-a)+fz*(c-a),
                    d+(1-fx)*(c-d)+(1-fz)*(b-d))

def geometric_error(source, coarse):
    """Maximum deviation at original vertices under the same b-c triangulation."""
    scale = (source.shape[0]-1)/(coarse.shape[0]-1)
    maximum = 0.
    u = np.arange(source.shape[1], dtype=np.float64)/scale
    for row in range(source.shape[0]):
        approximation = triangle_sample(coarse, u, np.full(u.shape, row/scale))
        maximum = max(maximum, float(np.max(np.abs(approximation-source[row]))))
    return maximum

def build_pack(values, output: Path, *, pack_id="midway", cell_m=4.,
               origin_x_m=-2048., origin_z_m=-2048., mesh_cells=32, root_cells=1024,
               easting_m=512952.5950985841, northing_m=4930199.044097667,
               vertical_origin_m=2200., provenance=None, append=False):
    identifier(pack_id)
    if any(c in pack_id for c in "/:"):
        raise ValueError("pack_id must be a simple path-safe identifier")
    for value, name in [(cell_m, "cell_m"), (origin_x_m, "origin_x_m"),
                        (origin_z_m, "origin_z_m"), (easting_m, "easting_m"),
                        (northing_m, "northing_m"), (vertical_origin_m, "vertical_origin_m")]:
        finite(value, name)
    if cell_m <= 0 or not 4 <= mesh_cells <= 128:
        raise ValueError("positive spacing and 4..128 cells per mesh required")
    if root_cells < mesh_cells or root_cells % mesh_cells:
        raise ValueError("root_cells must be a multiple of mesh_cells")
    ratio = root_cells // mesh_cells
    if ratio & (ratio - 1):
        raise ValueError("root_cells/mesh_cells must be a power of two")
    if values.ndim != 2 or (values.shape[0]-1)%root_cells or (values.shape[1]-1)%root_cells:
        raise ValueError("input cell dimensions must be whole multiples of root_cells")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    catalog_path = output/"catalog.json"
    existing = json.loads(catalog_path.read_text()) if append and catalog_path.exists() else None
    if catalog_path.exists() and not append:
        raise FileExistsError("output catalog exists; use a new directory or explicit --append")
    if (output/pack_id).exists():
        raise FileExistsError("immutable pack id already exists")
    frame = {"crs": "EPSG:32612", "easting_m": easting_m, "northing_m": northing_m,
             "vertical_origin_m": vertical_origin_m, "axis_rule": "+x east,+z south,+y up"}
    if existing and (existing["frame"] != frame or existing["schema"] != SCHEMA):
        raise ValueError("packs must share an explicit coordinate frame and schema")
    max_lod = int(math.log2(ratio))
    roots = []
    # Stage immutable pages first; publishing catalog.json is the commit point.
    staging = Path(tempfile.mkdtemp(prefix=".terrain-stage-", dir=output))
    try:
        def tile(lod, tx, tz):
            stride = 1 << lod
            count = mesh_cells * stride
            x, z = tx*count, tz*count
            source = np.asarray(values[z:z+count+1, x:x+count+1], dtype=np.float64)
            if not np.all(np.isfinite(source)):
                raise ValueError(f"NoData/nonfinite heights in root/tile {lod}/{tx}/{tz}")
            coarse = np.asarray(source[::stride, ::stride], dtype="<f4")
            prefix = f"{pack_id}/{lod}/{tx}_{tz}"
            raw = coarse.tobytes(order="C")
            path = staging/(prefix+".f32")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            descriptor = {"key": f"{pack_id}:{lod}:{tx}:{tz}", "page": prefix+".json",
                "lod": lod, "origin_x_m": origin_x_m+x*cell_m, "origin_z_m": origin_z_m+z*cell_m,
                "size_m": count*cell_m, "min_y_m": float(source.min()), "max_y_m": float(source.max()),
                "error_m": geometric_error(source, coarse.astype(np.float64)), "mesh_cells": mesh_cells}
            children = [tile(lod-1, tx*2+dx, tz*2+dz) for dz in range(2) for dx in range(2)] if lod else []
            page = {"schema": SCHEMA, "tile": descriptor, "children": children,
                    "heights": {"path": prefix+".f32", "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                                "dtype": "<f4", "shape": list(coarse.shape)},
                    "quality": (provenance or {}).get("quality", "derived_source_not_field_validated")}
            _write_json(staging/(prefix+".json"), page)
            return descriptor
        for tz in range((values.shape[0]-1)//root_cells):
            for tx in range((values.shape[1]-1)//root_cells):
                roots.append(tile(max_lod, tx, tz))
        for a in roots:
            for b in (existing or {}).get("roots", []):
                if (max(a["origin_x_m"], b["origin_x_m"]) < min(a["origin_x_m"]+a["size_m"], b["origin_x_m"]+b["size_m"])
                    and max(a["origin_z_m"], b["origin_z_m"]) < min(a["origin_z_m"]+a["size_m"], b["origin_z_m"]+b["size_m"])):
                    raise ValueError("root coverage overlaps; compose core/master heights before packing")
        (staging/pack_id).rename(output/pack_id)
        catalog = {"schema": SCHEMA, "dataset_revision": "", "frame": frame,
                   "roots": (existing or {}).get("roots", [])+roots,
                   "sources": (existing or {}).get("sources", [])+[{"pack_id": pack_id, **(provenance or {})}],
                   "edge_policy": "dyadic_shared_samples_visual_skirts_no_collision_skirts"}
        catalog["dataset_revision"] = hashlib.sha256(json.dumps(catalog,sort_keys=True).encode()).hexdigest()
        temporary = output/"catalog.pending.json"
        _write_json(temporary, catalog)
        os.replace(temporary, catalog_path)
        return catalog
    finally:
        import shutil
        shutil.rmtree(staging, ignore_errors=True)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, help="little-endian float32 raster; required unless --demo")
    p.add_argument("--nx", type=int, default=1025)
    p.add_argument("--nz", type=int, default=1025)
    p.add_argument("--cell", type=float, default=4.)
    p.add_argument("--origin-x", type=float, default=-2048.)
    p.add_argument("--origin-z", type=float, default=-2048.)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--pack-id", default="midway")
    p.add_argument("--mesh-cells", type=int, default=32)
    p.add_argument("--root-cells", type=int, default=1024)
    p.add_argument("--append", action="store_true")
    p.add_argument("--demo", action="store_true")
    args = p.parse_args()
    if args.demo:
        x,z = np.meshgrid(np.linspace(-512,512,257),np.linspace(-512,512,257))
        heights = (65*np.exp(-((x-60)/75)**2)*(1-.92*np.exp(-((z+130)/65)**2))
                   +8*np.sin(x/85)*np.cos(z/160)+.012*z).astype("<f4")
        provenance = {"quality":"synthetic_fixture_not_yellowstone", "generator":"analytic_ridge_and_gap_v1"}
        kw = dict(pack_id="synthetic", origin_x_m=-512., origin_z_m=-512., root_cells=256)
    else:
        if args.source is None or args.source.stat().st_size != args.nx*args.nz*4:
            p.error("source byte length must equal nx*nz*4")
        heights = np.memmap(args.source, mode="r", dtype="<f4", shape=(args.nz,args.nx))
        hasher = hashlib.sha256()
        with args.source.open("rb") as stream:
            for block in iter(lambda: stream.read(1024*1024),b""):
                hasher.update(block)
        provenance = {"quality":"derived_source_not_field_validated", "source_sha256":hasher.hexdigest(),
                      "source_name":args.source.name, "height_units":"m relative to vertical origin"}
        kw = dict(pack_id=args.pack_id, origin_x_m=args.origin_x, origin_z_m=args.origin_z, root_cells=args.root_cells)
    catalog = build_pack(heights,args.out,cell_m=args.cell,mesh_cells=args.mesh_cells,
                         append=args.append,provenance=provenance,**kw)
    print(json.dumps({"catalog":str(args.out/"catalog.json"),"roots":len(catalog["roots"]),
                      "dataset_revision":catalog["dataset_revision"]}))

if __name__ == "__main__":
    main()
