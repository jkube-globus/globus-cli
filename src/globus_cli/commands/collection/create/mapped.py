from __future__ import annotations

import typing as t
import uuid

import click
import globus_sdk

from globus_cli.constants import EXPLICIT_NULL, ExplicitNullType
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import (
    CommaDelimitedList,
    JSONStringOrFile,
    StringOrNull,
    UrlOrNull,
    command,
    endpoint_id_arg,
    mutex_option_group,
    nullable_multi_callback,
)
from globus_cli.termio import Field, TextMode, display


def _mkhelp(txt):
    return f"{txt} the collection"


def collection_create_params(f):
    """
    Collection of options consumed by GCS Collection update

    Usage:

    >>> @collection_create_and_update_params(create=False)
    >>> def command_func(**kwargs):
    >>>     ...
    """
    multi_use_option_str = "Give this option multiple times in a single command"

    f = click.argument("DISPLAY_NAME")(f)
    f = click.option(
        "--public/--private",
        "public",
        default=True,
        help="Set the collection to be public or private",
    )(f)
    f = click.option(
        "--description", type=StringOrNull(), help=_mkhelp("Description for")
    )(f)
    f = click.option(
        "--info-link", type=StringOrNull(), help=_mkhelp("Link for info about")
    )(f)
    f = click.option(
        "--contact-info", type=StringOrNull(), help=_mkhelp("Contact Info for")
    )(f)
    f = click.option(
        "--contact-email",
        type=StringOrNull(),
        help=_mkhelp("Contact email for"),
    )(f)
    f = click.option(
        "--organization", type=StringOrNull(), help=_mkhelp("Organization for")
    )(f)
    f = click.option(
        "--department", type=StringOrNull(), help=_mkhelp("Department which operates")
    )(f)
    f = click.option(
        "--keywords",
        type=CommaDelimitedList(),
        help=_mkhelp("Comma separated list of keywords to help searches for"),
    )(f)
    f = click.option(
        "--force-encryption/--no-force-encryption",
        "force_encryption",
        default=None,
        help=(
            "When set, all transfers to and from this collection are "
            "always encrypted"
        ),
    )(f)
    f = click.option(
        "--sharing-restrict-paths",
        type=JSONStringOrFile(null="null"),
        help="Path restrictions for sharing data on guest collections "
        "based on this collection. This option is only usable on Mapped "
        "Collections",
    )(f)
    f = click.option(
        "--allow-guest-collections/--no-allow-guest-collections",
        default=None,
        help=(
            "Allow Guest Collections to be created on this Collection. This option "
            "is only usable on Mapped Collections. If this option is disabled on a "
            "Mapped Collection which already has associated Guest Collections, "
            "those collections will no longer be accessible"
        ),
    )(f)
    f = click.option(
        "--disable-anonymous-writes/--enable-anonymous-writes",
        default=None,
        help=(
            "Allow anonymous write ACLs on Guest Collections attached to this "
            "Mapped Collection. This option is only usable on non high assurance "
            "Mapped Collections and the setting is inherited by the hosted Guest "
            "Collections. Anonymous write ACLs are enabled by default "
            "(requires an endpoint with API v1.8.0)"
        ),
    )(f)
    f = click.option(
        "--domain-name",
        help=(
            "DNS host name for the collection (mapped "
            "collections only). This may be either a host name "
            "or a fully-qualified domain name, but if it is the latter "
            "it must be a subdomain of the endpoint's domain"
        ),
    )(f)
    f = click.option(
        "--default-directory",
        default=None,
        help="Default directory when browsing the collection",
    )(f)

    f = click.option(
        "--enable-https",
        is_flag=True,
        help=(
            "Explicitly enable HTTPS supprt (requires a managed endpoint "
            "with API v1.1.0)"
        ),
    )(f)
    f = click.option(
        "--disable-https",
        is_flag=True,
        help=(
            "Explicitly disable HTTPS supprt (requires a managed endpoint "
            "with API v1.1.0)"
        ),
    )(f)
    f = mutex_option_group("--enable-https", "--disable-https")(f)

    f = click.option(
        "--user-message",
        help=(
            "A message for clients to display to users when interacting "
            "with this collection"
        ),
        type=StringOrNull(),
    )(f)
    f = click.option(
        "--user-message-link",
        help=(
            "Link to additional messaging for clients to display to users "
            "when interacting with this endpoint, linked to an http or https URL "
            "with this collection"
        ),
        type=UrlOrNull(),
    )(f)
    f = click.option(
        "--sharing-user-allow",
        "sharing_users_allow",
        multiple=True,
        callback=nullable_multi_callback(""),
        help=(
            "Connector-specific username allowed to create guest collections."
            f"{multi_use_option_str} to allow multiple users. "
            'Set a value of "" to clear this'
        ),
    )(f)
    f = click.option(
        "--sharing-user-deny",
        "sharing_users_deny",
        multiple=True,
        callback=nullable_multi_callback(""),
        help=(
            "Connector-specific username denied permission to create guest "
            f"collections. {multi_use_option_str} to deny multiple users. "
            'Set a value of "" to clear this'
        ),
    )(f)
    f = click.option(
        "--posix-sharing-group-allow",
        multiple=True,
        callback=nullable_multi_callback(""),
        help=(
            "POSIX group allowed access to create guest collections "
            "(POSIX Connector Only). "
            f"{multi_use_option_str} to allow multiple groups. "
            'Set a value of "" to clear this'
        ),
    )(f)
    f = click.option(
        "--posix-sharing-group-deny",
        multiple=True,
        callback=nullable_multi_callback(""),
        help=(
            "POSIX group denied permission to create guest collections "
            "(POSIX Connector Only). "
            f"{multi_use_option_str} to deny multiple groups. "
            + 'Set a value of "" to clear this'
        ),
    )(f)
    f = click.option(
        "--google-project-id",
        help=(
            "For Google Cloud Storage backed Collections only. The Google "
            "Cloud Platform project ID which is used by this Collection"
        ),
        type=StringOrNull(),
    )(f)

    # POSIX Staging connector (GCS v5.4.10)
    f = click.option(
        "--posix-staging-sharing-group-allow",
        multiple=True,
        callback=nullable_multi_callback(""),
        help=(
            "POSIX group allowed access to create guest collections "
            "(POSIX Staging Connector Only). "
            f"{multi_use_option_str} to allow multiple groups. "
            'Set a value of "" to clear this'
        ),
    )(f)
    f = click.option(
        "--posix-staging-sharing-group-deny",
        multiple=True,
        callback=nullable_multi_callback(""),
        help=(
            "POSIX group denied permission to create guest collections "
            "(POSIX Staging Connector Only). "
            f"{multi_use_option_str} to deny multiple groups. "
            'Set a value of "" to clear this'
        ),
    )(f)

    f = click.option(
        "--verify",
        type=click.Choice(["force", "disable", "default"], case_sensitive=False),
        help=(
            "Set the policy for this collection for file integrity verification "
            "after transfer. 'force' requires all transfers to perform "
            "verfication. 'disable' disables all verification checks. 'default' "
            "allows the user to decide on verification at Transfer task submit  "
            "time. When set on mapped collections, this policy is inherited by any "
            "guest collections"
        ),
    )(f)
    return f


