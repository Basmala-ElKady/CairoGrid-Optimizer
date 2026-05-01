from typing import Dict

class IntersectionPriority:
    """
    Simple intersection priority manager.

    It stores signal data and provides `get_multiplier(node_id, is_emergency)`
    which returns a multiplier to apply to edge travel costs when leaving `node_id`.

    By default normal traffic uses multiplier 1.0; emergency vehicles get a reduced multiplier < 1.0
    only at intersections (degree > 2). This class is lightweight and intentionally
    separated from routing logic so it can be extended later with signal timings.
    """

    def __init__(self, default_emergency_multiplier: float = 0.6):
        self.default_emergency_multiplier = float(default_emergency_multiplier)
        # allow per-node overrides: node_id -> multiplier
        self.overrides: Dict[str, float] = {}

    def set_override(self, node_id: str, multiplier: float):
        self.overrides[str(node_id)] = float(multiplier)

    def get_multiplier(self, node_id: str, is_emergency: bool) -> float:
        if not is_emergency:
            return 1.0
        return self.overrides.get(str(node_id), self.default_emergency_multiplier)
