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
class Args:
    a: int
    b: float

    # A `bool` argument will create a linked pair of flags `--c` and `--no-c`.
    c: bool

    # A command line argument will be optional if and only if a default value is
    # provided in the corresponding dataclass field.
    d: str | None = None


if __name__ == "__main__":
    print(argparcel.parse(Args))
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
Args(a=2, b=3.2, c=True, d=None)

$ uv run examples/example_0.py --a 2 --b 3.2 --no-c
Args(a=2, b=3.2, c=False, d=None)

$ uv run examples/example_0.py --a 2 --b 3.2 --no-c  --d moo
Args(a=2, b=3.2, c=False, d='moo')
```

We also support:
- `Literal` and `Enum`s forcing specific choices
- conversion to types whose `__init__` accepts a string, e.g. `pathlib.Path`
- annotated lists, e.g. `list[int]` or `list[pathlib.Path]`
- annotated homogeneous tuples, e.g. `tuple[int, int]` or `tuple[str, ...]`
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
class Args:
    # Using a `Literal` will force a choice between 1, 2, or 3.
    a: Literal[1, 2, 3]

    # An enum will force a choice between the names of the enum elements.
    b: Bird = Bird.puffin

    # A `Path` can be automatically converted from a string. Here we also specify a
    # 'help' message by using a 'docstring' for the field.
    c: pathlib.Path | None = None
    """An important path."""

    # A list will introduce a flag that consumes zero or more elements.
    d: list[float] | None = None

    # A tuple can require exactly a certain number of elements to be specified.
    e: tuple[int, int] | None = None

    # A tuple can also have an unknown number of elements.
    f: tuple[str, ...] | None = None

    # A tuple can also be required to have one or more elements.
    g: tuple[float, *tuple[float, ...]] | None = None


if __name__ == "__main__":
    print(argparcel.parse(Args))
```

```console
$ uv run examples/example_1.py --help
usage: example_1.py [-h] --a {1,2,3} [--b {puffin,lark}] [--c C] [--d [D ...]] [--e E E]

options:
  -h, --help         show this help message and exit
  --a {1,2,3}
  --b {puffin,lark}
  --c C              An important path.
  --d [D ...]
  --e E E


$ uv run examples/example_1.py --a 2
Args(a=2, b=<Bird.puffin: 1>, c=None, d=None, e=None)

$ uv run examples/example_1.py --a 2 --b lark --c /somewhere/to/go
Args(a=2, b=<Bird.lark: 2>, c=PosixPath('/somewhere/to/go'), d=None, e=None)

$ uv run examples/example_1.py --a 2 --b lark --d 1.0 2.0 3.0
Args(a=2, b=<Bird.lark: 2>, c=None, d=[1.0, 2.0, 3.0])

$ uv run examples/example_1.py --a 2 --e 4 5
Args(a=2, b=<Bird.puffin: 1>, c=None, d=None, e=(4, 5))
```

## Pitfall: forward-references

All types used in annotations _must_ be available at runtime.

Specifically, when you call `argparcel.parse(Args)`, internally it relies upon
`typings.get_type_hints(Args)` working. It will not work if any of the type annotations
for fields in `Args` can't be resolved at runtime. 

A plausible scenario for this to fail is when using forward references.

Forward references are used when:
- annotating with a string, or
- you have `from future import __annotations__` in the module, or
- you're using Python 3.14 or later.

In any of these cases, a linter rule like [ruff's TC003](https://docs.astral.sh/ruff/rules/typing-only-standard-library-import/) may encourage you to move an import into a `TYPE_CHECKING`-guarded block, like so:

```python
from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

import argparcel

if TYPE_CHECKING:
    from pathlib import Path


@dataclasses.dataclass
class Args:
    x: Path


argparcel.parse(Args)  # Raises NameError
```

But if you run this, you'll get:
```
<...snip stack trace...>
NameError: name 'Path' is not defined
```

### Solutions

If you run into this issue, take your pick from the following solutions:

1. Suppress your linter to permit the runtime import.
2. Alternatively, use the `argparcel.uses_types` decorator when defining the dataclass:

```python
@argparcel.uses_types(Path)
@dataclasses.dataclass
class Args:
    x: Path
```

This decorator is _only_ a convenience to allow the user to indicate to their linter
that the type is required. There's no requirement to specify all types that the
dataclass uses.

3. Use your own contrivance to ensure that the types are referenced at runtime.
