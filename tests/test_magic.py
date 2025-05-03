from __future__ import annotations

import dataclasses

from argparcel.magic import get_field_docstrings


@dataclasses.dataclass
class Example1:
    a: int
    """Message a."""

    b: int
    "Message b."

    c: float
    d: str | None = None
    """Message d."""


@dataclasses.dataclass
class Example2:
    """Class docstring."""

    """No-op string."""
    a: int
    # Line deliberately left blank
    """Message a.

    This continues over multiple lines.
    """


def test_get_field_docstrings() -> None:
    assert get_field_docstrings(Example1) == {
        "a": "Message a.",
        "b": "Message b.",
        "d": "Message d.",
    }

    assert get_field_docstrings(Example2) == {
        "a": """Message a.

    This continues over multiple lines.
    """
    }
