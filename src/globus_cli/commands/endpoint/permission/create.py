from __future__ import annotations

import sys
import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import ENDPOINT_PLUS_REQPATH, command, security_principal_opts
from globus_cli.termio import Field, TextMode, display

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


@command(
    "create",
    short_help="Create an access control rule",
    adoc_examples="""Give anyone read access to a directory.

[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ globus endpoint permission create $ep_id:/dir --permissions r --anonymous
----

Give read and write access to a specific user.

[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ globus endpoint permission create $ep_id:/ --permissions rw --identity go@globusid.org
----
""",
)
@security_principal_opts(
    allow_anonymous=True, allow_all_authenticated=True, allow_provision=True
)
@click.option(
    "--permissions",
    required=True,
    type=click.Choice(("r", "rw"), case_sensitive=False),
    help="Permissions to add. Read-Only or Read/Write",
)
@click.option(
    "--notify-email",
    metavar="EMAIL_ADDRESS",
    help="An email address to notify that the permission has been added",
)
@click.option(
    "--notify-message",
    metavar="MESSAGE",
    help="A custom message to add to email notifications",
)
@click.argument("endpoint_plus_path", type=ENDPOINT_PLUS_REQPATH)
@LoginManager.requires_login("auth", "transfer")
def create_command(
    login_manager: LoginManager,
    *,
    principal: tuple[str, str],
    permissions: Literal["r", "rw"],
    endpoint_plus_path: tuple[uuid.UUID, str | None],
    notify_email: str | None,
    notify_message: str | None,
) -> None:
    """
    Create a new access control rule on the target endpoint, granting users new
    permissions on the given path.

    The target endpoint must be a shared endpoint, as only these use access control
    lists to manage permissions.

    The '--permissions' option is required, and exactly one of '--all-authenticated'
    '--anonymous', '--group', or '--identity' is required to know to whom permissions
    are being granted.
    """
    from globus_cli.services.transfer import assemble_generic_doc

    endpoint_id, path = endpoint_plus_path
    principal_type, principal_val = principal

    transfer_client = login_manager.get_transfer_client()
    auth_client = login_manager.get_auth_client()

    if principal_type == "identity":
        lookup = auth_client.maybe_lookup_identity_id(principal_val)
        if not lookup:
            raise click.UsageError(
                "Identity does not exist. "
                "Use --provision-identity to auto-provision an identity."
            )
        else:
            principal_val = lookup
    elif principal_type == "provision-identity":
        principal_val = auth_client.maybe_lookup_identity_id(
            principal_val, provision=True
        )
        principal_type = "identity"

    if not notify_email:
        notify_message = None

    rule_data = assemble_generic_doc(
        "access",
        permissions=permissions,
        principal=principal_val,
        principal_type=principal_type,
        path=path,
        notify_email=notify_email,
        notify_message=notify_message,
    )

    res = transfer_client.add_endpoint_acl_rule(endpoint_id, rule_data)
    display(
        res,
        text_mode=TextMode.text_record,
        fields=[Field("Message", "message"), Field("Rule ID", "access_id")],
    )
