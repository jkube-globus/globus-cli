from __future__ import annotations

import typing as t
from urllib.parse import urlparse

import click

from globus_cli.constants import EXPLICIT_NULL, ExplicitNullType


def nullable_multi_callback(null: t.Any = "null") -> t.Callable[..., t.Any]:
    """
    A callback which converts multiple=True options as follows:
    - empty results, [] => None
    - [<null>,] => []
    - anything else => passthrough

    This makes the null value explicit, and not setting it results in omission, not
    clearing.

    The null value used here is tunable. If set to a non-string value when using a
    string type, like `None`, it means that "there is no null value" because
    there is no way to pass `[]`

    Note that this will see values after the type conversion has happened.
    """

    def callback(
        ctx: click.Context, param: click.Parameter, value: t.Sequence[t.Any] | None
    ) -> t.Any:
        if value is None or len(value) == 0:
            return None
        if len(value) == 1 and value[0] == null:
            return []
        return value

    return callback


class StringOrNull(click.ParamType):
    """
    Very similar to a basic string type, but one in which the empty string will
    be converted into an EXPLICIT_NULL
    """

    def get_type_annotation(self, param: click.Parameter) -> type:
        return t.cast(type, str | ExplicitNullType)

    def get_metavar(self, param: click.Parameter) -> str:
        return "TEXT"

    def convert(
        self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> t.Any:
        if value == "":
            return EXPLICIT_NULL
        else:
            return value


class UrlOrNull(StringOrNull):
    """
    Very similar to StringOrNull, but validates that the string is parsable as an
    http or https URL.
    """

    def get_metavar(self, param: click.Parameter) -> str:
        return "TEXT"

    def convert(
        self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> t.Any:
        if value == "":
            return EXPLICIT_NULL
        else:
            try:
                url = urlparse(value)
                assert url[0] in ["http", "https"]
            except Exception:
                raise click.UsageError(
                    f"'{value}' is not a well-formed http or https URL"
                )
            return value
