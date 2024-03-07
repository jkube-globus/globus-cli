from __future__ import annotations

import typing as t
import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import display


@command("is-activated", deprecated=True, hidden=True)
@endpoint_id_arg
@click.option(
    "--until",
    type=int,
    help=(
        "An integer number of seconds in the future. If the "
        "endpoint is activated, but will expire by then, exits "
        "with status 1"
    ),
)
@click.option(
    "--absolute-time",
    is_flag=True,
    show_default=True,
    default=False,
    help=(
        "Treat the value of --until as a POSIX timestamp (seconds "
        "since Epoch), not a number of seconds into the future."
    ),
)
@LoginManager.requires_login("transfer")
def endpoint_is_activated(
    login_manager: LoginManager,
    *,
    endpoint_id: uuid.UUID,
    until: int | None,
    absolute_time: bool,
) -> None:
    """
    Check if an endpoint is activated or requires activation.

    If it requires activation, exits with status 1, otherwise exits with status 0.

    If the endpoint is not activated, this command will output a link for web
    activation, or you can use 'globus endpoint activate' to activate the endpoint.
    """
    from globus_cli.services.transfer import activation_requirements_help_text

    transfer_client = login_manager.get_transfer_client()
    res = transfer_client.endpoint_get_activation_requirements(endpoint_id)

    def fail(deadline: int | None = None) -> t.NoReturn:
        exp_string = ""
        if deadline is not None:
            exp_string = f" or will expire within {deadline} seconds"
        requirements_help = activation_requirements_help_text(res, endpoint_id)

        display(
            res,
            text_mode=display.static_output(
                f"'{endpoint_id}' is not activated{exp_string}.\n\n{requirements_help}"
            ),
        )
        click.get_current_context().exit(1)

    def success(msg: str) -> t.NoReturn:
        display(res, text_mode=display.static_output(msg))
        click.get_current_context().exit(0)

    # eternally active endpoints have a special expires_in value
    if res["expires_in"] == -1:
        success(f"'{endpoint_id}' does not require activation")

    # autoactivation is not supported and --until was not passed
    if until is None:
        # and we are active right now (0s in the future)...
        if res.active_until(0):
            success(f"'{endpoint_id}' is activated")
        # or we are not active
        fail()

    # autoactivation is not supported and --until was passed
    if res.active_until(until, relative_time=not absolute_time):
        success(f"'{endpoint_id}' will be active for at least {until} seconds")
    else:
        fail(deadline=until)
