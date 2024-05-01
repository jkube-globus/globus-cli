import json

from globus_sdk._testing import RegisteredResponse


def test_base_json_hook(run_line):
    """
    confirms that the base json hook captures the error JSON and prints it verbatim
    """
    response = RegisteredResponse(
        service="transfer",
        path="/foo",
        status=400,
        json={"bar": "baz"},
    ).add()
    result = run_line("globus api transfer GET /foo -Fjson", assert_exit_code=1)
    assert response.json == json.loads(result.stderr)
