import dataclasses
import rich

import argparcel


@dataclasses.dataclass(frozen=True, slots=True)
class Moo:
    a: int | None
    b: float
    c: bool = True
    description: str | None = None


rich.print(argparcel.parse(Moo, ["--a", "2", "--b", "3.2"]))
rich.print(argparcel.parse(Moo, ["--a", "2", "--b", "3.2", "--no-c"]))
rich.print(argparcel.parse(Moo, ["--b", "4", "--c"]))
rich.print(argparcel.parse(Moo, ["--b", "4", "--c", "--description", "moo moo"]))
