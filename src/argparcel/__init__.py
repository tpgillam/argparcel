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


__all__ = ["parse", "uses_types"]


def _duck_metaclass(x: object) -> type:
    """Construct a metaclass for a type that will mimic the type of x.

    Use the returned class as a metaclass, for example:

        class X(metaclass=_meta_duck_type(moo)):
            slots = ()

    Will construct a type X for which:
        - runtime isinstance and issubclass checks are based on the runtime type of
          `moo`
        - static typecheckers treat X as an opaque, but not "unknown", type

    In practice this is intended to be used for allowing annotation for entities we can
    obtain whose types are not publicly exposed.
    """

    class Meta(type):
        slots = ("type_",)
        type_ = type(x)

        def __instancecheck__(cls, instance: object, /) -> bool:
            return isinstance(instance, cls.type_)

        def __subclasscheck__(cls, subclass: type, /) -> bool:
            return issubclass(subclass, cls.type_)

    return Meta


class _LiteralGenericAlias(metaclass=_duck_metaclass(typing.Literal[1])):
    slots = ()


class _UnionGenericAlias(metaclass=_duck_metaclass(typing.Union[int, bool])):  # noqa: UP007
    slots = ()


class _UnpackGenericAlias(metaclass=_duck_metaclass(typing.Unpack[tuple[int, ...]])):
    slots = ()


def _ensure_field_type(
    name: str, type_: object
) -> (
    type
    | enum.EnumType
    | types.UnionType
    | types.GenericAlias
    | _UnionGenericAlias
    | _LiteralGenericAlias
):
    if not isinstance(
        type_,
        (
            type,
            enum.EnumType,
            types.UnionType,
            types.GenericAlias,
            _UnionGenericAlias,
            _LiteralGenericAlias,
        ),
    ):
        msg = f"Unsupported type for field '{name}': {type_}  (of type {type(type_)})"
        raise TypeError(msg)
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
    choices: Sequence[typing.Any] | _Unspecified = _UNSPECIFIED,
    type_: object = _UNSPECIFIED,
    action: type[argparse.Action] | _Unspecified = _UNSPECIFIED,
    nargs: int | typing.Literal["?", "+", "*"] | None | _Unspecified = _UNSPECIFIED,
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
    if nargs is not _UNSPECIFIED:
        kwargs["nargs"] = nargs

    return parser.add_argument(name, help=help_, required=required, **kwargs)


def _add_argument_choices[T](
    parser: argparse.ArgumentParser,
    *,
    name: str,
    help_: str | None,
    required: bool,
    default: T,
    choices: Sequence[T],
    field_type: enum.EnumType | _LiteralGenericAlias,
    field_name: str,
    choice_type: object = _UNSPECIFIED,
    nargs: int | typing.Literal["?", "+", "*"] | None | _Unspecified = _UNSPECIFIED,
) -> argparse.Action:
    if len(choices) == 0:
        msg = f"Need at least one choice for field '{field_name}' of type {field_type}"
        raise ValueError(msg)

    if choice_type is _UNSPECIFIED:
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

        (choice_type,) = choice_types

    return _add_argument(
        parser,
        name=name,
        type_=choice_type,
        choices=choices,
        help_=help_,
        required=required,
        default=default,
        nargs=nargs,
    )


def _add_argument_literal(
    parser: argparse.ArgumentParser,
    *,
    name: str,
    help_: str | None,
    required: bool,
    default: object,
    field_type: _LiteralGenericAlias,
    field_name: str,
    nargs: int | typing.Literal["?", "+", "*"] | None | _Unspecified = _UNSPECIFIED,
) -> _Unspecified:
    # Represent literal arguments with choices.
    _add_argument_choices(
        parser,
        name=name,
        choices=typing.get_args(field_type),
        help_=help_,
        required=required,
        default=default,
        field_type=field_type,
        field_name=field_name,
        nargs=nargs,
    )
    return _UNSPECIFIED


