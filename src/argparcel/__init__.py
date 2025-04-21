from __future__ import annotations
import argparse
import dataclasses
import types
import typing

if typing.TYPE_CHECKING:
    import _typeshed
    from collections.abc import Sequence


def _fail(field: dataclasses.Field[typing.Any]) -> typing.Never:
    msg = f"Unsupported type for '{field.name}': {field.type}"
    raise ValueError(msg)


def parse[T: _typeshed.DataclassInstance](
    cls: type[T],
    command_line: Sequence[str] | None = None,
    *,
    exit_on_error: bool = True,
) -> T:
    """Parse arguments into an instance of `cls`."""
    parser = argparse.ArgumentParser(exit_on_error=exit_on_error)

    for field in dataclasses.fields(cls):
        name = f"--{field.name.replace('_', '-')}"

        no_default = field.default is dataclasses.MISSING

        if type(field.type) not in (type, types.UnionType):
            # NOTE: we do not yet support `types.GenericAlias` instances, e.g.
            #   `list[int]`
            _fail(field)
        field_type = typing.cast("type | types.UnionType", field.type)

        # If the type includes `None`, then we allow the type to
        if isinstance(field_type, types.UnionType):
            base_types = typing.get_args(field_type)
            allow_missing = any(issubclass(x, types.NoneType) for x in base_types)
            non_none_types = tuple(
                x for x in base_types if not issubclass(x, types.NoneType)
            )
            if len(non_none_types) != 1:
                _fail(field)
            base_type = non_none_types[0]

        else:
            allow_missing = False
            base_type = field_type

        # Build up the arguments for `parser.add_argument`
        kwargs: dict[str, typing.Any] = {}

        if not no_default:
            # We must only add an argument for the `default` if we have one to specify.
            # There isn't a sentinel value that we can use.
            if not isinstance(field.default, field_type):
                msg = (
                    f"Invalid {field.default = }; expected an instance of {field_type}"
                )
                raise ValueError(msg)
            kwargs["default"] = field.default

        # An argument is 'required' if the user MUST specify it on the command line.
        kwargs["required"] = no_default and (not allow_missing)

        if base_type is bool:
            parser.add_argument(name, action=argparse.BooleanOptionalAction, **kwargs)
        else:
            parser.add_argument(name, type=base_type, **kwargs)

    return cls(**parser.parse_args(command_line).__dict__)
