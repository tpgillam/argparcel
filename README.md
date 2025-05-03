# argparcel

[![image](https://img.shields.io/pypi/v/argparcel.svg)](https://pypi.python.org/pypi/argparcel)
[![image](https://img.shields.io/pypi/l/argparcel.svg)](https://github.com/tpgillam/argparcel/blob/main/LICENSE)
[![image](https://img.shields.io/pypi/pyversions/argparcel.svg)](https://pypi.python.org/pypi/argparcel)
[![Actions status](https://github.com/tpgillam/argparcel/workflows/CI/badge.svg)](https://github.com/tpgillam/argparcel/actions)

A minimalist library to parse command-line arguments into a dataclass.

## Example usage
```python
# examples/example_0.py
import dataclasses

import argparcel


@dataclasses.dataclass(kw_only=True, frozen=True, slots=True)
class _Args:
    a: int
    b: float

    # A `bool` argument will create a linked pair of flags `--c` and `--no-c`.
    c: bool

    # A command line argument will be optional if and only if a default value is
    # provided in the corresponding dataclass field.
    d: str | None = None


if __name__ == "__main__":
    print(argparcel.parse(_Args))
```

```console
$ uv run examples/example_0.py --help
usage: example_0.py [-h] --a A --b B --c | --no-c [--d D]

options:
  -h, --help   show this help message and exit
  --a A
  --b B
  --c, --no-c
  --d D

$ uv run examples/example_0.py --a 2 --b 3.2 --c
_Args(a=2, b=3.2, c=True, d=None)

$ uv run examples/example_0.py --a 2 --b 3.2 --no-c
_Args(a=2, b=3.2, c=False, d=None)

$ uv run examples/example_0.py --a 2 --b 3.2 --no-c  --d moo
_Args(a=2, b=3.2, c=False, d='moo')
```

We also support:
- `Literal` and `Enum`s forcing specific choices
- conversion to types whose `__init__` accepts a string, e.g. `pathlib.Path`
- 'help' can be provided too

```python
# examples/example_1.py
import dataclasses
import enum
import pathlib 
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
    # 'help' message by using a 'docstring' for the field.
    c: pathlib.Path | None = None
    """An important path."""


if __name__ == "__main__":
    print(argparcel.parse(_Args))
```

```console
$ uv run examples/example_1.py --help
usage: example_1.py [-h] --a {1,2,3} [--b {puffin,lark}] [--c C]

options:
  -h, --help         show this help message and exit
  --a {1,2,3}
  --b {puffin,lark}
  --c C              An important path.

$ uv run examples/example_1.py --a 2
_Args(a=2, b=<Bird.puffin: 1>, c=None)

$ uv run examples/example_1.py --a 2 --b lark --c /somewhere/to/go
_Args(a=2, b=<Bird.lark: 2>, c=PosixPath('/somewhere/to/go'))
```
