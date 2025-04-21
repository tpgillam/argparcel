import dataclasses
import pathlib
import rich

import argparcel


@dataclasses.dataclass(kw_only=True, frozen=True, slots=True)
class Moo:
    a: int | None
    b: float
    path: pathlib.Path | None
    c: bool = True
    description: str | None = None


rich.print(argparcel.parse(Moo, ["--a", "2", "--b", "3.2"]))
rich.print(argparcel.parse(Moo, ["--a", "2", "--b", "3.2", "--no-c"]))
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
rich.print(argparcel.parse(Moo, ["--help"]))
