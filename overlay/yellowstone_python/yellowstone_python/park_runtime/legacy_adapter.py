"""In-process bridge to the inspected existing LiveEngine, without a second clock.

The native checkpoint includes scientific Python objects. Volatile rollback works;
StateStore JSON persistence is deliberately NOT supported by this bridge until the
native solver supplies a versioned serializer. Do not use pickle as a workaround.
"""
from __future__ import annotations
import copy
from .contracts import finite, identifier

class LegacyLiveDomain:
    model_id = "yellowstone.legacy_live_bridge.v1"
    persistence_supported = False

    def __init__(self, engine, domain_id="midway.firehole"):
        if engine._worker is not None:
            raise ValueError("construct LiveEngine with start_worker=False; only ParkRuntime owns advancement")
        self.engine = engine
        self.domain_id = identifier(domain_id)

    @property
    def time_s(self):
        return float(self.engine.river.time_s)

    def advance_to(self, target_s):
        self.engine.compute_until(finite(target_s, "target_s"))
        # The parent orchestrator retains history. Avoid an unbounded second history.
        keep = self.time_s - max(self.engine.horizon_s, 60.)
        self.engine._frames = [f for f in self.engine._frames if f["t_s"] >= keep]
        self.engine._checkpoints = {t: c for t, c in self.engine._checkpoints.items() if t >= keep}
        self.engine._publish_snapshot()

    def snapshot(self):
        return {"domain_id": self.domain_id, "model_id": self.model_id,
                "quality": "existing_solver_claims_unchanged", "t_s": self.time_s,
                "frame": copy.deepcopy(self.engine._frames[-1])}

    def checkpoint(self):
        return {"model_id": self.model_id, "native": self.engine._checkpoint(),
                "revision": self.engine.revision,
                "frames": copy.deepcopy(self.engine._frames[-2:])}

    def restore(self, checkpoint):
        if checkpoint["model_id"] != self.model_id:
            raise ValueError("legacy checkpoint identity mismatch")
        self.engine._restore(checkpoint["native"])
        self.engine.revision = checkpoint["revision"]
        self.engine._frames = copy.deepcopy(checkpoint["frames"])
        self.engine._checkpoints = {self.time_s: self.engine._checkpoint()}
        self.engine._publish_snapshot()

    def intervene(self, changes):
        self.engine.command("control", {"at_s": self.time_s, "changes": changes})
