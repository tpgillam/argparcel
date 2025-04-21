# argparcel

A minimalist library to parse command-line arguments into a dataclass.

```python
import dataclasses

import argparcel


@dataclasses.dataclass(frozen=True, slots=True)
class Moo:
    a: int | None
    b: float
    c: bool = True
    description: str | None = None


print(argparcel.parse(Moo, ["--a", "2", "--b", "3.2"]))
print(argparcel.parse(Moo, ["--a", "2", "--b", "3.2", "--no-c"]))
print(argparcel.parse(Moo, ["--b", "4", "--c"]))
print(argparcel.parse(Moo, ["--b", "4", "--c", "--description", "moo moo"]))
print(
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
```

```console
Moo(a=2, b=3.2, path=None, c=True, description=None)
Moo(a=2, b=3.2, path=None, c=False, description=None)
Moo(a=None, b=4.0, path=None, c=True, description=None)
Moo(a=None, b=4.0, path=None, c=True, description='moo moo')
Moo(
    a=None,
    b=4.0,
    path=PosixPath('/somewhere/over/the/rainbow'),
    c=True,
    description='moo moo'
)

usage: moo.py [-h] [--a A] --b B [--path PATH] [--c | --no-c]
              [--description DESCRIPTION]
```

```python
class Thingy(enum.Enum):
    a = enum.auto()
    b = enum.auto()


@dataclasses.dataclass(kw_only=True, frozen=True, slots=True)
class Moo2:
    choice: Literal[1, 2, 3] | None
    no_choice: Literal["foo", "bar"] = argparcel.help("baz")
    thingy: Thingy = Thingy.a


argparcel.parse(Moo2, ["--help"])
```

```console
usage: moo.py [-h] [--choice {1,2,3}] --no-choice {foo,bar}
              [--thingy {Thingy.a,Thingy.b}]

options:
  -h, --help            show this help message and exit
  --choice {1,2,3}
  --no-choice {foo,bar}
                        baz
  --thingy {Thingy.a,Thingy.b}
```
