from __future__ import annotations

import dataclasses

import argparcel


@dataclasses.dataclass(kw_only=True, frozen=True, slots=True)
class _Args:
    a: int
    b: float

    # A `bool` argument will create a linked pair of flags `--c` and `--no-c`.
    c: bool

    # A command line argument will be optional if and only if a default value is
    # provided in the corresponding dataclass field.
    d: str | None = None


if __name__ == "__main__":
    print(argparcel.parse(_Args))
