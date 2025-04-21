from __future__ import annotations
import argparse
import dataclasses
import types
import typing

if typing.TYPE_CHECKING:
    import _typeshed
    from collections.abc import Sequence
    from collections.abc import Iterable


HELP_KEY = "help"
"""A key to use in the 'metadata' for a dataclasses field for argparcel help."""


def _ensure_field_type(
    name: str, type_: object
) -> (
    type
    | types.UnionType
    | typing._UnionGenericAlias  # pyright: ignore [reportAttributeAccessIssue]
    | typing._LiteralGenericAlias  # pyright: ignore [reportAttributeAccessIssue]
):
    if type(type_) not in (
        type,
        types.UnionType,
        typing._UnionGenericAlias,  # pyright: ignore [reportAttributeAccessIssue]
        typing._LiteralGenericAlias,  # pyright: ignore [reportAttributeAccessIssue]
    ):
        msg = f"Unsupported type for field '{name}': {type_}  (of type {type(type_)})"
        raise ValueError(msg)
    return type_


class _Unspecified:
    pass


_UNSPECIFIED = _Unspecified()


def _add_argument(
    parser: argparse.ArgumentParser,
    *,
    name: str,
    help: str | None,
    required: bool,
    default: object,
    choices: Iterable | _Unspecified = _UNSPECIFIED,
    type_: object = _UNSPECIFIED,
    action: type[argparse.Action] | _Unspecified = _UNSPECIFIED,
) -> argparse.Action:
    # Build up common arguments for `parser.add_argument` into this dictionary. This is
    # the easiest way for us to avoid passing in arguments that should be unspecified.
    kwargs: dict[str, typing.Any] = {}
    if default is not _UNSPECIFIED:
        kwargs["default"] = default
    if choices is not _UNSPECIFIED:
        kwargs["choices"] = choices
    if type_ is not _UNSPECIFIED:
        kwargs["type"] = type
    if action is not _UNSPECIFIED:
        kwargs["action"] = action

    return parser.add_argument(name, help=help, required=required, **kwargs)


def _add_argument_from_field(
    parser: argparse.ArgumentParser, field: dataclasses.Field
) -> None:
    name = f"--{field.name.replace('_', '-')}"
    no_default = field.default is dataclasses.MISSING
    field_type = _ensure_field_type(field.name, field.type)
    help = field.metadata.get(HELP_KEY)

    if isinstance(
        field_type,
        types.UnionType | typing._UnionGenericAlias,  # pyright: ignore [reportAttributeAccessIssue]
    ):
        base_types = typing.get_args(field_type)
        allow_missing = any(x is types.NoneType for x in base_types)
        non_none_types = tuple(x for x in base_types if x is not types.NoneType)
        if len(non_none_types) != 1:
            msg = f"Can only support one non-None type for '{field.name}': {field.type}"
            raise ValueError(msg)
        base_type = non_none_types[0]

    else:
        allow_missing = False
        base_type = field_type

    if no_default:
        default = _UNSPECIFIED
    else:
        # We must only add an argument for the `default` if we have one to specify.
        # There isn't a sentinel value that we can use.
        if not isinstance(field.default, field_type):
            msg = f"Invalid {field.default = }; expected an instance of {field_type}"
            raise ValueError(msg)
        default = field.default

    # An argument is 'required' if the user MUST specify it on the command line.
    required = no_default and (not allow_missing)

    if base_type is bool:
        # Represent boolean arguments as 'flags'
        _add_argument(
            parser=parser,
            name=name,
            action=argparse.BooleanOptionalAction,
            help=help,
            required=required,
            default=default,
        )

    elif isinstance(base_type, typing._LiteralGenericAlias):  # pyright: ignore [reportAttributeAccessIssue]
        # Represent literal arguments with choices.
        # We enforce that they MUST all be of the same type, so that we can convert
        # them simply and unambiguously (e.g. `Literal[42, "42"]` could cause
        # problems).
        choices = typing.get_args(base_type)
        choice_types = {type(x) for x in choices}
        if len(choice_types) != 1:
            msg = (
                "Need exactly one type of choice. "
                f"Found {choice_types} for {field_type}, for field '{field.name}'"
            )
            raise ValueError(msg)
        (type_,) = choice_types
        _add_argument(
            parser,
            name=name,
            type_=type_,
            choices=choices,
            help=help,
            required=required,
            default=default,
        )

    else:
        _add_argument(
            parser,
            name=name,
            type_=base_type,
            help=help,
            required=required,
            default=default,
        )


def help(message: str, /) -> typing.Any:
    """Create a dataclasses field with the argparcel help populated."""
    return dataclasses.field(metadata={HELP_KEY: message})


def parse[T: _typeshed.DataclassInstance](
    cls: type[T],
    command_line: Sequence[str] | None = None,
    *,
    exit_on_error: bool = True,
) -> T:
    """Parse arguments into an instance of `cls`."""
    parser = argparse.ArgumentParser(exit_on_error=exit_on_error)

    for field in dataclasses.fields(cls):
        _add_argument_from_field(parser, field)

    return cls(**parser.parse_args(command_line).__dict__)
