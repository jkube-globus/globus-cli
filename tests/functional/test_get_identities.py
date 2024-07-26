import json

from globus_sdk._testing import RegisteredResponse, load_response, load_response_set


def test_default_one_id(run_line):
    """
    Runs get-identities with one id, confirms correct username returned.
    """
    meta = load_response_set("cli.foo_user_info").metadata
    user_id = meta["user_id"]
    username = meta["username"]
    result = run_line(f"globus get-identities {user_id}")
    assert username + "\n" == result.output


def test_default_one_username(run_line):
    """
    Runs get-identities with one username, confirms correct id returned.
    """
    meta = load_response_set("cli.foo_user_info").metadata
    user_id = meta["user_id"]
    username = meta["username"]
    result = run_line("globus get-identities " + username)
    assert user_id + "\n" == result.output


def test_default_nosuchidentity(run_line):
    """
    Runs get-identities with one username, confirms correct id returned.
    """
    load_response(
        RegisteredResponse(
            service="auth", path="/v2/api/identities", json={"identities": []}
        )
    )
    result = run_line("globus get-identities invalid@nosuchdomain.exists")
    assert "NO_SUCH_IDENTITY\n" == result.output


def test_invalid_username(run_line):
    # check that 'invalid' is called out as not being a valid username or identity
    result = run_line("globus get-identities invalid", assert_exit_code=2)
    assert "'invalid' does not appear to be a valid identity" in result.stderr


def test_default_multiple_inputs(run_line):
    """
    Runs get-identities with id username, duplicate and invalid inputs
    Confirms order is preserved and all values are as expected
    """
    meta = load_response_set("cli.multiuser_get_identities").metadata
    users = meta["users"]
    in_vals = [
        users[0]["username"],
        users[0]["user_id"],
        "invalid@nosuchdomain.exists",
        users[1]["username"],
        users[1]["username"],
    ]

    expected = [
        users[0]["user_id"],
        users[0]["username"],
        "NO_SUCH_IDENTITY",
        users[1]["user_id"],
        users[1]["user_id"],
    ]

    result = run_line("globus get-identities " + " ".join(in_vals))
    assert "\n".join(expected) + "\n" == result.output


def test_verbose(run_line):
    """
    Runs get-identities with --verbose, confirms expected fields found.
    """
    meta = load_response_set("cli.foo_user_info").metadata
    user_id = meta["user_id"]
    result = run_line("globus get-identities --verbose " + user_id)
    for key in ["username", "user_id", "name", "organization", "email"]:
        assert meta[key] in result.output


def test_json(run_line):
    """
    Runs get-identities with -F json confirms expected values.
    """
    meta = load_response_set("cli.foo_user_info").metadata
    user_id = meta["user_id"]
    output = json.loads(run_line("globus get-identities -F json " + user_id).output)
    assert meta["user_id"] == output["identities"][0]["id"]
    for key in ["username", "name", "organization", "email"]:
        assert meta[key] == output["identities"][0][key]
