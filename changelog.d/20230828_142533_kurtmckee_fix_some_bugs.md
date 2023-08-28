### Bugfixes

*   Make `--no-recursive` and `--batch` mutually exclusive options.

    This affects the `globus transfer` and the `globus timer create transfer` commands.

    Previously, `--no-recursive` was not caught because of its internal representation.
    This is now fixed, so `--no-recursive` cannot be combined with `--batch`.
