from __future__ import annotations

import typing as t
import uuid

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import display

from ._common import server_add_opts


@command(
    "add",
    deprecated=True,
    short_help="Add a server to an endpoint.",
    adoc_examples="""Add a server with a url of gridftp.example.org to an endpoint

[source,bash]
----
$ ep_id=aa752cea-8222-5bc8-acd9-555b090c0ccb
$ globus endpoint server add $ep_id --hostname gridftp.example.org
----
""",
)
@endpoint_id_arg
@server_add_opts
@LoginManager.requires_login("transfer")
def server_add(
    login_manager: LoginManager,
    *,
    endpoint_id: uuid.UUID,
    subject: str | None,
    port: int,
    scheme: t.Literal["gsiftp", "ftp"],
    hostname: str,
    incoming_data_ports: tuple[int | None, int | None] | None,
    outgoing_data_ports: tuple[int | None, int | None] | None,
) -> None:
    """
    Add a server to an endpoint.

    An endpoint must be a Globus Connect Server endpoint to have servers.
    """
    from globus_cli.services.transfer import assemble_generic_doc

    transfer_client = login_manager.get_transfer_client()

    server_doc = assemble_generic_doc(
        "server", subject=subject, port=port, scheme=scheme, hostname=hostname
    )

    # n.b. must be done after assemble_generic_doc(), as that function filters
    # out `None`s, which we need to be able to set for `'unspecified'`
    if incoming_data_ports:
        server_doc.update(
            incoming_data_port_start=incoming_data_ports[0],
            incoming_data_port_end=incoming_data_ports[1],
        )
    if outgoing_data_ports:
        server_doc.update(
            outgoing_data_port_start=outgoing_data_ports[0],
            outgoing_data_port_end=outgoing_data_ports[1],
        )

    res = transfer_client.add_endpoint_server(endpoint_id, server_doc)
    display(res, text_mode=display.RAW, response_key="message")
