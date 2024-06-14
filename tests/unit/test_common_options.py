import click
import pytest

from globus_cli.parsing.command_state import CommandState
from globus_cli.parsing.shared_options import common_options


def test_common_options_are_not_exposed(runner):
    """
    The common options decorator only produces options which are stored to the
    CommandState object via callbacks.

    Therefore, a command with no arguments should work.
    """

    @common_options()
    @click.command
    def foo():
        pass

    result = runner.invoke(foo, [])
    assert result.exit_code == 0


@pytest.mark.parametrize(
    "add_args, expect_verbosity",
    (
        pytest.param([], 0, id="default"),
        pytest.param(["-v"], 1, id="v"),
        pytest.param(["--verbose"], 1, id="verbose"),
        pytest.param(["-vv"], 2, id="vv"),
        pytest.param(["-vvv"], 3, id="vvv"),
        pytest.param(["--quiet"], -1, id="quiet"),
        pytest.param(["-v", "--quiet"], 0, id="v-quiet"),
        pytest.param(["-vv", "--quiet"], 1, id="vv-quiet"),
        pytest.param(["-vv", "--quiet", "--quiet"], 0, id="vv-quiet-quiet"),
        pytest.param(["--debug"], 3, id="debug"),
        pytest.param(["--debug", "--quiet"], 2, id="debug-quiet"),
    ),
)
def test_verbosity_control(runner, add_args, expect_verbosity):
    @common_options()
    @click.command
    def foo():
        ctx = click.get_current_context()
        state = ctx.ensure_object(CommandState)
        print(state.verbosity)

    result = runner.invoke(foo, add_args)
    assert result.exit_code == 0
    assert int(result.output) == expect_verbosity
