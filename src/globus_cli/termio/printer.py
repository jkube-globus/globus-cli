from __future__ import annotations

import enum
import json
import shutil
import textwrap
import typing as t

import click
import globus_sdk

from .awscli_text import unix_display
from .context import (
    get_jmespath_expression,
    outformat_is_json,
    outformat_is_text,
    outformat_is_unix,
)
from .field import Field
from .server_timing import maybe_show_server_timing

if t.TYPE_CHECKING:
    from globus_cli.types import JsonValue

T = t.TypeVar("T")


class TextMode(enum.Enum):
    silent = enum.auto()
    json = enum.auto()
    text_table = enum.auto()
    text_record = enum.auto()
    text_record_list = enum.auto()
    text_raw = enum.auto()
    text_custom = enum.auto()


def _none_to_null(val: T | None) -> T | str:
    if val is None:
        return "NULL"
    return val


def _assert_fields(fields: list[Field] | None) -> list[Field]:
    if fields is None:
        raise ValueError(
            "Internal Error! Output format requires fields; none given. "
            "You can workaround this error by using `--format JSON`"
        )
    return fields


def _get_terminal_content_width() -> int:
    """Get a content width for text output based on the terminal size.

    Uses 80% of the terminal width, if it can be detected and isn't too small.
    """
    cols = shutil.get_terminal_size(fallback=(80, 20)).columns
    return cols if cols < 100 else int(0.8 * cols)


def _jmespath_preprocess(res: JsonValue | globus_sdk.GlobusHTTPResponse) -> t.Any:
    jmespath_expr = get_jmespath_expression()

    if isinstance(res, globus_sdk.GlobusHTTPResponse):
        res = res.data

    if not isinstance(res, str):
        if jmespath_expr is not None:
            res = jmespath_expr.search(res)

    return res


def print_json_response(
    res: JsonValue | globus_sdk.GlobusHTTPResponse, *, sort_keys: bool = True
) -> None:
    res = _jmespath_preprocess(res)
    res = json.dumps(res, indent=2, separators=(",", ": "), sort_keys=sort_keys)
    click.echo(res)


def print_unix_response(res: JsonValue | globus_sdk.GlobusHTTPResponse) -> None:
    res = _jmespath_preprocess(res)
    try:
        unix_display(res)
    # Attr errors indicate that we got data which cannot be unix formatted
    # likely a scalar + non-scalar in an array, though there may be other cases
    # print good error and exit(2) (Count this as UsageError!)
    except AttributeError:
        click.echo(
            "UNIX formatting of output failed."
            "\n  "
            "This usually means that data has a structure which cannot be "
            "handled by the UNIX formatter."
            "\n  "
            "To avoid this error in the future, ensure that you query the "
            'exact properties you want from output data with "--jmespath"',
            err=True,
        )
        click.get_current_context().exit(2)


def _colon_display(
    data: JsonValue | globus_sdk.GlobusHTTPResponse, fields: list[Field]
) -> None:
    maxlen = max(len(f.name) for f in fields) + 2
    indent = " " * maxlen

    content_width = _get_terminal_content_width()
    wrapper = textwrap.TextWrapper(
        initial_indent=indent, subsequent_indent=indent, width=content_width
    )

    for field in fields:
        # str in case the result is `None`
        value = str(field(data))

        # only wrap if it's enabled and detected
        if field.wrap_enabled and (
            len(value) + maxlen > content_width or "\n" in value
        ):
            # TextWrapper will discard existing whitespace, including newlines
            # so split, wrap each resulting line, then rejoin
            lines = value.split("\n")
            lines = [wrapper.fill(x) for x in lines]
            if len(lines) > 5:  # truncate here, max 5 lines
                lines = lines[:5] + [indent + "..."]
            # lstrip to remove indent on the first line, since it will be indented by
            # the format string below
            value = "\n".join(lines).lstrip()

        click.echo("{}{}".format((field.name + ":").ljust(maxlen), value))


def print_table(
    iterable: t.Iterable[t.Any], fields: list[Field], print_headers: bool = True
) -> None:
    # the iterable may not be safe to walk multiple times, so we must walk it
    # only once -- however, to let us write things naturally, convert it to a
    # list and we can assume it is safe to walk repeatedly
    iterable = list(iterable)

    # extract headers and keys as separate lists
    headers = [f.name for f in fields]

    # use the iterable to find the max width of an element for each column
    # use a special function to handle empty iterable
    def get_max_colwidth(f: Field) -> int:
        def _safelen(x: t.Any) -> int:
            try:
                return len(x)
            except TypeError:
                return len(str(x))

        lengths = [_safelen(f(i)) for i in iterable]
        if not lengths:
            return 0
        else:
            return max(lengths)

    widths = [get_max_colwidth(f) for f in fields]
    # handle the case in which the column header is the widest thing
    widths = [max(w, len(h)) for w, h in zip(widths, headers)]

    def format_line(inputs: list[str]) -> str:
        out = ""
        last_offset = 3
        for w, h, x in zip(widths, headers, inputs):
            out += str(x).ljust(w)
            if h:
                out += " | "
                last_offset = 3
            else:
                last_offset = 0
        return out[:-last_offset]

    # print headers
    if print_headers:
        click.echo(format_line(headers))
        click.echo(
            format_line(["-" * w if h else " " * w for w, h in zip(widths, headers)])
        )

    # print the rows of data
    for i in iterable:
        click.echo(format_line([_none_to_null(f(i)) for f in fields]))


