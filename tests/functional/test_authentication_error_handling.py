"""
tests for scenarios in which the credentials in use by the CLI have been
invalidated and are treated as invalid by the services
"""

import uuid

from globus_sdk._testing import RegisteredResponse


def test_whoami_unauthorized_error(run_line):
    RegisteredResponse(
        service="auth",
        path="/v2/oauth2/userinfo",
        status=401,
        json={"code": "UNAUTHORIZED", "message": "foo bar"},
    ).add()
    result = run_line("globus whoami", assert_exit_code=1)
    assert "Unable to get user information" in result.stderr


def test_auth_api_call_unauthorized(run_line):
    RegisteredResponse(
        service="auth",
        path="/v2/api/identities",
        status=401,
        json={"code": "UNAUTHORIZED", "message": "foo bar"},
    ).add()
    result = run_line(
        "globus get-identities foo@globusid.org",
        assert_exit_code=1,
    )
    assert "No Authentication provided." in result.stderr


def test_transfer_call_unauthorized(run_line):
    ep_id = str(uuid.uuid1())
    RegisteredResponse(
        service="transfer",
        path=f"/operation/endpoint/{ep_id}/ls",
        status=401,
        json={
            "code": "ClientError.AuthenticationFailed",
            "message": "foo bar",
            "request_id": "abc123",
        },
    ).add()
    result = run_line(["globus", "ls", ep_id], assert_exit_code=1)
    assert "No Authentication provided." in result.stderr
