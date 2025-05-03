"""Dangerously magical AST-based utilities."""

from __future__ import annotations

import ast
import importlib
import inspect
import itertools
import types
import typing

if typing.TYPE_CHECKING:
    import _typeshed


def get_field_docstrings(cls: type[_typeshed.DataclassInstance]) -> dict[str, str]:
    """Extracts any 'field docstrings' present in `cls`.

    Returns a mapping from field name -> docstring, only for fields with which strings
    can be associated.


    Static-analysis tools like pyright will interpret strings that appear immediately
    after the definition of a field in a dataclass as documentation for that field, so
    this is an 'expected' concept. However, it is _not_ a feature of the Python runtime.

    For that reason we resort to some dastardly AST inspection to extract the messages.
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


def _is_type_checking_block(node: ast.AST) -> typing.TypeGuard[ast.If]:
    """Returns True if the given AST node is an `if TYPE_CHECKING:` block."""
    if not isinstance(node, ast.If):
        return False

    test = node.test
    if isinstance(test, ast.Name):
        return test.id == "TYPE_CHECKING"
    if isinstance(test, ast.Attribute):
        return (
            isinstance(test.value, ast.Name)
            and test.value.id == "typing"
            and test.attr == "TYPE_CHECKING"
        )
    return False


def _module_globals_including_type_checking(
    module: types.ModuleType,
) -> dict[str, typing.Any]:
    """Get the global namespace for `module`... including imports in TYPE_CHECKING."""
    source = inspect.getsource(module)
    globalns = dict(vars(module))

    tree = ast.parse(source)

    for node in tree.body:
        if not _is_type_checking_block(node):
            continue

        for stmt in node.body:
            if isinstance(stmt, ast.Import):
                for alias in stmt.names:
                    mod = importlib.import_module(alias.name)
                    asname = alias.asname or alias.name
                    globalns[asname] = mod

            elif isinstance(stmt, ast.ImportFrom):
                modname = stmt.module
                assert modname is not None
                mod = importlib.import_module(modname)
                for alias in stmt.names:
                    name = alias.name
                    asname = alias.asname or name
                    globalns[asname] = getattr(mod, name)

    return globalns


def get_type_hints(cls: type[_typeshed.DataclassInstance]) -> dict[str, typing.Any]:
    """A more magical version of `typing.get_type_hints`.

    This version will _also_ consider imports made in a TYPE_CHECKING block of the
    module in which `cls` is defined.
    """
    module_name = cls.__module__
    module = importlib.import_module(module_name)
    return typing.get_type_hints(
        cls, globalns=_module_globals_including_type_checking(module)
    )
