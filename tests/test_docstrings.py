from __future__ import annotations

import dataclasses
from argparcel.docstrings import get_field_docstrings


@dataclasses.dataclass
class Example1:
    a: int
    """Message a."""

    b: int
    "Message b."

    c: float
    d: str | None = None
    """Message d."""


def test_get_field_docstrings() -> None:
    assert get_field_docstrings(Example1) == {
        "a": "Message a.",
        "b": "Message b.",
        "d": "Message d.",
    }
