from __future__ import annotations

import dataclasses
import enum
from typing import TYPE_CHECKING, Literal

import argparcel

if TYPE_CHECKING:
    import pathlib


class Bird(enum.Enum):
    puffin = enum.auto()
    lark = enum.auto()


@dataclasses.dataclass(kw_only=True, frozen=True, slots=True)
class _Args:
    # Using a `Literal` will force a choice between 1, 2, or 3.
    a: Literal[1, 2, 3]

    # An enum will force a choice between the names of the enum elements.
    b: Bird = Bird.puffin

    # A `Path` can be automatically converted from a string. Here we also specify a
    # 'help' message by using a 'docstring' for the field.
    c: pathlib.Path | None = None
    """An important path."""


if __name__ == "__main__":
    print(argparcel.parse(_Args))
