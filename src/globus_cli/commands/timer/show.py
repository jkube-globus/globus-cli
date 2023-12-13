import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import TextMode, display

from ._common import TIMER_FORMAT_FIELDS


@command("show", short_help="Display a timer")
@click.argument("TIMER_ID", type=click.UUID)
@LoginManager.requires_login("timer")
def show_command(login_manager: LoginManager, *, timer_id: uuid.UUID) -> None:
    """
    Display information about a particular timer.
    """
    timer_client = login_manager.get_timer_client()
    response = timer_client.get_job(timer_id)
    display(response, text_mode=TextMode.text_record, fields=TIMER_FORMAT_FIELDS)
