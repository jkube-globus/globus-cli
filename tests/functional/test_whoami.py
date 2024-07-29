from globus_sdk._testing import load_response_set


def test_verbose(run_line):
    """
    Confirms --verbose includes Name, Email, and ID fields.
    """
    meta = load_response_set("cli.foo_user_info").metadata

    result = run_line("globus whoami --verbose")
    for field in ["Username", "Name", "Email", "ID"]:
        assert field in result.output
    for field in ["username", "name", "email", "user_id"]:
        assert meta[field] in result.output


def test_linked_identities(run_line):
    """
    Confirms --linked-identities sees foo2.
    """
    meta = load_response_set("cli.foo_user_info").metadata
    username = meta["username"]
    linked_usernames = [x["username"] for x in meta["linked_ids"]]

    result = run_line("globus whoami --linked-identities")
    assert username in result.output
    for n in linked_usernames:
        assert n in result.output


def test_verbose_linked_identities(run_line):
    """
    Confirms combining --verbose and --linked-identities has expected
    values present for the whole identity set.
    """
    meta = load_response_set("cli.foo_user_info").metadata
    linked_users = meta["linked_ids"]

    result = run_line("globus whoami --linked-identities -v")

    for field in ["Username", "Name", "Email", "ID"]:
        assert field in result.output
    for field in ["username", "name", "email", "user_id"]:
        assert meta[field] in result.output
        for x in linked_users:
            assert x[field] in result.output
