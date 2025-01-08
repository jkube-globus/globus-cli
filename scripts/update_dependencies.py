#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import pathlib
import re
import urllib.request

REPO_ROOT = pathlib.Path(__file__).parent.parent


class Abort(RuntimeError):
    pass


def get_pkg_latest(name: str) -> str:
    with urllib.request.urlopen(f"https://pypi.python.org/pypi/{name}/json") as conn:
        version_data = json.load(conn)
    return str(version_data["info"]["version"])


def bump_pkg_version_on_file(
    path: pathlib.Path,
    pkg_name: str,
    new_version: str,
    *,
    version_format: str = r"(\d+\.\d+\.\d+)",
) -> None:
    print(f"updating {pkg_name} in {path.relative_to(REPO_ROOT)} ... ", end="")
    with open(path) as fp:
        content = fp.read()
    match = re.search(re.escape(pkg_name) + "==" + version_format + r"(\W|$)", content)
    if not match:
        raise Abort(f"{path} did not contain {pkg_name} version pattern")

    old_version = match.group(1)
    old_str = f"{pkg_name}=={old_version}"
    new_str = f"{pkg_name}=={new_version}"
    content = content.replace(old_str, new_str)
    with open(path, "w") as fp:
        fp.write(content)
    print("ok")


_all_pkgs = {
    "jmespath": "pyproject.toml",
    "responses": "pyproject.toml",
    "ruamel.yaml": "pyproject.toml",
    "globus-sdk": "pyproject.toml",
    "mypy": "pyproject.toml",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pkg",
        choices=_all_pkgs,
        action="append",
        help="select a dependency to update, defaults to all",
    )
    args = parser.parse_args()

    pkgs = args.pkg or _all_pkgs

    for pkg in pkgs:
        version = get_pkg_latest(pkg)
        bump_pkg_version_on_file(REPO_ROOT / _all_pkgs[pkg], pkg, version)


if __name__ == "__main__":
    main()
