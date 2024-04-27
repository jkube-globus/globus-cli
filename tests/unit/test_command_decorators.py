import errno
from unittest import mock

import click

from globus_cli.parsing import command, main_group


def test_main_group_is_always_named_globus():
    @main_group()
    def foo():
        pass

    assert foo.name == "globus"


def test_main_group_reraises_epipe_errors_without_invoking_custom_handler(runner):
    @main_group()
    def foo():
        click.echo("hi")
        # simulate a broken pipe, as would happen if a command is piped to a command
        # which only reads some of the output before closing the stream, like `head`
        raise OSError("broken pipe", errno=errno.EPIPE)

    # we want to assert not only that the command exits successfully, but specifically
    # that it does not invoke the CLI's custom exception handler
    #
    # if it does, that means we won't get click's cleanup for EPIPE, which includes
    # special wrapping of `sys.stdout` and `sys.stderr`
    with mock.patch("globus_cli.parsing.commands.custom_except_hook") as mock_handler:
        result = runner.invoke(foo, [])
    assert result.exit_code == 0
    assert mock_handler.call_count == 0


def test_custom_command_missing_param_helptext(runner):
    @command()
    @click.option("--bar", help="BAR-STRING-HERE", required=True)
    def foo(bar):
        click.echo(bar or "none")

    # call with `--help` to confirm help behavior
    result = runner.invoke(foo, ["--help"])
    assert result.exit_code == 0
    assert "BAR-STRING-HERE" in result.output

    # no args should produce the same, but with an exit status of 2
    result = runner.invoke(foo, [])
    assert result.exit_code == 2
    assert "BAR-STRING-HERE" in result.output
    # should include missing arg message
    assert "Missing option '--bar'" in result.output


def test_custom_command_missing_param_helptext_suppressed_when_args_present(runner):
    @command()
    @click.option("--bar", help="BAR-STRING-HERE", required=True)
    @click.option("--baz", help="BAZ-STRING-HERE", required=True)
    def foo(bar, baz):
        click.echo(bar or "none")
        click.echo(baz or "none")

    # call with `--help` to confirm help behavior
    result = runner.invoke(foo, ["--help"])
    assert result.exit_code == 0
    assert "BAR-STRING-HERE" in result.output
    assert "BAZ-STRING-HERE" in result.output

    # no args should produce the same, but with an exit status of 2
    # and a missing arg message
    result = runner.invoke(foo, [])
    assert result.exit_code == 2
    assert "Missing option" in result.output
    assert "BAR-STRING-HERE" in result.output
    assert "BAZ-STRING-HERE" in result.output

    # partial args should produce the missing arg message
    # but not helptext
    result = runner.invoke(foo, ["--bar", "X"])
    assert result.exit_code == 2
    assert "Missing option '--baz'" in result.output
    assert "BAR-STRING-HERE" not in result.output
    assert "BAZ-STRING-HERE" not in result.output
