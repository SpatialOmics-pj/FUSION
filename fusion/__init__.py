"""Stable public entry points for FUSION.

Imports are intentionally lazy so that ``import fusion`` can be used to check
an installation before the optional R bridge is configured.
"""

from importlib.metadata import PackageNotFoundError, version
from typing import Any

try:
    __version__ = version("fusion-srt")
except PackageNotFoundError:  # Running directly from a source checkout.
    __version__ = "0.1.0"

__all__ = [
    "FUSION_Init",
    "FUSION_preprocess",
    "FUSION_main",
    "FUSION_correction",
    "section_alignment",
]


def FUSION_Init(*args: Any, **kwargs: Any) -> Any:
    from R_initialization import FUSION_Init as implementation

    return implementation(*args, **kwargs)


def FUSION_preprocess(*args: Any, **kwargs: Any) -> Any:
    from main_ref import FUSION_preprocess as implementation

    return implementation(*args, **kwargs)


def FUSION_main(*args: Any, **kwargs: Any) -> Any:
    from main_ref import FUSION_main as implementation

    return implementation(*args, **kwargs)


def FUSION_correction(*args: Any, **kwargs: Any) -> Any:
    from r_batch import FUSION_correction as implementation

    return implementation(*args, **kwargs)


def section_alignment(*args: Any, **kwargs: Any) -> Any:
    from utils import section_alignment as implementation

    return implementation(*args, **kwargs)