class Renderer:
    TABLE = TextMode.text_table
    SILENT = TextMode.silent
    JSON = TextMode.json
    RECORD = TextMode.text_record
    RECORD_LIST = TextMode.text_record_list
    RAW = TextMode.text_raw

    def __call__(
        self,
        response_data: t.Any,
        *,
        simple_text: str | None = None,
        text_preamble: str | None = None,
        text_epilog: str | None = None,
        text_mode: TextMode | t.Callable[[t.Any], None] = TextMode.text_table,
        json_converter: t.Callable[..., t.Any] | None = None,
        fields: list[Field] | None = None,
        response_key: str | t.Callable[[t.Any], t.Any] | None = None,
        sort_json_keys: bool = True,
    ) -> None:
        _display(
            response_data,
            simple_text=simple_text,
            text_preamble=text_preamble,
            text_epilog=text_epilog,
            text_mode=text_mode,
            json_converter=json_converter,
            fields=fields,
            response_key=response_key,
            sort_json_keys=sort_json_keys,
        )

    def render_table(
        self,
        iterable: t.Iterable[t.Any],
        fields: list[Field],
        print_headers: bool = True,
    ) -> None:
        print_table(iterable, fields, print_headers)


display = Renderer()


def _display(
    response_data: t.Any,
    *,
    simple_text: str | None = None,
    text_preamble: str | None = None,
    text_epilog: str | None = None,
    text_mode: TextMode | t.Callable[[t.Any], None] = TextMode.text_table,
    json_converter: t.Callable[[t.Any], t.Any] | None = None,
    fields: list[Field] | None = None,
    response_key: str | t.Callable[[t.Any], t.Any] | None = None,
    sort_json_keys: bool = True,
) -> None:
    """
    A generic output printer. Consumes the following pieces of data:

    ``response_data`` is a dict, list (if the ``text_mode`` is
    ``TextMode.text_record_list``), or GlobusHTTPResponse object.
    It contains either an API response or synthesized data for printing.

    ``simple_text`` is a text override -- normal printing is skipped and this
    string is printed instead (text output only)
    ``text_preamble`` is text which prints before normal printing (text output
    only)
    ``text_epilog`` is text which prints after normal printing (text output
    only)
    ``text_mode`` is a TextMode OR a callable which takes ``response_data`` and prints
    output. Note that when a callable is given, it does the actual printing

    ``json_converter`` is a callable that does preprocessing of JSON output. It
    must take ``response_data`` and produce another dict or dict-like object
    (json/unix output only)

    ``fields`` is an iterable of fields. They may be expressed as Field
    objects, (fieldname, key_string) tuples, or (fieldname, key_func) tuples.

    ``response_key`` is a key into the data to print. When used with table
    printing, it must get an iterable out, and when used with raw printing, it
    gets a string. Necessary for certain formats like text table (text output
    only)

    ``sort_json_keys`` is a flag that will cause JSON keys to be sorted or unsorted.
    It is only used when the output format is JSON.
    """

    if isinstance(response_data, globus_sdk.GlobusHTTPResponse):
        maybe_show_server_timing(response_data)

    def _print_as_text() -> None:
        # if we're given simple text, print that and exit
        if simple_text is not None:
            click.echo(simple_text)
            return

        # if there's a preamble, print it before any other text
        if text_preamble is not None:
            click.echo(text_preamble)

        # If there's a response key, either key into the response data or apply it as a
        # callable to extract from the response data
        if response_key is None:
            data = response_data
        elif callable(response_key):
            data = response_key(response_data)
        else:
            data = response_data[response_key]

        #  do the various kinds of printing
        if text_mode == TextMode.text_table:
            print_table(data, _assert_fields(fields))
        elif text_mode == TextMode.text_record:
            _colon_display(data, _assert_fields(fields))
        elif text_mode == TextMode.text_record_list:
            fields_ = _assert_fields(fields)
            if not isinstance(data, list):
                raise ValueError("only lists can be output in text record list format")
            first = True
            for record in data:
                # add empty line between records after the first
                if not first:
                    click.echo()
                first = False
                _colon_display(record, fields_)
        elif text_mode == TextMode.text_raw:
            click.echo(data)
        elif text_mode == TextMode.text_custom:
            # _custom_text_formatter is set along with FORMAT_TEXT_CUSTOM
            assert _custom_text_formatter
            _custom_text_formatter(data)

        # if there's an epilog, print it after any text
        if text_epilog is not None:
            click.echo(text_epilog)

    if isinstance(text_mode, TextMode):
        _custom_text_formatter = None
    else:
        _custom_text_formatter = text_mode
        text_mode = TextMode.text_custom

    if outformat_is_json() or (outformat_is_text() and text_mode == TextMode.json):
        print_json_response(
            json_converter(response_data) if json_converter else response_data,
            sort_keys=sort_json_keys,
        )
    elif outformat_is_unix():
        print_unix_response(
            json_converter(response_data) if json_converter else response_data
        )
    else:
        # silent does nothing
        if text_mode == TextMode.silent:
            return
        _print_as_text()