@command("create", short_help="Create a new Mapped Collection")
@endpoint_id_arg
@click.argument("STORAGE_GATEWAY_ID")
@click.argument("BASE_PATH")
@collection_create_params
@click.option(
    "--identity-id",
    help=(
        "Globus Auth identity to who acts as the owner of this Collection. This "
        "identity must be an administrator on the Endpoint"
    ),
)
@LoginManager.requires_login(LoginManager.TRANSFER_RS, LoginManager.AUTH_RS)
def collection_create_mapped(
    *,
    login_manager: LoginManager,
    # positional args
    endpoint_id: uuid.UUID,
    storage_gateway_id: uuid.UUID,
    base_path: str,
    display_name: str,
    # options
    public: bool,
    description: str | None,
    info_link: str | None,
    contact_info: str | None,
    contact_email: str | None,
    organization: str | None,
    department: str | None,
    keywords: str | None,
    default_directory: str | None,
    force_encryption: bool | None,
    domain_name: str | None,
    disable_anonymous_writes: bool | None,
    identity_id: str | None,
    google_project_id: str | None,
    posix_sharing_group_allow: t.Iterable[str] | None,
    posix_sharing_group_deny: t.Iterable[str] | None,
    posix_staging_sharing_group_allow: t.Iterable[str] | None,
    posix_staging_sharing_group_deny: t.Iterable[str] | None,
    sharing_restrict_paths: t.Dict[str, t.Iterable[str]] | None | ExplicitNullType,
    allow_guest_collections: bool | None,
    sharing_users_allow: t.Iterable[str] | None,
    sharing_users_deny: t.Iterable[str] | None,
    user_message: str | None | ExplicitNullType,
    user_message_link: str | None | ExplicitNullType,
    enable_https: bool | None,
    disable_https: bool | None,
    verify: str | None,
) -> None:
    """
    Create a new Mapped Collection, rooted on some given path within an
    existing Storage Gateway.

    The ENDPOINT_ID and STORAGE_GATEWAY_ID are both required in order to specify where
    and how the collection is hosted.
    """
    gcs_client = login_manager.get_gcs_client(endpoint_id=endpoint_id)

    policies: t.Optional[globus_sdk.CollectionPolicies] = None
    if google_project_id is not None:
        policies = globus_sdk.GoogleCloudStorageCollectionPolicies(
            project=google_project_id
        )

    if posix_sharing_group_allow is not None or posix_sharing_group_deny is not None:
        if policies is not None:
            raise click.UsageError("Incompatible policy options detected")
        # Added in 5.4.8 for POSIX connector
        policies = globus_sdk.POSIXCollectionPolicies(
            posix_sharing_group_allow=posix_sharing_group_allow,
            posix_sharing_group_deny=posix_sharing_group_deny,
        )

    if (
        posix_staging_sharing_group_allow is not None
        or posix_staging_sharing_group_deny is not None
    ):
        if policies is not None:
            raise click.UsageError("Incompatible policy options detected")
        # Added in 5.4.10 for POSIX staging connector
        policies = globus_sdk.POSIXStagingStoragePolicies(
            sharing_groups_allow=posix_staging_sharing_group_allow,
            sharing_groups_deny=posix_staging_sharing_group_deny,
        )

    if sharing_restrict_paths == EXPLICIT_NULL:
        sharing_restrict_paths = None
    if user_message == EXPLICIT_NULL:
        user_message = None
    if user_message_link == EXPLICIT_NULL:
        user_message_link = None

    # These are added in GCS 5.4.4, so if neither --enable-https or
    # --disable-https are set, then we'll not try to set the value for
    # backward compatibility
    if enable_https is False:
        enable_https = None
    if disable_https:
        enable_https = False

    force_verify: bool | None = None
    disable_verify: bool | None = None
    if verify is not None:
        if verify.lower() == "force":
            force_verify, disable_verify = True, False
        elif verify.lower() == "disable":
            force_verify, disable_verify = False, True
        else:
            force_verify, disable_verify = False, False

    collection_doc = globus_sdk.MappedCollectionDocument(
        storage_gateway_id=storage_gateway_id,
        collection_base_path=base_path,
        display_name=display_name,
        public=public,
        description=description,
        info_link=info_link,
        contact_info=contact_info,
        contact_email=contact_email,
        organization=organization,
        department=department,
        keywords=keywords,
        default_directory=default_directory,
        force_encryption=force_encryption,
        domain_name=domain_name,
        disable_anonymous_writes=disable_anonymous_writes,
        identity_id=identity_id,
        policies=policies,
        allow_guest_collections=allow_guest_collections,
        sharing_users_allow=sharing_users_allow,
        sharing_users_deny=sharing_users_deny,
        sharing_restrict_paths=sharing_restrict_paths,
        user_message=user_message,
        user_message_link=user_message_link,
        enable_https=enable_https,
        disable_verify=disable_verify,
        force_verify=force_verify,
    )
    res = gcs_client.create_collection(collection_doc)

    display(res, text_mode=TextMode.text_record, fields=[Field("Collection ID", "id")])
