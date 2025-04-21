from __future__ import annotations

import argparse
import contextlib
import dataclasses
import pathlib  # noqa: TC003 We need this at runtime for parsing
from typing import Literal

import rich

import argparcel


@dataclasses.dataclass(kw_only=True, frozen=True, slots=True)
class Moo:
    a: int | None
    b: float
    choice: Literal[1, 2, 3] | None = argparcel.help("choose wisely")
    path: pathlib.Path | None
    c: bool = True
    description: str | None = None


rich.print(argparcel.parse(Moo, ["--a", "2", "--b", "3.2", "--choice", "1"]))
rich.print(argparcel.parse(Moo, ["--a", "2", "--b", "3.2", "--no-c", "--choice", "3"]))
rich.print(argparcel.parse(Moo, ["--b", "4", "--c"]))
rich.print(argparcel.parse(Moo, ["--b", "4", "--c", "--description", "moo moo"]))
rich.print(
    argparcel.parse(
        Moo,
        [
            "--b",
            "4",
            "--c",
            "--description",
            "moo moo",
            "--path",
            "/somewhere/over/the/rainbow",
        ],
    )
)

print()
print()


@dataclasses.dataclass(kw_only=True, frozen=True, slots=True)
class Moo2:
    choice: Literal[1, 2, 3] | None
    no_choice: Literal["foo", "bar"]


rich.print(argparcel.parse(Moo2, ["--choice", "2", "--no-choice", "bar"]))
rich.print(argparcel.parse(Moo2, ["--no-choice", "foo"]))
with contextlib.suppress(argparse.ArgumentError):
    rich.print(argparcel.parse(Moo2, [], exit_on_error=False))
