import pytest
from click.shell_completion import ShellComplete
from click.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def run_command(runner):
    def _run(cmd, args, exit_code=0):
        result = runner.invoke(cmd, args, catch_exceptions=bool(exit_code))
        assert result.exit_code == exit_code
        return result

    return _run


@pytest.fixture
def get_completions():
    """
    This fixture provides a function which accepts a command,
    arguments, and an incomplete string (the last, partial arg).

    It then uses test helpers defined in click's own testsuite to
    render this to a list of strings.
    """

    def complete(cli, args, incomplete, *, as_strings: bool = True):
        if as_strings:
            return _get_words(cli, args, incomplete)
        else:
            return _get_completions(cli, args, incomplete)

    return complete


# NOTE: this function was lifted directly from click test_shell_completion.py
# https://github.com/pallets/click/blob/923d197b56caa9ffea21edeef5baf1816585b099/tests/test_shell_completion.py#L21-L22
def _get_words(cli, args, incomplete):
    return [c.value for c in _get_completions(cli, args, incomplete)]


# NOTE: this function was lifted directly from click test_shell_completion.py
# https://github.com/pallets/click/blob/923d197b56caa9ffea21edeef5baf1816585b099/tests/test_shell_completion.py#L16-L18
def _get_completions(cli, args, incomplete):
    comp = ShellComplete(cli, {}, cli.name, "_CLICK_COMPLETE")
    return comp.get_completions(args, incomplete)
