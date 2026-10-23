# 04. Exact implementation status

## Implemented source, exercised by Python tests

| Component | Scope |
|---|---|
| `contracts.py` | Coordinate conversion, validated interest messages, dependency closure |
| `terrain_pack.py` | Out-of-core-capable source input, paged dyadic hierarchy, triangulated error, shared samples, immutable hashes, non-overlap checks |
| `forcing.py` | Shared prescribed timeline, exact interval integration for supported interpolation modes |
| `reference_network.py` | Illustrative conservative branching reservoirs, confluences, water/heat/solute ledgers |
| `coupling.py` | Conservative extensive-state split/merge and exactly-once interface accounting |
| `runtime.py` | Common frontier, atomic domain advance, retained history, intervention rollback, filtered bracket, committed saves |
| `state_store.py` | Atomic SQLite checkpoints/events, integrity checks and model-version guards |
| `service.py` | Loopback worker-owned service, bounded commands/publications and independent rendering |
| `field_codec.py` | Bounded binary numeric field-pair codec |

The test report records **34 passed** at the final package validation. See the
final report for any subsequent additions/reruns. Scientific tests apply to the
reference numerical fixture and orchestration contracts, not new park predictions.

## GDScript checks

`world_frame.gd`, `terrain_job.gd`, `tile_visual.gd`, `demand_planner.gd`,
`terrain_streamer.gd`, `vegetation_batch.gd`, `field_buffer.gd`, `park_client.gd`,
`runtime_monitor.gd`, `streaming_demo.gd`, and the two test/benchmark scripts are
provided as source. Godot 4.5.1 has now imported the project and run its checks.
A visible Compatibility-renderer route also ran on Apple M4. These checks cover the
synthetic demo; full-world physics and comparative GPU performance remain untested.

The renderer implements perspective-camera demand, movement lookahead, soft
sampled terrain occlusion, all-direction coarse cover, asynchronous mesh arrays,
parent/child coverage, separate collision creation, guarded readiness and origin
shifting. It is not an orthographic/VR/multi-camera planner, texture streamer, cloud
renderer replacement or fully proven conservative occlusion solver.

## Implemented adapter, not integration-tested against the full native environment

`legacy_adapter.py` wraps the inspected LiveEngine. It intentionally requires that
engine's own worker be disabled. In-memory checkpoint/restore is connected to native
APIs. Durable native persistence is blocked until a safe versioned serializer exists.
It uses private methods at this baseline and must be ported to public wrappers/tests
as the migration guide specifies. The original solver is not replaced by a fixture.

## Explicit integration work remaining

- Make the opt-in real world use the new streamer without loading the giant scene.
- Compose the master/core height authority; preserve pool cuts, shorelines, routes,
  boardwalks and interaction geometry in bounded feature pages/jobs.
- Page canopy, forest-floor and wildlife sources; implement the specific near/mid/far
  representations and actor state subscriptions using the new batch/transport helpers.
- Port geographic materials, texture caches, atmosphere coordinates, maps and probes.
- Adapt native controls/UI and command-completion polling. The minimal client reports
  queued commands, not final acceptance. Connect hot native fields to the binary codec.
- Add native checkpoint serialization, real domain boundary coupling, numerical
  coarse/fine reconciliation and measured regional worker parallelism where justified.
- Add budget-driven automatic quality adaptation, larger bootstrap catalog paging,
  robust fast-travel preparation and more aggressive proven occlusion only after
  correctness tests. Current terrain pressure is reported rather than silently
  violating the configured accounting budget.

These are specific tasks in `01_CURRENT_FILE_EDITS.md`, not work that has already
been completed or tested in the user's checkout. This package makes no repository
changes, no FPS promises and no claim to finish the whole park's scientific models.
