def supported_activation_methods(res):
    """
    Given an activation_requirements document
    returns a list of activation methods supported by this endpoint.
    """
    supported = ["web"]  # web activation is always supported.

    # oauth
    if res["oauth_server"]:
        supported.append("oauth")

    for req in res["DATA"]:
        # myproxy
        if (
            req["type"] == "myproxy"
            and req["name"] == "hostname"
            and req["value"] != "myproxy.globusonline.org"
        ):
            supported.append("myproxy")

        # delegate_proxy
        if req["type"] == "delegate_proxy" and req["name"] == "public_key":
            supported.append("delegate_proxy")

    return supported


def activation_requirements_help_text(res, ep_id):
    """
    Given an activation requirements document and an endpoint_id
    returns a string of help text for how to activate the endpoint
    """
    methods = supported_activation_methods(res)

    lines = [
        "This endpoint supports the following activation methods: ",
        ", ".join(methods).replace("_", " "),
        "\n",
        (
            "For web activation use:\n"
            "'globus endpoint activate --web {}'\n".format(ep_id)
            if "web" in methods
            else ""
        ),
        (
            "For myproxy activation use:\n"
            "'globus endpoint activate --myproxy {}'\n".format(ep_id)
            if "myproxy" in methods
            else ""
        ),
        (
            "For oauth activation use web activation:\n"
            "'globus endpoint activate --web {}'\n".format(ep_id)
            if "oauth" in methods
            else ""
        ),
        (
            "For delegate proxy activation use:\n"
            "'globus endpoint activate --delegate-proxy "
            "X.509_PEM_FILE {}'\n".format(ep_id)
            if "delegate_proxy" in methods
            else ""
        ),
        (
            "Delegate proxy activation requires an additional dependency on "
            "cryptography. See the docs for details:\n"
            "https://docs.globus.org/cli/reference/endpoint_activate/\n"
            if "delegate_proxy" in methods
            else ""
        ),
    ]

    return "".join(lines)
