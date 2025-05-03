"""Utility to parse 'field docstrings' from a dataclass.

Static-analysis tools like pyright will interpret strings that appear immediately after
the definition of a field in a dataclass as documentation for that field, so this is an
'expected' concept. However, it is _not_ a feature of the Python runtime.

For that reason we resort to some dastardly AST inspection to extract the messages.
"""

from __future__ import annotations

import ast
import inspect
import itertools
import typing

if typing.TYPE_CHECKING:
    import _typeshed


def get_field_docstrings(cls: type[_typeshed.DataclassInstance]) -> dict[str, str]:
    """Extracts any 'field docstrings' present in `cls`.

    Returns a mapping from field name -> docstring, only for fields with which strings
    can be associated.
    """
    # Obtaining the source code might fail with an exception; we let that propagate up
    # to the user.
    source = inspect.getsource(cls)
    tree = ast.parse(source)

    # Find the class definition node; if it doesn't exist something is fundamentally
    # broken, so we are happy with an assert.
    class_node = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == cls.__name__
        ),
        None,
    )
    assert class_node is not None

    result: dict[str, str] = {}

    # Walk through the class body to collect field docstrings. We're looking for pairs
    # of field definition followed by a docstring.
    for node, next_node in itertools.pairwise(class_node.body):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            field_name = node.target.id

            if (
                isinstance(next_node, ast.Expr)
                and isinstance(next_node.value, ast.Constant)
                and isinstance(next_node.value.value, str)
            ):
                result[field_name] = next_node.value.value

    return result
