"""Utility to parse 'field docstrings' from a dataclass.

Static-analysis tools like pyright will interpret strings that appear immediately after
the definition of a field in a dataclass as documentation for that field, so this is an
'expected' concept. However, it is _not_ a feature of the Python runtime.

For that reason we resort to some dastardly AST inspection to extract the messages.
"""

from __future__ import annotations

import ast
import inspect
import typing

if typing.TYPE_CHECKING:
    import _typeshed


def get_field_docstrings(cls: type[_typeshed.DataclassInstance]) -> dict[str, str]:
    """Extracts 'docstrings' for all fields in a dataclass, if present.

    If a 'docstring' is not found for a given field, it will not be included in the
    output.
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

    # Walk through the class body to collect field docstrings
    i = 0
    while i < len(class_node.body):
        node = class_node.body[i]

        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            field_name = node.target.id
            docstring: str | None = None

            # Check if the next statement is a string literal
            if i + 1 < len(class_node.body):
                next_node = class_node.body[i + 1]
                if (
                    isinstance(next_node, ast.Expr)
                    and isinstance(next_node.value, ast.Constant)
                    and isinstance(next_node.value.value, str)
                ):
                    docstring = next_node.value.value
                    i += 1  # Skip over the docstring node

            if docstring is not None:
                result[field_name] = docstring

        i += 1

    return result
