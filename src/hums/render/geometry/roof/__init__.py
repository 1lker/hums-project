"""PRD-003 · §6.2 — roof Strategy registry."""
from .base import RoofGenerator
from .complex_pitched import ComplexPitchedRoof
from .flat import FlatRoof
from .gable import GableRoof
from .hip import HipRoof
from .mansard import MansardRoof
from .vault_flat import VaultFlatRoof

SHAPE_TO_GENERATOR: dict[str, type[RoofGenerator]] = {
    "flat": FlatRoof,
    "gable": GableRoof,
    "hip": HipRoof,
    "mansard": MansardRoof,
    "vault_flat": VaultFlatRoof,
    "complex_pitched": ComplexPitchedRoof,
}


def for_shape(shape: str) -> RoofGenerator:
    cls = SHAPE_TO_GENERATOR.get(shape, GableRoof)
    return cls()
