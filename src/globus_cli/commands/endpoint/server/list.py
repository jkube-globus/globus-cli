from __future__ import annotations

import typing as t
import uuid

import globus_sdk

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import Field, display, formatters


class ServerURIFormatter(formatters.StrFormatter):
    parse_null_values = True

    def parse(self, value: t.Any) -> str:
        if value is None:
            return "none (Globus Connect Personal)"
        return str(value)


@command(
    "list",
    deprecated=True,
    short_help="List all servers for an endpoint",
    adoc_examples="""[source,bash]
----
$ ep_id=aa752cea-8222-5bc8-acd9-555b090c0ccb
$ globus endpoint server list $ep_id
----
""",
)
@endpoint_id_arg
@LoginManager.requires_login("transfer")
def server_list(login_manager: LoginManager, *, endpoint_id: uuid.UUID) -> None:
    """List all servers belonging to an endpoint."""
    transfer_client = login_manager.get_transfer_client()
    # raises usage error on shares for us
    endpoint_w_server_list = transfer_client.get_endpoint_w_server_list(endpoint_id)
    endpoint = endpoint_w_server_list[0]
    server_list: str | dict[str, t.Any] | globus_sdk.GlobusHTTPResponse = (
        endpoint_w_server_list[1]
    )

    if server_list == "S3":  # not GCS -- this is an S3 endpoint
        server_list = {"s3_url": endpoint["s3_url"]}
        fields = [Field("S3 URL", "s3_url")]
        text_mode = display.RECORD
    else:  # regular GCS host endpoint
        fields = [
            Field("ID", "id"),
            Field("URI", "uri", formatter=ServerURIFormatter()),
        ]
        text_mode = display.TABLE
    display(server_list, text_mode=text_mode, fields=fields)
