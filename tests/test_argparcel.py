from __future__ import annotations

import dataclasses
import pathlib
from typing import Literal

import argparcel


@dataclasses.dataclass(kw_only=True, frozen=True, slots=True)
class Moo:
    a: int | None
    b: float
    choice: Literal[1, 2, 3] | None = argparcel.arg(help="choose wisely")
    path: pathlib.Path | None
    c: bool = True
    description: str | None = None


def test_happy_paths() -> None:
    assert argparcel.parse(Moo, ["--a", "2", "--b", "3.2", "--choice", "1"]) == Moo(
        a=2, b=3.2, choice=1, path=None, c=True, description=None
    )
    assert argparcel.parse(
        Moo, ["--a", "2", "--b", "3.2", "--no-c", "--choice", "3"]
    ) == Moo(a=2, b=3.2, choice=3, path=None, c=False, description=None)
    assert argparcel.parse(Moo, ["--b", "4", "--c"]) == Moo(
        a=None, b=4, choice=None, path=None, c=True, description=None
    )
    assert argparcel.parse(Moo, ["--b", "4", "--c", "--description", "moo moo"]) == Moo(
        a=None, b=4, choice=None, path=None, c=True, description="moo moo"
    )
    assert argparcel.parse(
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
    ) == Moo(
        a=None,
        b=4,
        choice=None,
        path=pathlib.Path("/somewhere/over/the/rainbow"),
        c=True,
        description="moo moo",
    )
