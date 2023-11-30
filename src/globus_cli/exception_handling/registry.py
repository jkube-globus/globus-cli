from __future__ import annotations

import functools
import typing as t

import click
import globus_sdk

from globus_cli.parsing.command_state import CommandState

E = t.TypeVar("E", bound=Exception)

HOOK_TYPE = t.Callable[[E], t.NoReturn]
# something which can be decorated to become a hook
_HOOK_SRC_TYPE = t.Union[t.Callable[[E], None], t.Callable[[E], t.Optional[int]]]

CONDITION_TYPE = t.Callable[[E], bool]

_REGISTERED_HOOKS: list[tuple[HOOK_TYPE, CONDITION_TYPE]] = []


def sdk_error_handler(
    *,
    error_class: str = "GlobusAPIError",
    condition: t.Callable[[globus_sdk.GlobusAPIError], bool] | None = None,
    exit_status: int = 1,
) -> t.Callable[[_HOOK_SRC_TYPE], HOOK_TYPE]:
    return _error_handler(
        condition=_build_condition(condition, error_class), exit_status=exit_status
    )


def error_handler(
    *,
    error_class: type[Exception] | None = None,
    condition: t.Callable[[globus_sdk.GlobusAPIError], bool] | None = None,
    exit_status: int = 1,
) -> t.Callable[[_HOOK_SRC_TYPE], HOOK_TYPE]:
    return _error_handler(
        condition=_build_condition(condition, error_class), exit_status=exit_status
    )


def find_handler(exception: Exception) -> HOOK_TYPE | None:
    for handler, condition in _REGISTERED_HOOKS:
        if not condition(exception):
            continue
        return handler
    return None


def _error_handler(
    *,
    condition: t.Callable[[Exception], bool],
    exit_status: int = 1,
) -> t.Callable[[_HOOK_SRC_TYPE], HOOK_TYPE]:
    """decorator for excepthooks

    register each one, in order, with any relevant "condition"
    """

    def inner_decorator(fn: _HOOK_SRC_TYPE) -> HOOK_TYPE:
        @functools.wraps(fn)
        def wrapped(exception: Exception) -> t.NoReturn:
            hook_result = fn(exception)
            ctx = click.get_current_context()

            if isinstance(exception, globus_sdk.GlobusAPIError):
                # get the mapping by looking up the state and getting the mapping attr
                mapping = ctx.ensure_object(CommandState).http_status_map

                # if there is a mapped exit code, exit with that. Otherwise, exit below
                if exception.http_status in mapping:
                    ctx.exit(mapping[exception.http_status])

            # if the hook instructed that a specific error code be used, use that
            if hook_result is not None:
                ctx.exit(hook_result)

            ctx.exit(exit_status)

        _REGISTERED_HOOKS.append((wrapped, condition))
        return wrapped

    return inner_decorator


def _build_condition(
    condition: CONDITION_TYPE | None, error_class: str | type[Exception] | None
) -> CONDITION_TYPE:
    inner_condition: CONDITION_TYPE

    if condition is None:
        if error_class is None:
            raise ValueError("a hook must specify either condition or error_class")

        def inner_condition(exception: Exception) -> bool:
            error_class_ = _resolve_error_class(error_class)
            return isinstance(exception, error_class_)

    elif error_class is None:
        inner_condition = condition

    else:

        def inner_condition(exception: Exception) -> bool:
            error_class_ = _resolve_error_class(error_class)
            return isinstance(exception, error_class_) and condition(exception)

    return inner_condition


def _resolve_error_class(error_class: str | type[Exception]) -> type[Exception]:
    if isinstance(error_class, str):
        resolved = getattr(globus_sdk, error_class, None)
        if resolved is None:
            raise LookupError(f"no such globus_sdk error class '{error_class}'")
        if not (isinstance(resolved, type) and issubclass(resolved, Exception)):
            raise ValueError(f"'globus_sdk.{error_class}' is not an error class")
        return resolved
    else:
        return error_class
