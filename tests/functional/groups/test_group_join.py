import json

import pytest
import responses
from globus_sdk._testing import load_response, register_response_set


@pytest.fixture(autouse=True, scope="session")
def _register_invitation_responses():
    group_id = "ee49e222-d007-11e4-8b51-22000aa51e6e"
    identity_id = "00000000-0000-0000-0000-000000000001"
    username = "test_user1"
    identity_id2 = "00000000-0000-0000-0000-000000000002"
    username2 = "test_user2"

    _common_metadata = {
        "group_id": group_id,
        "identity_id": identity_id,
        "username": username,
        "identity_id2": identity_id2,
        "username2": username2,
    }

    def action_response(action: str, success, *, error_detail_present=True):
        return {
            "service": "groups",
            "path": f"/groups/{group_id}",
            "method": "POST",
            "json": (
                {
                    action: [
                        {
                            "group_id": group_id,
                            "identity_id": identity_id,
                            "username": username,
                            "role": "member",
                            "status": "active",
                        }
                    ]
                }
                if success
                else {
                    action: [],
                    "errors": {
                        action: [
                            {
                                "code": "ERROR_ERROR_IT_IS_AN_ERROR",
                                "identity_id": identity_id,
                                **(
                                    {"detail": "Domo arigato, Mr. Roboto"}
                                    if error_detail_present
                                    else {}
                                ),
                            }
                        ]
                    },
                }
            ),
            "metadata": _common_metadata,
        }

    for action in ("join", "request_join"):
        register_response_set(
            f"group_{action}_response",
            {
                "default": action_response(action, True),
                "error": action_response(action, False),
                "error_nodetail": action_response(
                    action, False, error_detail_present=False
                ),
            },
            metadata=_common_metadata,
        )

    register_response_set(
        "group_join_userinfo",
        {
            "default": {
                "service": "auth",
                "path": "/v2/oauth2/userinfo",
                "json": {
                    "preferred_username": username,
                    "name": "Foo McUser",
                    "sub": identity_id,
                    "email": "foo.mcuser@globus.org",
                    "identity_set": [
                        {
                            "username": username2,
                            "name": "Foo2 McUser",
                            "sub": identity_id2,
                            "identity_provider": "c8abac57-560c-46c8-b386-f116ed8793d5",
                            "identity_provider_display_name": "Globus ID",
                            "organization": "McUsers and Company",
                            "status": "used",
                            "email": "foo2.mcuser@globus.org",
                        },
                        {
                            "username": username,
                            "name": "Foo McUser",
                            "sub": identity_id,
                            "identity_provider": "c8abac57-560c-46c8-b386-f116ed8793d5",
                            "identity_provider_display_name": "Globus ID",
                            "organization": "McUser Group",
                            "status": "used",
                            "email": "foo.mcuser@globus.org",
                        },
                    ],
                },
            }
        },
        metadata=_common_metadata,
    )


@pytest.mark.parametrize("action", ("join", "request_join"))
@pytest.mark.parametrize("with_id_arg", (True, False))
def test_group_join(run_line, action, with_id_arg):
    meta = load_response(f"group_{action}_response").metadata
    load_response("group_join_userinfo")

    add_args = []
    if with_id_arg:
        add_args = ["--identity", meta["identity_id"]]
    if action == "request_join":
        add_args.append("--request")
    result = run_line(["globus", "group", "join", meta["group_id"]] + add_args)
    assert meta["identity_id"] in result.output

    sent_data = json.loads(responses.calls[-1].request.body)
    assert action in sent_data
    assert len(sent_data[action]) == 1
    assert sent_data[action][0]["identity_id"] == meta["identity_id"]


@pytest.mark.parametrize("action", ("join", "request_join"))
@pytest.mark.parametrize("error_detail_present", (True, False))
def test_group_join_failure(run_line, action, error_detail_present):
    load_response("group_join_userinfo")
    meta = load_response(
        f"group_{action}_response",
        case="error" if error_detail_present else "error_nodetail",
    ).metadata

    add_args = []
    if action == "request_join":
        add_args.append("--request")
    result = run_line(
        ["globus", "group", "join", meta["group_id"]] + add_args, assert_exit_code=1
    )
    assert "Error" in result.stderr
    if error_detail_present:
        assert "Domo arigato" in result.stderr
    else:
        assert "Could not join group" in result.stderr

    # the request sent was as expected
    sent_data = json.loads(responses.calls[-1].request.body)
    assert action in sent_data
    assert len(sent_data[action]) == 1
    assert sent_data[action][0]["identity_id"] == meta["identity_id"]
