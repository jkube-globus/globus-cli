from __future__ import annotations

import uuid

import click
import globus_sdk

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import (
    Field,
    TextMode,
    display,
    formatters,
    outformat_is_text,
    print_command_hint,
)

from ._common import SESSION_ENFORCEMENT_FIELD

_COMMON_FIELDS = [
    Field("BAA", "subscription_info.is_baa", formatter=formatters.Bool),
    Field(
        "High Assurance",
        "subscription_info.is_high_assurance",
        formatter=formatters.Bool,
    ),
]


@click.argument("subscription_id", type=click.UUID)
@command("get-by-subscription")
@LoginManager.requires_login("groups")
def group_get_by_subscription(
    login_manager: LoginManager, *, subscription_id: uuid.UUID
) -> None:
    """Show the Group which provides a specific Subscription.

    If the Group is not visible to the current user, only the Group ID will be shown.
    """
    groups_client = login_manager.get_groups_client()

    subscription_data = groups_client.get_group_by_subscription_id(subscription_id)

    # for text output only, attempt to fetch the Group data
    if outformat_is_text():
        group_data: globus_sdk.GlobusHTTPResponse | None = try_resolve_group(
            groups_client, subscription_data["group_id"]
        )
    # for JSON or unix-formatted output, do not look up the Group
    else:
        group_data = None

    # if text output was wanted *and* we successfully got the group data
    # then we will display Group data
    if group_data:
        display(
            group_data,
            text_mode=TextMode.text_record,
            fields=(
                [Field("Group ID", "id")]
                + _COMMON_FIELDS
                + [
                    Field("Name", "name"),
                    Field("Description", "description", wrap_enabled=True),
                    Field("Type", "group_type"),
                    Field("Visibility", "policies.group_visibility"),
                    Field("Membership Visibility", "policies.group_members_visibility"),
                    SESSION_ENFORCEMENT_FIELD,
                    Field("Join Requests Allowed", "policies.join_requests"),
                    Field(
                        "Signup Fields",
                        "policies.signup_fields",
                        formatter=formatters.SortedArray,
                    ),
                    Field(
                        "Roles",
                        "my_memberships[].role",
                        formatter=formatters.SortedArray,
                    ),
                ]
            ),
        )
    # otherwise, display the subscription data and text-mode will be just the Group ID
    else:
        # if text mode was requested and we're in this branch, it means an attempt to
        # grab the group itself failed, so show a warning/hint
        if outformat_is_text():
            print_command_hint(
                "The Group for this Subscription is not visible to you.\n"
            )
        display(
            subscription_data,
            text_mode=TextMode.text_record,
            fields=[Field("Group ID", "group_id")] + _COMMON_FIELDS,
        )


def try_resolve_group(
    groups_client: globus_sdk.GroupsClient, group_id: str
) -> globus_sdk.GlobusHTTPResponse | None:
    """Attempt to get a group"""
    try:
        return groups_client.get_group(group_id, include="my_memberships")
    except globus_sdk.GlobusAPIError as e:
        if e.http_status == 403:
            return None
        raise
