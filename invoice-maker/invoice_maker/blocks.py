"""Small rendering helpers shared by every invoice template.

Keep this module to genuinely template-agnostic primitives only -- a
specific layout (column counts, spans, colours) belongs in the template
module that uses it, not here.
"""

from __future__ import annotations

from datetime import date

from reportlab.lib import colors
from reportlab.platypus import Paragraph, Table, TableStyle


def p(text, style) -> Paragraph:
    """Paragraph from plain text/HTML-ish markup, tolerating None/empty values."""
    safe = (str(text) if text is not None else "").replace("\n", "<br/>")
    return Paragraph(safe or "&nbsp;", style)


def money(value: float) -> str:
    """Fixed 2-decimal money formatting, e.g. 3500 -> '3,500.00'."""
    return f"{value:,.2f}"


def money_smart(value: float) -> str:
    """Money formatting that drops a trailing '.00'.

    Some reference invoices (the plain item/qty/total style) always show
    whole-dollar line items without decimals, e.g. '3,500' not '3,500.00'.
    """
    return f"{value:,.0f}" if float(value).is_integer() else f"{value:,.2f}"


def fmt_date(value: date, style: str = "short") -> str:
    if not value:
        return ""
    if style == "long":
        return f"{value:%B} {value.day}, {value.year}"
    return f"{value.day}-{value.strftime('%b')}-{value.year}"


def rule_bar(width: float, height: float = 2.5, color=colors.black) -> Table:
    """A solid horizontal divider bar, ``width`` points wide."""
    bar = Table([[""]], colWidths=[width], rowHeights=[height])
    bar.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), color)]))
    return bar
