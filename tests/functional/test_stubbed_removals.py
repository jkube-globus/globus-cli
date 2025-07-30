import pytest


@pytest.mark.parametrize(
    "command",
    [
        pytest.param(["globus", "endpoint", "activate"], id="endpoint_activate"),
        pytest.param(["globus", "endpoint", "deactivate"], id="endpoint_deactivate"),
        pytest.param(
            ["globus", "endpoint", "is-activated"], id="endpoint_is_activated"
        ),
    ],
)
@pytest.mark.parametrize(
    "add_args",
    [
        pytest.param([], id="zero_args"),
        pytest.param(["foo"], id="one_arg"),
        pytest.param(["foo"] * 100, id="one_hundred_args"),
        pytest.param(["foo", "--bar", "--baz"], id="one_arg_two_opts"),
        pytest.param(["--bar", "quux"] * 10, id="ten_opts_with_values"),
    ],
)
def test_stubbed_removal_emits_explicit_error(run_line, command, add_args):
    result = run_line([*command, *add_args], assert_exit_code=1)
    expect_message = f"`{' '.join(command)}` has been removed from the Globus CLI."
    assert expect_message in result.stderr
