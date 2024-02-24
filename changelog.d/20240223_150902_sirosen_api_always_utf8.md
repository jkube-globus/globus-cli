### Bugfixes

* Payloads sent with `globus api` commands are now always encoded as UTF-8.
  This fixes an issue on certain platforms in which encoding could fail on
  specific payloads.
