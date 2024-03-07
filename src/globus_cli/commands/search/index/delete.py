import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import display


@command("delete")
@LoginManager.requires_login("search")
@click.argument("INDEX_ID")
def delete_command(login_manager: LoginManager, *, index_id: str) -> None:
    """Delete a Search Index"""
    search_client = login_manager.get_search_client()
    display(
        search_client.delete_index(index_id),
        text_mode=display.static_output(
            f"Index {index_id} is now marked for deletion.\n"
            "It will be fully deleted after cleanup steps complete."
        ),
    )
