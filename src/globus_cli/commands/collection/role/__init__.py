from globus_cli.parsing import group


@group(
    "role",
    lazy_subcommands={},
)
def role_command() -> None:
    """Manage Roles on Collections."""
