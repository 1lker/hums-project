"""Cross-cutting — PRD traceability helpers.

Attach a PRD identifier to classes/functions so generated artefacts and logs
can cite the spec section that produced them. Purely declarative; no runtime
behaviour beyond metadata attachment.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class PrdRef:
    number: str          # e.g. "001"
    section: str | None  # e.g. "§4 Outputs"
    note: str | None = None

    def __str__(self) -> str:
        tail = f" · {self.section}" if self.section else ""
        return f"PRD-{self.number}{tail}"


def prd(number: str, section: str | None = None, note: str | None = None) -> Callable[[T], T]:
    ref = PrdRef(number=number, section=section, note=note)

    def wrap(obj: T) -> T:
        setattr(obj, "__prd__", ref)
        return obj

    return wrap
