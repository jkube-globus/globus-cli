### Bugfixes

* In certain conditions, the CLI would not handle Broken Pipe errors (EPIPE)
  correctly, resulting in error messages on stderr when commands were piped to
  commands like `head`. The handling of broken pipes has been improved to avoid
  these spurious error messages.
