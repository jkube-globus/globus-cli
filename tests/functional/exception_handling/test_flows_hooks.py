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


def test_flows_validation_hook_on_multiple_errors(run_line):
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
                        "loc": ["definition"],
                        "msg": "none is not an allowed value",
                        "type": "type_error.none.not_allowed",
                    },
                    {
                        "loc": ["StartAt"],
                        "msg": "extra fields not permitted",
                        "type": "value_error.extra",
                    },
                ],
                "message": (
                    "2 validation errors in body. "
                    "$.definition: none is not an allowed value ; "
                    "$.StartAt: extra fields not permitted"
                ),
            },
            "debug_id": "fae137a7-9e4d-4009-aec2-efe71d02c509",
        },
    ).add()
    result = run_line(
        "globus api flows POST /flow/validate --body "
        '\'{"definition": null, "StartAt": "4tehlulz"}\'',
        assert_exit_code=1,
    )
    assert "A Flows API Error Occurred." in result.stderr
    assert "$.definition: none is not an allowed value" in result.stderr
    assert "$.StartAt: extra fields not permitted" in result.stderr


def test_flows_validation_hook_on_multiple_strange_errors(run_line):
    RegisteredResponse(
        service="flows",
        path="/frobulate",
        method="POST",
        status=422,
        # this is an error shape which does not meet our expectations
        # verify that we still get the message field, at the very least
        json={
            "error": {
                "code": "UNPROCESSABLE_ENTITY",
                "detail": [
                    {
                        "loc": ["a"],
                        "msg": "messageA",
                        "type": "typeA",
                    },
                    {
                        "loc": ["b"],
                        "msg": "messageB",
                        "type": "typeB",
                    },
                    # perhaps there's a special case where 'msg' or 'loc' is absent...
                    {"type": "kaboom!"},
                ],
                "message": "it went boom",
            },
            "debug_id": "fae137a7-9e4d-4009-aec2-efe71d02c509",
        },
    ).add()
    result = run_line(
        "globus api flows POST /frobulate --body '[]'", assert_exit_code=1
    )
    assert "A Flows API Error Occurred." in result.stderr
    assert "it went boom" in result.stderr
