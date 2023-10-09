import sys
import warnings

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

# this bool turns off all warning controls, handing control of python
# warnings to the testsuite
# this ensures that `pytest --filterwarnings error` works
_TEST_WARNING_CONTROL: bool = False


def simplefilter(
    filterstr: Literal["default", "error", "ignore", "always", "module", "once"]
) -> None:
    """
    wrap `warnings.simplefilter` with a check on `_TEST_WARNING_CONTROL`
    """
    if not _TEST_WARNING_CONTROL:
        warnings.simplefilter(filterstr)
