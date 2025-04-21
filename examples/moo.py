import dataclasses

import argparcel

import rich


@dataclasses.dataclass(frozen=True, slots=True)
class Moo:
    a: int | None
    b: float
    c: bool = True


rich.print(argparcel.parse(Moo, ["--a", "2", "--b", "3.2"]))
rich.print(argparcel.parse(Moo, ["--a", "2", "--b", "3.2", "--no-c"]))
