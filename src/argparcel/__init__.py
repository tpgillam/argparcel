from __future__ import annotations

import argparse
import dataclasses
import enum
import types
import typing

from argparcel.docstrings import get_field_docstrings

if typing.TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    import _typeshed


__all__ = ["parse"]


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
    name_to_help: Mapping[str, str],
) -> Callable[[typing.Any], typing.Any] | _Unspecified:
    name = f"--{field.name.replace('_', '-')}"

    # An argument is 'required' if the user MUST specify it on the command line. We
    # equate this with the field on the dataclass not having a default value.
    required = field.default is dataclasses.MISSING

    field_type = _ensure_field_type(field.name, name_to_type[field.name])
    help_ = name_to_help.get(field.name)
    if not (help_ is None or isinstance(help_, str)):
        msg = f"Unsupported help metadata for field '{field.name}': {help_!r}"
        raise ValueError(msg)

    if isinstance(
        field_type,
        types.UnionType | typing._UnionGenericAlias,  # pyright: ignore [reportAttributeAccessIssue]  # noqa: SLF001
    ):
        base_types = typing.get_args(field_type)
        assert len(base_types) > 0
        non_none_types = tuple(x for x in base_types if x is not types.NoneType)
        if len(non_none_types) != 1:
            msg = f"More than one non-None type given for '{field.name}'; {field.type}"
            raise ValueError(msg)
        base_type = non_none_types[0]
    else:
        base_type = field_type

    default = _UNSPECIFIED if required else field.default

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
        return _UNSPECIFIED

    if isinstance(base_type, typing._LiteralGenericAlias):  # pyright: ignore [reportAttributeAccessIssue]  # noqa: SLF001
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
        return _UNSPECIFIED

    if isinstance(base_type, enum.EnumType):
        # Enums are a bit awkward. We handle them in two stages:
        #   1. Let argparse treat them as a set of string choices, corresponding to the
        #       name of each enum element. Note that we also need to modify any default
        #       value to be consistent with this approach.
        #   2. Convert back to an enum element prior to populating the dataclass.
        #
        # Telling argparse about the enum directly is awkward, as discussed in:
        #   https://github.com/tpgillam/argparcel/issues/2
        enum_element_names: tuple[str, ...] = tuple(
            x.name  # pyright: ignore[reportAttributeAccessIssue]
            for x in base_type
        )
        _add_argument_choices(
            parser,
            name=name,
            type_=str,
            choices=enum_element_names,  # Sequence of elements.
            help_=help_,
            required=required,
            default=(
                default
                if isinstance(default, _Unspecified | types.NoneType)
                else default.name
            ),
            field_type=field.type,
            field_name=field.name,
        )

        def _lookup_enum_element(value: str | None) -> enum.EnumType | None:
            if value is None:
                # Argument wasn't specified, so no conversion to do.
                return None
            return getattr(base_type, value)

        return _lookup_enum_element

    _add_argument(
        parser,
        name=name,
        type_=base_type,
        help_=help_,
        required=required,
        default=default,
    )
    return _UNSPECIFIED


def parse[T: _typeshed.DataclassInstance](
    cls: type[T],
    command_line: Sequence[str] | None = None,
    *,
    exit_on_error: bool = True,
) -> T:
    """Parse arguments into an instance of `cls`."""
    parser = argparse.ArgumentParser(exit_on_error=exit_on_error)

    # If 'future annotations' are in use, `Field.type` may be a string. If we use
    # `get_type_hints`, then these will get resolved into the actual runtime types.
    name_to_type = typing.get_type_hints(cls)

    # Get the 'help' messages from any 'docstrings'.
    name_to_help = get_field_docstrings(cls)

    # A mapping from argument name to a function that should be applied to whatever we
    # get out of argparse, to give us the value we should give to the dataclass
    # constructor.
    name_to_converter: dict[str, Callable[[typing.Any], typing.Any]] = {}

    for field in dataclasses.fields(cls):
        converter = _add_argument_from_field(parser, field, name_to_type, name_to_help)
        if not isinstance(converter, _Unspecified):
            name_to_converter[field.name] = converter

    # Get the raw arguments from argparse.
    kwargs = parser.parse_args(command_line).__dict__

    # Now apply any conversions required before constructing the dataclass.
    converted_kwargs: dict[str, typing.Any] = {
        k: name_to_converter[k](v) if k in name_to_converter else v
        for k, v in kwargs.items()
    }

    return cls(**converted_kwargs)
