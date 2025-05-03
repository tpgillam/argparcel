# argparcel

[![image](https://img.shields.io/pypi/v/argparcel.svg)](https://pypi.python.org/pypi/argparcel)
[![image](https://img.shields.io/pypi/l/argparcel.svg)](https://github.com/tpgillam/argparcel/blob/main/LICENSE)
[![image](https://img.shields.io/pypi/pyversions/argparcel.svg)](https://pypi.python.org/pypi/argparcel)
[![Actions status](https://github.com/tpgillam/argparcel/workflows/CI/badge.svg)](https://github.com/tpgillam/argparcel/actions)

A minimalist library to parse command-line arguments into a dataclass.

## Example usage
```python
import dataclasses
from typing import Literal

import argparcel


@dataclasses.dataclass(kw_only=True, frozen=True, slots=True)
class _Args:
    a: int
    b: float
    c: Literal[1, 2, 3] = argparcel.arg(help="choose wisely")
    d: bool = True
    e: str | None = None


if __name__ == "__main__":
    print(argparcel.parse(_Args))
```

```console
$ python examples/example_0.py --help
usage: example_0.py [-h] --a A --b B --c {1,2,3} [--d | --no-d] [--e E]

options:
  -h, --help   show this help message and exit
  --a A
  --b B
  --c {1,2,3}  choose wisely
  --d, --no-d
  --e E

$ python examples/example_0.py --a 2 --b 3.2 --c 1
_Args(a=2, b=3.2, c=1, d=True, e=None)

$ python examples/example_0.py --a 2 --b 3.2 --c 1 --no-d
_Args(a=2, b=3.2, c=1, d=False, e=None)

$ python examples/example_0.py --a 2 --b 3.2 --c 1 --no-d  --e moo
_Args(a=2, b=3.2, c=1, d=False, e='moo')
```

Another example:
```python
class Thingy(enum.Enum):
    a = enum.auto()
    b = enum.auto()


@dataclasses.dataclass(kw_only=True, frozen=True, slots=True)
class Moo2:
    choice: Literal[1, 2, 3] | None = None
    no_choice: Literal["foo", "bar"] = argparcel.arg(help="baz")
    thingy: Thingy = Thingy.a


argparcel.parse(Moo2, ["--help"])
```

```console
usage: moo.py [-h] [--choice {1,2,3}] --no-choice {foo,bar} [--thingy {a,b}]

options:
  -h, --help            show this help message and exit
  --choice {1,2,3}
  --no-choice {foo,bar}
                        baz
  --thingy {a,b}
```
