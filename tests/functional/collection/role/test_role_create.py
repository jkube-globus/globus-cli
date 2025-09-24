from globus_sdk._testing import RegisteredResponse, load_response_set


def test_successful_gcs_collection_role_creation(
    run_line,
    add_gcs_login,
):
    # setup data for the collection_id -> endpoint_id lookup
    # and create dummy credentials for the test to run against that GCS
    meta = load_response_set("cli.collection_operations").metadata
    endpoint_id = meta["endpoint_id"]
    user_id = meta["role_identity_id"]
    role = meta["role"]
    role_id = meta["role_id"]
    collection_id = meta["mapped_collection_id"]
    add_gcs_login(endpoint_id)

    role = "activity_monitor"

    # mock the responses for the Delete Role API (GCS)
    RegisteredResponse(
        service="gcs",
        path="/roles/",
        json={
            "DATA_TYPE": "role#1.0.0",
            "collection": f"{collection_id}",
            "id": f"{role_id}",
            "principal": f"urn:globus:auth:identity:{user_id}",
            "role": "activity_monitor",
        },
    ).add()

    # now test the command and confirm that a successful role creation is reported
    run_line(
        ["globus", "collection", "role", "create", collection_id, role, user_id],
        search_stdout=[
            "success",
        ],
    )
