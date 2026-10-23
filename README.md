# Yellowstone park runtime

A Godot 4.5 terrain-streaming demo and a small Python simulation service. Elevation pages load as the camera moves, coarse terrain stays visible while finer pages are prepared, and mesh and collision work have separate budgets.

The bundled terrain is a synthetic ridge with a gap. It lets you test streaming without downloading Yellowstone data.

## Run the demo

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python tools/prepare_demo.py
godot --headless --editor --path demo --import --quit
godot --path demo
```

Use Godot 4.5.1. Move with WASD, Q/E for height, Shift for faster travel, and right-drag to look. The HUD shows tile residency, preparation work and frame intervals.

## Tests

```sh
python -m pytest -q
godot --headless --path demo --script tests/park_runtime/run_tests.gd
```

The Godot checks cover page loading, coordinate conversion, interpolation and demand planning. To record a camera route with frame intervals and renderer counters:

```sh
godot --path demo --script tests/park_runtime/benchmark_route.gd -- \
  --frames=600 --duration=10 --out=res://route-results.json
```

Run that command with a visible renderer for timing comparisons. Headless results are useful for checking execution, not GPU performance.

## Optional simulation service

```sh
PYTHONPATH=overlay/yellowstone_python python -m yellowstone_python.park_runtime \
  --state ./reference-state.sqlite3
```

The service runs separately from rendering. It provides a shared timeline, bracketing snapshots, checkpoint rollback and committed state. Its reservoir network is a numerical example; it does not replace Yellowstone's river model.

## Layout

- `overlay/yellowstone_midway/`: reusable GDScript modules and test scene.
- `overlay/yellowstone_python/`: simulation and terrain-page modules.
- `demo/`: assembled Godot project and synthetic elevation pages.
- `tests/`: Python tests.
- `tools/`: demo preparation and optional Yellowstone integration helpers.
- `docs/`: architecture and integration notes tied to the recorded baseline.

The demo is independently runnable. Connecting it to the full Yellowstone scene requires the terrain, vegetation, wildlife and simulation adapters described in the integration notes. The legacy live-engine adapter does not yet provide durable native saves. The demo's frame intervals do not establish performance for the full park.

Source code is published by its owner for inspection. No additional reuse license is granted by this repository.
