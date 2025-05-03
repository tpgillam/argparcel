from __future__ import annotations

import dataclasses
import enum

# NOTE: Ruff rule TC003: https://docs.astral.sh/ruff/rules/typing-only-standard-library-import/
#   argparcel requires pathlib to be imported at runtime, since it will be used for
#   conversion. Static analysis tools (like ruff) notice that we're only using the type
#   for annotating the dataclass, however argparcel inspects this at runtime.
import pathlib  # noqa: TC003
from typing import Literal

import argparcel


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
    # 'help' message along with a default by using `argparcel.arg`
    c: pathlib.Path | None = argparcel.arg(help="specify a path", default=None)  # noqa: RUF009


if __name__ == "__main__":
    print(argparcel.parse(_Args))
