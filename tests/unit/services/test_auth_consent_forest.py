import json
from unittest import mock

import pytest
from globus_sdk.experimental.scope_parser import Scope
from globus_sdk.scopes import MutableScope

from globus_cli.services.auth import ConsentForestResponse


def _make_response(data):
    raw_response = mock.Mock()
    raw_response.json.return_value = data
    raw_response.status_code = 200
    raw_response.reason = "OK"
    raw_response.headers = {}
    raw_response.text = json.dumps(data)
    raw_response.content = raw_response.text.encode()

    dummy_client = mock.Mock()
    return ConsentForestResponse(raw_response, client=dummy_client)


def test_empty_forest_has_no_data():
    forest = _make_response({"consents": []})
    assert forest.consents == []
    assert forest.top_level_consents() == []
    assert not forest.contains_scopes(["foo", "bar"])


def test_consent_forest_identifies_top_level_scopes():
    forest = _make_response(
        {
            "consents": [
                {
                    "dependency_path": [1],
                    "scope_name": "foo",
                },
                {
                    "dependency_path": [1, 2],
                    "scope_name": "bar",
                },
                {
                    "dependency_path": [3],
                    "scope_name": "baz",
                },
            ]
        }
    )

    assert len(forest.top_level_consents()) == 2
    assert [c["scope_name"] for c in forest.top_level_consents()] == ["foo", "baz"]


@pytest.mark.parametrize("mode", ("str", "parser_scope", "mutable_scope"))
def test_simple_forest_contains_scope_regardless_of_shape(mode):
    forest = _make_response(
        {
            "consents": [
                {
                    "dependency_path": [1],
                    "scope_name": "foo",
                },
                {
                    "dependency_path": [1, 2],
                    "scope_name": "bar",
                },
            ]
        }
    )

    if mode == "str":
        includes = ["foo[bar]"]
        not_includes = ["bar"]
    elif mode == "parser_scope":
        includes = [Scope.deserialize("foo[bar]")]
        not_includes = [Scope("bar")]
    elif mode == "mutable_scope":
        scope = MutableScope("foo")
        scope.add_dependency("bar")
        includes = [scope]
        not_includes = [MutableScope("bar")]
    else:
        raise NotImplementedError(f"Unknown test mode: {mode}")

    assert forest.contains_scopes(includes)
    assert not forest.contains_scopes(not_includes)
