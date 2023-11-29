"""
tests dedicated to the `globus gcs` aliasing of other commands,
which specifically exercise the behavior of *aliasing*

these tests do not exercise the aliased commands at all
"""
import pytest


@pytest.mark.parametrize(
    "subcommand",
    (
        ["collection", "delete"],
        ["collection", "list"],
        (
            ["endpoint", "storage-gateway", "list"],
            ["gcs", "storage-gateway", "list"],
        ),
        (
            ["endpoint", "user-credential", "list"],
            ["gcs", "user-credential", "list"],
        ),
    ),
)
def test_aliased_commands_have_unique_usage_lines(run_line, subcommand):
    if isinstance(subcommand, tuple):
        from_command = subcommand[0]
        to_command = subcommand[1]
    else:
        from_command = subcommand
        to_command = ["gcs"] + subcommand

    unaliased_help = run_line(["globus", *from_command, "--help"]).stdout
    aliased_help = run_line(["globus", *to_command, "--help"]).stdout

    unaliased_usage_line = unaliased_help.splitlines()[0]
    aliased_usage_line = aliased_help.splitlines()[0]

    # verify:
    # - they aren't the same
    assert unaliased_usage_line != aliased_usage_line
    # - they each start correctly
    assert " ".join(["globus", *from_command]) in unaliased_usage_line
    assert " ".join(["globus", *to_command]) in aliased_usage_line
