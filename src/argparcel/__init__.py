from __future__ import annotations

import argparse
import dataclasses
import enum
import types
import typing

if typing.TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    import _typeshed


__all__ = ["arg", "parse"]


_HELP_KEY = "help"
"""A key to use in the 'metadata' for a dataclasses field for argparcel help."""


def _ensure_field_type(
    name: str, type_: object
) -> (
    type
    | enum.EnumType
    | types.UnionType
    | typing._UnionGenericAlias  # pyright: ignore [reportAttributeAccessIssue]
    | typing._LiteralGenericAlias  # pyright: ignore [reportAttributeAccessIssue]
):
    if type(type_) not in (
        type,
        enum.EnumType,
        types.UnionType,
        typing._UnionGenericAlias,  # pyright: ignore [reportAttributeAccessIssue]  # noqa: SLF001
        typing._LiteralGenericAlias,  # pyright: ignore [reportAttributeAccessIssue]  # noqa: SLF001
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
    help_: str | None,
    required: bool,
    default: object,
    choices: Sequence | _Unspecified = _UNSPECIFIED,
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
        kwargs["type"] = type_
    if action is not _UNSPECIFIED:
        kwargs["action"] = action

    return parser.add_argument(name, help=help_, required=required, **kwargs)


def _add_argument_choices[T](
    parser: argparse.ArgumentParser,
    *,
    name: str,
    help_: str | None,
    required: bool,
    default: T,
    choices: Sequence[T],
    field_type: enum.EnumType | typing._LiteralGenericAlias,  # pyright: ignore [reportAttributeAccessIssue]
    field_name: str,
    type_: object = _UNSPECIFIED,
) -> argparse.Action:
    if len(choices) == 0:
        msg = f"Need at least one choice for field '{field_name}' of type {field_type}"
        raise ValueError(msg)

    if type_ is _UNSPECIFIED:
        choice_types = {type(x) for x in choices}
        # We enforce that all choices MUST all be of the same type, so that we can
        # convert them simply and unambiguously (e.g. `Literal[42, "42"]` could cause
        # problems).
        if len(choice_types) != 1:
            msg = (
                "Need exactly one type of choice. "
                f"Found {choice_types} for {field_type}, for field '{field_name}'"
            )
            raise ValueError(msg)

        (type_,) = choice_types

    return _add_argument(
        parser,
        name=name,
        type_=type_,
        choices=choices,
        help_=help_,
        required=required,
        default=default,
    )


def _add_argument_from_field(
    parser: argparse.ArgumentParser,
    field: dataclasses.Field,
    name_to_type: Mapping[str, object],
) -> None:
    name = f"--{field.name.replace('_', '-')}"
    no_default = field.default is dataclasses.MISSING
    field_type = _ensure_field_type(field.name, name_to_type[field.name])
    help_ = field.metadata.get(_HELP_KEY)
    if not (help_ is None or isinstance(help_, str)):
        msg = f"Unsupported help metadata for field '{field.name}': {help_!r}"
        raise ValueError(msg)

    if isinstance(
        field_type,
        types.UnionType | typing._UnionGenericAlias,  # pyright: ignore [reportAttributeAccessIssue]  # noqa: SLF001
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

    default = _UNSPECIFIED if no_default else field.default

    # An argument is 'required' if the user MUST specify it on the command line.
    required = no_default and (not allow_missing)

    if base_type is bool:
        # Represent boolean arguments as 'flags'
        _add_argument(
            parser=parser,
            name=name,
            action=argparse.BooleanOptionalAction,
            help_=help_,
            required=required,
            default=default,
        )

    elif isinstance(base_type, typing._LiteralGenericAlias):  # pyright: ignore [reportAttributeAccessIssue]  # noqa: SLF001
        # Represent literal arguments with choices.
        _add_argument_choices(
            parser,
            name=name,
            choices=typing.get_args(base_type),
            help_=help_,
            required=required,
            default=default,
            field_type=field.type,
            field_name=field.name,
        )

    elif isinstance(base_type, enum.EnumType):
        # FIXME: This is inconsistent.
        #   The help description lists the choices as e.g. `EnumName.a, EnumName.b`, but
        #   the users should just pass `a` and `b`. But if we change `choices` to be a
        #   sequence of strings, then the help becomes correct, but the parsing is then
        #   broken.
        _add_argument_choices(
            parser,
            name=name,
            type_=base_type.__getitem__,  # Look up the enum element by name.
            choices=tuple(base_type),  # Sequence of elements.
            help_=help_,
            required=required,
            default=default,
            field_type=field.type,
            field_name=field.name,
        )

    else:
        _add_argument(
            parser,
            name=name,
            type_=base_type,
            help_=help_,
            required=required,
            default=default,
        )


def arg(
    *,
    default: object = dataclasses.MISSING,
    help: str | None = None,  # noqa: A002
) -> typing.Any:  # noqa: ANN401
    """Create a dataclasses.Field in a way that argparcel understands."""
    return dataclasses.field(default=default, metadata={_HELP_KEY: help})


def parse[T: _typeshed.DataclassInstance](
    cls: type[T],
    command_line: Sequence[str] | None = None,
    *,
    exit_on_error: bool = False,
) -> T:
    """Parse arguments into an instance of `cls`."""
    parser = argparse.ArgumentParser(exit_on_error=exit_on_error)

    # If 'future annotations' are in use, `Field.type` may be a string. If we use
    # `get_type_hints`, then these will get resolved into the actual runtime types.
    name_to_type = typing.get_type_hints(cls)
    for field in dataclasses.fields(cls):
        _add_argument_from_field(parser, field, name_to_type)

    return cls(**parser.parse_args(command_line).__dict__)
