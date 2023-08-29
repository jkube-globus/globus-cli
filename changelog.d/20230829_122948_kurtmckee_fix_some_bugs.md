### Bugfixes

*   Fix a bug that caused `--batch` input files to default to non-recursive transfers.

    This affects the `globus transfer` and `globus timer create transfer` commands.

    It's now possible for `--batch` input files to use
    `--recursive` to enable recursive transfers
    or `--no-recursive` to explicitly disable recursive transfers.
    If neither option is specified, path type auto-detection
    will determine the correct recursion setting.