def _add_argument_enum[T: enum.Enum](
    parser: argparse.ArgumentParser,
    *,
    name: str,
    help_: str | None,
    required: bool,
    default: T | None | _Unspecified,
    field_type: type[T],
    field_name: str,
    nargs: int | typing.Literal["+", "*"] | None | _Unspecified = _UNSPECIFIED,
) -> Callable[[typing.Any], typing.Any]:
    # Enums are a bit awkward. We handle them in two stages:
    #   1. Let argparse treat them as a set of string choices, corresponding to the
    #       name of each enum element. Note that we also need to modify any default
    #       value to be consistent with this approach.
    #   2. Convert back to an enum element prior to populating the dataclass.
    #
    # Telling argparse about the enum directly is awkward, as discussed in:
    #   https://github.com/tpgillam/argparcel/issues/2
    enum_element_names: tuple[str, ...] = tuple(x.name for x in field_type)
    _add_argument_choices(
        parser,
        name=name,
        choice_type=str,
        choices=enum_element_names,  # Sequence of elements.
        help_=help_,
        required=required,
        default=(
            default
            if isinstance(default, _Unspecified | types.NoneType)
            else default.name
        ),
        field_type=field_type,
        field_name=field_name,
        nargs=nargs,
    )

    match nargs:
        case None | _Unspecified():

            def _lookup_enum_element(value: str | None) -> enum.EnumType | None:
                if value is None:
                    # Argument wasn't specified, so no conversion to do.
                    return None
                return getattr(field_type, value)

            return _lookup_enum_element

        case int() | "+" | "*":

            def _lookup_enum_elements(value: list[str]) -> list[enum.EnumType]:
                return [getattr(field_type, x) for x in value]

            return _lookup_enum_elements


def _tuplify(
    converter: Callable[[typing.Any], typing.Any] | _Unspecified,
) -> Callable[[typing.Any], typing.Any]:
    """Given a converter, return a new converter that converts the result to a tuple."""

    def f(value: Sequence[typing.Any] | None) -> tuple[typing.Any, ...] | None:
        if value is None:
            # 'None' is the value used to represent unspecified arguments, so we should
            # propagate that.
            return value

        if isinstance(converter, _Unspecified):
            return tuple(value)
        return tuple(converter(value))

    return f


