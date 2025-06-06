from __future__ import annotations

import argparse
import contextlib
import dataclasses
import enum
import io
import pathlib
from typing import TYPE_CHECKING, Literal

import pytest

import argparcel

if TYPE_CHECKING:
    import _typeshed


@dataclasses.dataclass(kw_only=True, frozen=True, slots=True)
class Moo:
    a: int | None = None
    b: float
    choice: Literal[1, 2, 3] | None = None
    """choose wisely"""

    path: pathlib.Path | None = None
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
    optional_choice: Literal[1, 2, 3] | None = None
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


class ThingyStr(enum.StrEnum):
    a = enum.auto()
    b = enum.auto()


class ThingyInt(enum.IntEnum):
    a = 1
    b = 42


@dataclasses.dataclass(kw_only=True, frozen=True, slots=True)
class MooEnum:
    x: Thingy = Thingy.a
    y: Thingy
    z: Thingy | None = None


@dataclasses.dataclass(kw_only=True, frozen=True, slots=True)
class MooStrEnum:
    x: ThingyStr = ThingyStr.a
    y: ThingyStr
    z: ThingyStr | None = None


@dataclasses.dataclass(kw_only=True, frozen=True, slots=True)
class MooIntEnum:
    x: ThingyInt = ThingyInt.a
    y: ThingyInt
    z: ThingyInt | None = None


def _get_help_text(cls: type[_typeshed.DataclassInstance]) -> str:
    """Get the output of `--help` if using argparcel with `cls`."""
    with contextlib.redirect_stdout(io.StringIO()) as f, pytest.raises(SystemExit):
        argparcel.parse(cls, ["--help"])
    return f.getvalue()


def test_enum_help() -> None:
    for type_ in (MooEnum, MooStrEnum, MooIntEnum):
        help_text = _get_help_text(type_)
        assert (
            """[-h] [--x {a,b}] --y {a,b} [--z {a,b}]

options:
  -h, --help  show this help message and exit
  --x {a,b}
  --y {a,b}
  --z {a,b}
"""
            in help_text
        )


def test_enum() -> None:
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


def test_str_enum() -> None:
    assert argparcel.parse(MooStrEnum, ["--y", "a"]) == MooStrEnum(
        x=ThingyStr.a, y=ThingyStr.a, z=None
    )
    assert argparcel.parse(MooStrEnum, ["--y", "b"]) == MooStrEnum(
        x=ThingyStr.a, y=ThingyStr.b, z=None
    )
    assert argparcel.parse(MooStrEnum, ["--x", "b", "--y", "b"]) == MooStrEnum(
        x=ThingyStr.b, y=ThingyStr.b, z=None
    )
    assert argparcel.parse(MooStrEnum, ["--y", "b", "--z", "b"]) == MooStrEnum(
        x=ThingyStr.a, y=ThingyStr.b, z=ThingyStr.b
    )


def test_int_enum() -> None:
    assert argparcel.parse(MooIntEnum, ["--y", "a"]) == MooIntEnum(
        x=ThingyInt.a, y=ThingyInt.a, z=None
    )
    assert argparcel.parse(MooIntEnum, ["--y", "b"]) == MooIntEnum(
        x=ThingyInt.a, y=ThingyInt.b, z=None
    )
    assert argparcel.parse(MooIntEnum, ["--x", "b", "--y", "b"]) == MooIntEnum(
        x=ThingyInt.b, y=ThingyInt.b, z=None
    )
    assert argparcel.parse(MooIntEnum, ["--y", "b", "--z", "b"]) == MooIntEnum(
        x=ThingyInt.a, y=ThingyInt.b, z=ThingyInt.b
    )


@dataclasses.dataclass
class ArgsRequiredFlag:
    a: bool


def test_missing_argument() -> None:
    with pytest.raises(argparse.ArgumentError, match="arguments are required: --b"):
        argparcel.parse(Moo, [], exit_on_error=False)
    with pytest.raises(
        argparse.ArgumentError, match="arguments are required: --a/--no-a"
    ):
        argparcel.parse(ArgsRequiredFlag, [], exit_on_error=False)


@dataclasses.dataclass
class BadUnderscore1:
    _a: bool


@dataclasses.dataclass
class BadUnderscore2:
    # pyright tells us we're not allowed to do this. For the sake of our testing, let's
    # brute force it.
    __a: bool  # pyright: ignore [reportGeneralTypeIssues]

    def moo(self) -> bool:
        # This exists purely so pyright doesn't see `__a` as being unaccessed.
        return self.__a


def test_bad_underscores() -> None:
    with pytest.raises(
        ValueError, match="Field names must not start with an underscore; got '_a'"
    ):
        argparcel.parse(BadUnderscore1, ["--help"])

    with pytest.raises(
        ValueError,
        match="Field names must not start with an underscore; got '_BadUnderscore2__a'",
    ):
        argparcel.parse(BadUnderscore2, ["--help"])


@dataclasses.dataclass
class MooWithMethods:
    a: bool

    @property
    def b(self) -> bool:
        return self.a

    def c(self) -> bool:
        return self.a


def test_properties_and_methods_ok() -> None:
    # The presence of properties and methods should not impact parsing; they do not
    # count as fields and therefore should not be added as arguments.
    help_text = _get_help_text(MooWithMethods)
    assert (
        """[-h] --a | --no-a

options:
  -h, --help   show this help message and exit
  --a, --no-a
"""
        in help_text
    )

    assert argparcel.parse(MooWithMethods, ["--a"]) == MooWithMethods(a=True)
