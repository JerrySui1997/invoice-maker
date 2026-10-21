"""Template registry: pluggable invoice styles.

To add a new invoice style: create ``invoice_maker/templates/<name>.py``
exposing a module-level ``SPEC`` (a :class:`TemplateSpec`), then register
it below. Nothing outside this package needs to change -- the CLI and
renderer both work against the ``TemplateSpec`` contract.
"""

from __future__ import annotations

from .base import TemplateSpec
from . import glitch, simple

REGISTRY = {
    "glitch": glitch.SPEC,
    "simple": simple.SPEC,
}


def get_template(name: str) -> TemplateSpec:
    name = name or "glitch"
    try:
        return REGISTRY[name]
    except KeyError:
        available = ", ".join(sorted(REGISTRY))
        raise ValueError(f"Unknown invoice template '{name}'. Available: {available}")


__all__ = ["TemplateSpec", "REGISTRY", "get_template"]
