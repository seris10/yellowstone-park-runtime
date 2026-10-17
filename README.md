# Yellowstone: park-scale runtime migration package

**New scripts + file-specific integration instructions.** Targets the inspected
`seris10/yellowstone` commit `c2b4c7923a6eeed61e2feca3946555826849ec67` and Godot 4.5.1.
No existing repository files were modified.

Start with **[AGENT_START_HERE.md](AGENT_START_HERE.md)**. The detailed edit map is
**[docs/01_CURRENT_FILE_EDITS.md](docs/01_CURRENT_FILE_EDITS.md)**. It specifies changes
to the actual world bootstrap, player, terrain/core/water pipeline, materials,
vegetation, wildlife, atmosphere, Python engine, transport and controls.

## What the code does

The terrain path builds meshes on demand from small immutable elevation source
pages. Its demand planner combines screen-space geometric error, camera frustum,
movement lookahead and a soft terrain-occlusion hint. Coarse parents stay visible
until complete child coverage is ready. Workers construct arrays; main-thread
commits and physics collision commits are independently bounded. Absolute source
coordinates survive local origin shifting.

The Python path keeps simulation separate from visibility. It supplies one physical
timeline, bracketing snapshots, checkpoint rollback, persistent committed state,
shared forcing, conservative transfer accounting and a bridge to the existing live
engine. An illustrative branching network exercises the infrastructure without
pretending to replace Yellowstone's native physics.

## Run the reference checks and demo

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python tools/prepare_demo.py
# Set GODOT to a local Godot 4.5.1 executable:
"$GODOT" --headless --editor --path demo --import --quit
"$GODOT" --headless --path demo --script tests/park_runtime/run_tests.gd
"$GODOT" --path demo
```

The demo includes a synthetic ridge and gap. It is a streaming fixture, not park data.
Use WASD to fly, Q/E vertically, Shift for faster travel, and right-drag to look. The
HUD exposes tile residency, preparation work, frame intervals and service status.

Optional, in another terminal:

```sh
PYTHONPATH=overlay/yellowstone_python python -m yellowstone_python.park_runtime \
  --state /tmp/yellowstone-park-reference.sqlite3
```

The service and Godot are separate processes. The service is optional for the terrain
demo and is explicitly a numerical fixture until the real engine is integrated.

## Contents

| Location | Purpose |
|---|---|
| `overlay/yellowstone_midway/scripts/park_runtime/` | New GDScript modules |
| `overlay/yellowstone_python/yellowstone_python/park_runtime/` | New Python modules |
| `overlay/yellowstone_midway/tests/park_runtime/` | Local Godot checks and route benchmark |
| `tests/` | Executed Python tests |
| `demo/` | Isolated Godot project with synthetic elevation input pages |
| `tools/` | Baseline checker, no-overwrite installer and demo assembler |
| `docs/` | Binding architecture, exact edits, coupling, acceptance, status and sources |
| `reports/` | Actual validation output and scope |

## Validation and limits

The recorded Python run passed **34 tests**. Godot was not available in this build
environment, so GDScript engine compilation, runtime/physics behavior and GPU
performance remain explicit local gates. Source preload references were checked.
The full existing Yellowstone scientific test suite was not run here.

This is a migration foundation, not a finished replacement for every current scene
layer. The core/master height composition, shoreline/route feature adapters, streamed
vegetation/wildlife integration and real material/texture paging are specified work
for the local agent. Native durable saves require an explicit serializer; the bridge
blocks them until that is implemented. A general coupled adaptive scientific solver
is not claimed implemented. See `docs/04_IMPLEMENTATION_STATUS.md` for the exact split.

The installer adds new files only and refuses to overwrite conflicting local work.
Keep the old scene as the comparison path until the integration and parity gates pass.
