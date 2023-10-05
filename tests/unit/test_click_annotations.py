from __future__ import annotations

import click
import pytest

import globus_cli.parsing
from globus_cli.reflect import iter_all_commands
from globus_cli.types import JsonValue

click_type_test = pytest.importorskip(
    "click_type_test", reason="tests require 'click-type-test'"
)

_SKIP_MODULES = (
    "globus_cli.commands.endpoint.deactivate",
    "globus_cli.commands.endpoint.delete",
    "globus_cli.commands.endpoint.local_id",
    "globus_cli.commands.endpoint.my_shared_endpoint_list",
    "globus_cli.commands.endpoint.permission.create",
    "globus_cli.commands.endpoint.permission.show",
    "globus_cli.commands.endpoint.permission.update",
    "globus_cli.commands.endpoint.role.create",
    "globus_cli.commands.endpoint.search",
    "globus_cli.commands.endpoint.show",
    "globus_cli.commands.endpoint.storage_gateway.list",
    "globus_cli.commands.get_identities",
    "globus_cli.commands.login",
    "globus_cli.commands.logout",
)

_ALL_NON_GROUP_COMMANDS: tuple[click.Command, ...] = (
    ctx.command
    for ctx in iter_all_commands(skip_hidden=False)
    if not isinstance(ctx.command, click.Group)
)
_ALL_COMMANDS_TO_TEST: tuple[tuple[str, str], ...] = (
    command
    for command in _ALL_NON_GROUP_COMMANDS
    if command.callback.__module__ not in _SKIP_MODULES
)


def _command_id_fn(val):
    assert isinstance(val, click.Command)
    return val.callback.__module__


_ALL_PARSING_ATTRS = {
    attrname: getattr(globus_cli.parsing, attrname)
    for attrname in globus_cli.parsing.__all__
}
_ALL_CUSTOM_PARAM_TYPES = (
    getattr(globus_cli.parsing, attrname)
    for attrname, attrval in _ALL_PARSING_ATTRS.items()
    if isinstance(attrval, type) and issubclass(attrval, click.ParamType)
)


@pytest.mark.parametrize(
    "param_type", _ALL_CUSTOM_PARAM_TYPES, ids=lambda x: x.__name__
)
def test_custom_param_types_are_annotated(param_type):
    assert isinstance(param_type, click_type_test.AnnotatedParamType)


@pytest.mark.parametrize("command", _ALL_COMMANDS_TO_TEST, ids=_command_id_fn)
def test_annotations_match_click_params(command):
    click_type_test.check_param_annotations(
        command, known_type_names={JsonValue: "globus_cli.types.JsonValue"}
    )
