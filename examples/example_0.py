from __future__ import annotations

import dataclasses
from typing import Literal

import argparcel


@dataclasses.dataclass(kw_only=True, frozen=True, slots=True)
class _Args:
    a: int
    b: float
    c: Literal[1, 2, 3] = argparcel.arg(help="choose wisely")
    d: bool = True
    e: str | None = None


if __name__ == "__main__":
    print(argparcel.parse(_Args))