def _add_argument_from_field(  # noqa: C901, PLR0911, PLR0912, PLR0915
    parser: argparse.ArgumentParser,
    field: dataclasses.Field[typing.Any],
    name_to_type: Mapping[str, object],
    name_to_help: Mapping[str, str],
) -> Callable[[typing.Any], typing.Any] | _Unspecified:
    if field.name.startswith("_"):
        msg = f"Field names must not start with an underscore; got {field.name!r}"
        raise ValueError(msg)
    arg_name = f"--{field.name.replace('_', '-')}"

    # An argument is 'required' if the user MUST specify it on the command line. We
    # equate this with the field on the dataclass not having a default value.
    required = field.default is dataclasses.MISSING

    field_type = _ensure_field_type(field.name, name_to_type[field.name])
    help_ = name_to_help.get(field.name)

    if isinstance(field_type, (types.UnionType, _UnionGenericAlias)):
        non_none_types = tuple(
            x for x in typing.get_args(field_type) if x is not types.NoneType
        )
        if len(non_none_types) != 1:
            msg = (
                f"Exactly one non-None type required for '{field.name}'; "
                f"got {field.type}"
            )
            raise ValueError(msg)
        base_type = non_none_types[0]
    else:
        base_type = field_type

    default = _UNSPECIFIED if required else field.default

    if base_type is bool:
        # Represent boolean arguments as 'flags'
        _add_argument(
            parser=parser,
            name=arg_name,
            action=argparse.BooleanOptionalAction,
            help_=help_,
            required=required,
            default=default,
        )
        return _UNSPECIFIED

    if isinstance(base_type, types.GenericAlias):
        origin = typing.get_origin(base_type)
        if origin is list:
            args = typing.get_args(base_type)
            if len(args) != 1:
                msg = f"Malformed list: {base_type}"
                raise ValueError(msg)
            (element_type,) = args
            # NOTE: providing a list-as-default here would be bad because mutable.
            #   This is currently prevented by dataclasses preventing assigning mutable
            #   defaults, so for now we don't try to handle this specially.

            if isinstance(element_type, _LiteralGenericAlias):
                return _add_argument_literal(
                    parser,
                    name=arg_name,
                    help_=help_,
                    required=required,
                    default=default,
                    field_type=element_type,
                    field_name=field.name,
                    nargs="*",
                )

            if isinstance(element_type, enum.EnumType):
                assert issubclass(element_type, enum.Enum)
                return _add_argument_enum(
                    parser,
                    name=arg_name,
                    help_=help_,
                    required=required,
                    default=default,
                    field_type=element_type,
                    field_name=field.name,
                    nargs="*",
                )

            _add_argument(
                parser,
                name=arg_name,
                help_=help_,
                required=required,
                default=default,
                type_=element_type,
                nargs="*",
            )
            return _UNSPECIFIED

        if origin is tuple:
            args = typing.get_args(base_type)

            if len(args) == 0:
                msg = f"Empty tuples not supported: {base_type}"
                raise ValueError(msg)

            if len(args) == 2 and isinstance(args[1], types.EllipsisType):
                # Variable-length tuple, e.g. tuple[int, ...]
                element_type = args[0]
                nargs = "*"

            elif isinstance(args[-1], _UnpackGenericAlias):
                # Variable-length tuple with at least N elements,
                #   e.g.: tuple[int, *tuple[int, ...]]
                # We only support a limited number of constructs here.
                *args_enforced, arg_unpack = args

                # TODO: This code is a bit fragile in its handling of unhappy paths.
                unpack_args = typing.get_args(arg_unpack)
                assert len(unpack_args) == 1
                assert isinstance(unpack_args[0], types.GenericAlias)
                assert typing.get_origin(unpack_args[0]) is tuple
                unpack_tuple_args = typing.get_args(unpack_args[0])

                if len(unpack_tuple_args) != 2 or not isinstance(
                    unpack_tuple_args[1], types.EllipsisType
                ):
                    msg = f"Unsupported Unpack: {arg_unpack}"
                    raise ValueError(msg)
                unpack_type = unpack_tuple_args[0]

                if len(args_enforced) > 1:
                    msg = f"Currently only '>=1' supported, not {base_type}"
                    raise NotImplementedError(msg)
                (arg_enforced,) = args_enforced
                if unpack_type != arg_enforced:
                    msg = (
                        "Only homogeneous tuples currently supported, "
                        f"found: {base_type}"
                    )
                    raise NotImplementedError(msg)

                element_type = unpack_type
                nargs = "+"

            else:
                unique_element_types = set(args)
                if len(unique_element_types) > 1:
                    msg = (
                        "Only homogeneous tuples currently supported, "
                        f"found: {base_type}"
                    )
                    raise NotImplementedError(msg)

                (element_type,) = unique_element_types
                nargs = len(args)

            if isinstance(element_type, _LiteralGenericAlias):
                return _tuplify(
                    _add_argument_literal(
                        parser,
                        name=arg_name,
                        help_=help_,
                        required=required,
                        default=default,
                        field_type=element_type,
                        field_name=field.name,
                        nargs=nargs,
                    )
                )

            if isinstance(element_type, enum.EnumType):
                assert issubclass(element_type, enum.Enum)
                return _tuplify(
                    _add_argument_enum(
                        parser,
                        name=arg_name,
                        help_=help_,
                        required=required,
                        default=default,
                        field_type=element_type,
                        field_name=field.name,
                        nargs=nargs,
                    )
                )

            _add_argument(
                parser,
                name=arg_name,
                help_=help_,
                required=required,
                default=default,
                type_=element_type,
                nargs=nargs,
            )
            return _tuplify(_UNSPECIFIED)

        msg = f"Unsupported GenericAlias: {base_type}"
        raise ValueError(msg)

    if isinstance(base_type, _LiteralGenericAlias):
        return _add_argument_literal(
            parser,
            name=arg_name,
            help_=help_,
            required=required,
            default=default,
            field_type=base_type,
            field_name=field.name,
        )

    if isinstance(base_type, enum.EnumType):
        assert issubclass(base_type, enum.Enum)
        return _add_argument_enum(
            parser,
            name=arg_name,
            help_=help_,
            required=required,
            default=default,
            field_type=base_type,
            field_name=field.name,
        )

    # Catch types that are not supported properly, and are probably accidental omissions
    if base_type is list:
        msg = "`list` must be subscripted; please use e.g. 'list[int]'"
        raise ValueError(msg)

    if base_type is tuple:
        msg = "`tuple` must be subscripted; please use e.g. 'tuple[int, int]'"
        raise ValueError(msg)

    _add_argument(
        parser,
        name=arg_name,
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
    converted_kwargs = {
        k: name_to_converter[k](v) if k in name_to_converter else v
        for k, v in kwargs.items()
    }

    return cls(**converted_kwargs)


def uses_types[T: type](*types: type) -> Callable[[T], T]:
    """Decorate a dataclass, and indicate types needed at runtime.

    The existence of this method is a somewhat disgusting workaround to let you, the
    user, declare to your static linting tools that a type is required at runtime, and
    that the import must not be moved into a `TYPE_CHECKING` block.
    """
    del types

    def f(cls: T, /) -> T:
        return cls

    return f
