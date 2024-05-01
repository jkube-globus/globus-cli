from globus_sdk._testing import RegisteredResponse


def test_flows_validation_hook_on_single_error(run_line):
    RegisteredResponse(
        service="flows",
        path="/flow/validate",
        method="POST",
        status=422,
        json={
            "error": {
                "code": "UNPROCESSABLE_ENTITY",
                "detail": [
                    {
                        "loc": ["definition", "States", "hi"],
                        "msg": "Discriminator 'type' is missing in value",
                        "type": (
                            "value_error.discriminated_union.missing_discriminator"
                        ),
                        "ctx": {"discriminator_key": "type"},
                    }
                ],
                "message": (
                    "1 validation error in body. "
                    "$.definition.States.hi: "
                    "Discriminator 'type' is missing in value"
                ),
            },
            "debug_id": "7bb1ddee-f41d-4e80-9bd7-fd16966e783b",
        },
    ).add()
    result = run_line(
        "globus api flows POST /flow/validate --body "
        '\'{"definition": {"StartAt": "hi", "States": {"hi": {}}}}\'',
        assert_exit_code=1,
    )
    assert "A Flows API Error Occurred." in result.stderr
    assert (
        "$.definition.States.hi: Discriminator 'type' is missing in value"
        in result.stderr
    )
