# argparcel

Parse command-line arguments into a dataclass.

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
```

```python
Moo(a=2, b=3.2, c=True)
Moo(a=2, b=3.2, c=False)
Moo(a=None, b=4.0, c=True)
Moo(a=None, b=4.0, c=True, description='moo moo')
```
