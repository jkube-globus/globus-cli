import typing as t

import globus_sdk

from globus_cli.termio import Field, formatters
from globus_cli.termio.formatters.auth import PrincipalURNFormatter


class CollectionRoleFormatter(PrincipalURNFormatter):
    """
    A formatter for collection roles
    """

    def __init__(
        self, auth_client: globus_sdk.AuthClient, collection_role: dict[str, t.Any]
    ) -> None:
        super().__init__(auth_client)
        self.add_items(collection_role.get("id"))
        self.add_items(*collection_role.get("role", ()))
        self.add_items(*collection_role.get("principal", ()))


def collection_role_format_fields(
    auth_client: globus_sdk.AuthClient,
    collection_roles: dict[str, t.Any],
) -> list[Field]:
    """
    The standard list of fields to render for a collection role.

    :param auth_client: An AuthClient, used to resolve principal URNs.
    :param collection_role: The collection role to format
    """
    principal = CollectionRoleFormatter(auth_client, collection_roles)
    csv_roles_list = formatters.ArrayFormatter(
        element_formatter=principal,
        delimiter=", ",
    )

    return [
        Field("ID", "id", formatter=csv_roles_list),
        Field("Role", "role", formatter=csv_roles_list),
        Field("Principal", "principal", formatter=principal),
    ]
