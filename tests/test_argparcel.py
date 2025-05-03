from __future__ import annotations

import contextlib
import dataclasses
import enum
import io
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


@dataclasses.dataclass(kw_only=True, frozen=True, slots=True)
class MooLiteral:
    optional_choice: Literal[1, 2, 3] | None
    choice: Literal["foo", "bar"]
    defaulted_choice: Literal["a", "b", "c"] = "c"


def test_literals() -> None:
    assert argparcel.parse(MooLiteral, ["--choice", "foo"]) == MooLiteral(
        optional_choice=None, choice="foo", defaulted_choice="c"
    )
    assert argparcel.parse(
        MooLiteral, ["--optional-choice", "1", "--choice", "foo"]
    ) == MooLiteral(optional_choice=1, choice="foo", defaulted_choice="c")
    assert argparcel.parse(
        MooLiteral,
        ["--optional-choice", "1", "--choice", "foo", "--defaulted-choice", "a"],
    ) == MooLiteral(optional_choice=1, choice="foo", defaulted_choice="a")


class Thingy(enum.Enum):
    a = enum.auto()
    b = enum.auto()


@dataclasses.dataclass(kw_only=True, frozen=True, slots=True)
class MooEnum:
    x: Thingy = Thingy.a
    y: Thingy
    z: Thingy | None


def test_enum() -> None:
    with (
        contextlib.redirect_stdout(io.StringIO()) as f,
        contextlib.suppress(SystemExit),
    ):
        argparcel.parse(MooEnum, ["--help"])
    help_text = f.getvalue()
    assert (
        """usage: pytest [-h] [--x {a,b}] --y {a,b} [--z {a,b}]

options:
  -h, --help  show this help message and exit
  --x {a,b}
  --y {a,b}
  --z {a,b}
"""
        in help_text
    )

    assert argparcel.parse(MooEnum, ["--y", "a"]) == MooEnum(
        x=Thingy.a, y=Thingy.a, z=None
    )
    assert argparcel.parse(MooEnum, ["--y", "b"]) == MooEnum(
        x=Thingy.a, y=Thingy.b, z=None
    )
    assert argparcel.parse(MooEnum, ["--x", "b", "--y", "b"]) == MooEnum(
        x=Thingy.b, y=Thingy.b, z=None
    )
    assert argparcel.parse(MooEnum, ["--y", "b", "--z", "b"]) == MooEnum(
        x=Thingy.a, y=Thingy.b, z=Thingy.b
    )
