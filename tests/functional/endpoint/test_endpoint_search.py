from __future__ import annotations

import random
import typing as t
import uuid

import pytest
from globus_sdk._testing import RegisteredResponse


def _make_mapped_collection_search_result(
    collection_id: str,
    endpoint_id: str,
    *,
    display_name: str = "dummy result",
    authentication_timeout_mins: int = 15840,
) -> dict[str, t.Any]:
    username = "u_abcdefghijklmnop"  # not a real b32 username
    owner_string = "globus@globus.org"
    manager_fqdn = "a0bc1.23de.data.globus.org"
    collection_fqdn = f"m-f45678.{manager_fqdn}"
    gcs_version = "5.4.50"
    data = {
        "DATA_TYPE": "endpoint",
        "_rank": random.random() * 10,
        "authentication_timeout_mins": authentication_timeout_mins,
        "canonical_name": f"u_{username}#{collection_id}",
        "default_directory": "/{server_default}/",
        "display_name": display_name,
        "entity_type": "GCSv5_mapped_collection",
        "expires_in": -1,
        "gcs_manager_url": f"https://{manager_fqdn}",
        "gcs_version": gcs_version,
        "id": collection_id,
        "location": "Automatic",
        "max_concurrency": 4,
        "max_parallelism": 8,
        "my_effective_roles": [],
        "myproxy_server": "myproxy.globusonline.org",
        "name": collection_id,
        "network_use": "normal",
        "non_functional_endpoint_display_name": f"host of {display_name}",
        "non_functional_endpoint_id": endpoint_id,
        "owner_id": endpoint_id,
        "owner_string": owner_string,
        "preferred_concurrency": 2,
        "preferred_parallelism": 4,
        "public": True,
        "shareable": True,
        "tlsftp_server": f"tlsftp://{collection_fqdn}:443",
        "username": username,
    }
    # there are so many null and False values in a typical item, it's worth packing them
    # in strings and filling them in loops -- makes the document above more readable
    null_keys = """
        acl_max_expiration_period_mins authentication_assurance_timeout
        authentication_policy_id contact_email contact_info department description
        expire_time gcp_connected gcp_paused globus_connect_setup_key host_endpoint
        host_endpoint_display_name host_endpoint_id host_path https_server info_link
        keywords last_accessed_time local_user_info_available
        mapped_collection_display_name mapped_collection_id myproxy_dn oauth_server
        organization s3_url sharing_target_endpoint sharing_target_root_path
        subscription_id user_message user_message_link
    """.split()
    false_keys = """
        acl_available acl_editable activated disable_anonymous_writes disable_verify
        force_encryption force_verify french_english_bilingual high_assurance in_use
        is_globus_connect mfa_required non_functional requester_pays s3_owner_activated
    """.split()
    for k in null_keys:
        data[k] = None
    for k in false_keys:
        data[k] = False
    return data


@pytest.fixture
def singular_search_response():
    collection_id = str(uuid.uuid4())
    endpoint_id = str(uuid.uuid4())
    return RegisteredResponse(
        service="transfer",
        path="/endpoint_search",
        metadata={
            "collection_id": collection_id,
            "endpoint_id": endpoint_id,
        },
        json={
            "DATA": [_make_mapped_collection_search_result(collection_id, endpoint_id)],
            "DATA_TYPE": "endpoint_list",
            "has_next_page": False,
            "limit": 25,
            "offset": 0,
        },
    )


def test_search_shows_collection_id(run_line, singular_search_response):
    singular_search_response.add()
    meta = singular_search_response.metadata
    collection_id = meta["collection_id"]
    endpoint_id = meta["endpoint_id"]

    result = run_line("globus endpoint search mytestquery")

    lines = result.output.rstrip("\n").split("\n")
    assert len(lines) == 3
    assert endpoint_id not in lines[-1]
    assert collection_id in lines[-1]
