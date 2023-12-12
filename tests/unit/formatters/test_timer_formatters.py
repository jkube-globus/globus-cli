import datetime

import pytest

from globus_cli.commands.timer._common import (
    CallbackActionTypeFormatter,
    ScheduleFormatter,
)


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


start_string = "2023-12-19T21:00:00+03:00"
end_string = "2024-01-01T15:16:17-14:00"
start_rendered = (
    datetime.datetime.fromisoformat(start_string)
    .astimezone()
    .strftime("%Y-%m-%d %H:%M:%S")
)
end_rendered = (
    datetime.datetime.fromisoformat(end_string)
    .astimezone()
    .strftime("%Y-%m-%d %H:%M:%S")
)


@pytest.mark.parametrize(
    "value, expected_template",
    (
        pytest.param(
            {
                "end": {"count": 3},
                "interval_seconds": 86400,
                "start": start_string,
                "type": "recurring",
            },
            "every 86400 seconds, starting {start} and running for 3 iterations",
            id="start-end-count",
        ),
        pytest.param(
            {
                "end": {"datetime": end_string},
                "interval_seconds": 86400,
                "start": start_string,
                "type": "recurring",
            },
            "every 86400 seconds, starting {start} and running until {end}",
            id="start-end-datetime",
        ),
        pytest.param(
            {
                "datetime": start_string,
                "type": "once",
            },
            "once at {start}",
            id="start-once",
        ),
    ),
)
def test_schedule_formatter(value, expected_template):
    expected = expected_template.format(start=start_rendered, end=end_rendered)
    assert ScheduleFormatter().render(value) == expected
