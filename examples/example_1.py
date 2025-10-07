from __future__ import annotations

import dataclasses
import enum
import pathlib
from typing import Literal

import argparcel


class Bird(enum.Enum):
    puffin = enum.auto()
    lark = enum.auto()


# argparcel requires pathlib to be imported at runtime, since it will be used for
# conversion. Static analysis tools (like ruff) notice that we're only using the type
# for annotating the dataclass, and so might suggest moving its import to a
# TYPE_CHECKING block.
#
# The `uses_types` function is a trivial function to indicate types required at runtime
# to your linter.
@argparcel.uses_types(pathlib.Path)
@dataclasses.dataclass(kw_only=True, frozen=True, slots=True)
class Args:
    # Using a `Literal` will force a choice between 1, 2, or 3.
    a: Literal[1, 2, 3]

    # An enum will force a choice between the names of the enum elements.
    b: Bird = Bird.puffin

    # A `Path` can be automatically converted from a string. Here we also specify a
    # 'help' message by using a 'docstring' for the field.
    c: pathlib.Path | None = None
    """An important path."""

    # A list will introduce a flag that consumes zero or more elements.
    d: list[float] | None = None

    # A tuple can require exactly a certain number of elements to be specified.
    e: tuple[int, int] | None = None

    # A tuple can also have an unknown number of elements.
    f: tuple[str, ...] | None = None

    # A tuple can also be required to have one or more elements.
    g: tuple[float, *tuple[float, ...]] | None = None


if __name__ == "__main__":
    print(argparcel.parse(Args))
