"""The contract every invoice template implements."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Type


@dataclass
class TemplateSpec:
    name: str
    data_model: Type              # dataclass with a `from_dict(raw)` classmethod
    build: Callable                # (config, invoice) -> List[Flowable]
    doc_meta: Callable             # (config, invoice) -> {"title": str, "author": str}
    filename: Callable             # (config, invoice) -> str, e.g. "INVOICE_123_Name.pdf"
    margins: dict                  # {"left", "right", "top", "bottom"} in points
    prepare: Optional[Callable] = None  # optional (config, invoice) -> None, fills defaults
