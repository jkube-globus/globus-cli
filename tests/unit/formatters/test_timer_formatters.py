import pytest

from globus_cli.commands.timer._common import CallbackActionTypeFormatter


@pytest.mark.parametrize(
    "value, expected",
    (
        ("https://actions.automate.globus.org/transfer/transfer/run", "Transfer"),
        ("https://transfer.actions.integration.globuscs.info/transfer/run", "Transfer"),
        ("https://flows.automate.globus.org", "Flow"),
        ("bogus", "bogus"),
    ),
)
def test_action_formatter(value, expected):
    assert CallbackActionTypeFormatter().render(value) == expected
