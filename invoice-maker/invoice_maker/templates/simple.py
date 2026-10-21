"""The plain item invoice template.

Used for one-off invoices you receive from a vendor/artist: an "invoice"
wordmark, invoice #/date due/pay method, an optional payment-installment
badge, an item/qty/price/total table, an amount-due box, and a
vendor/bill-to footer. See ``glitch.py`` for the timesheet-style template.
"""

from __future__ import annotations

from typing import List

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Spacer, Table, TableStyle

from ..blocks import fmt_date, money_smart, p, rule_bar
from ..constants import CURRENCY_SYMBOLS, SIMPLE_BOX_GREY, SIMPLE_COL_WIDTHS, SIMPLE_LINK_COLOR
from ..models import Config, SimpleInvoice
from .base import TemplateSpec

TOTAL_WIDTH = sum(SIMPLE_COL_WIDTHS)

LOGO_STYLE = ParagraphStyle(
    "logo", fontName="Helvetica-Bold", fontSize=34, leading=34, textColor=colors.black
)
INSTALLMENT_STYLE = ParagraphStyle(
    "installment", fontName="Helvetica", fontSize=8.5, leading=11, alignment=TA_RIGHT
)
LINK_STYLE = ParagraphStyle(
    "link", fontName="Helvetica", fontSize=9, leading=12, alignment=TA_RIGHT,
    textColor=SIMPLE_LINK_COLOR,
)
META_STYLE = ParagraphStyle("meta", fontName="Helvetica", fontSize=9, leading=13)
TABLE_HEADER = ParagraphStyle("table_header", fontName="Helvetica-Oblique", fontSize=8.5, leading=11)
TABLE_HEADER_R = ParagraphStyle(
    "table_header_r", fontName="Helvetica-Oblique", fontSize=8.5, leading=11, alignment=TA_RIGHT
)
ITEM_STYLE = ParagraphStyle("item", fontName="Helvetica", fontSize=9, leading=12)
CELL_R = ParagraphStyle("cell_r", fontName="Helvetica", fontSize=9, leading=12, alignment=TA_RIGHT)
AMOUNT_LABEL = ParagraphStyle("amount_label", fontName="Helvetica-Bold", fontSize=10, leading=13)
AMOUNT_VALUE = ParagraphStyle(
    "amount_value", fontName="Helvetica-Bold", fontSize=10, leading=13, alignment=TA_RIGHT
)
FOOTER_BOLD = ParagraphStyle("footer_bold", fontName="Helvetica-Bold", fontSize=8.5, leading=12)
FOOTER_NORMAL = ParagraphStyle("footer_normal", fontName="Helvetica", fontSize=8.5, leading=12)
FOOTER_RIGHT = ParagraphStyle(
    "footer_right", fontName="Helvetica", fontSize=8.5, leading=12, alignment=TA_RIGHT
)
FOOTER_RIGHT_BOLD = ParagraphStyle(
    "footer_right_bold", fontName="Helvetica-Bold", fontSize=8.5, leading=12, alignment=TA_RIGHT
)


def _qty(value: float) -> str:
    return f"{value:g}"


def _header_section(inv: SimpleInvoice) -> Table:
    logo = p("invoice", LOGO_STYLE)

    right_lines = []
    if inv.installment.is_multi:
        label = f" ({inv.installment.label})" if inv.installment.label else ""
        right_lines.append(f"Installment {inv.installment.current} of {inv.installment.total}{label}")
    right = p("<br/>".join(right_lines), INSTALLMENT_STYLE) if right_lines else ""

    if inv.payment_link_text:
        if inv.payment_link_url:
            link_markup = f'<link href="{inv.payment_link_url}"><u>{inv.payment_link_text}</u></link>'
        else:
            link_markup = f"<u>{inv.payment_link_text}</u>"
        link_p = p(link_markup, LINK_STYLE)
    else:
        link_p = ""

    rows = [[logo, right], ["", link_p]]
    table = Table(rows, colWidths=[300, TOTAL_WIDTH - 300])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("SPAN", (0, 0), (0, 1)),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return table


def _meta_section(inv: SimpleInvoice) -> Table:
    rows = [
        [p("Invoice number", META_STYLE), p(inv.invoice_number, META_STYLE)],
        [p("Date due", META_STYLE), p(fmt_date(inv.date_due, "long"), META_STYLE)],
        [p("Pay method", META_STYLE), p(inv.pay_method, META_STYLE)],
    ]
    table = Table(rows, colWidths=[110, TOTAL_WIDTH - 110])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return table


def _items_section(inv: SimpleInvoice) -> Table:
    header = [
        p("Item", TABLE_HEADER),
        p("Qty", TABLE_HEADER_R),
        p("Price/unit", TABLE_HEADER_R),
        p("Total", TABLE_HEADER_R),
        p("Current Due", TABLE_HEADER_R),
    ]
    rows: List[list] = [header]
    for item in inv.items:
        desc = f"<b>{item.description}</b>" if item.description else ""
        if item.credit:
            desc += f" &mdash; <i>{item.credit}</i>"
        rows.append([
            p(desc, ITEM_STYLE),
            p(_qty(item.qty), CELL_R),
            p(money_smart(item.unit_price), CELL_R),
            p(money_smart(item.total), CELL_R),
            p(money_smart(item.current_due), CELL_R),
        ])

    table = Table(rows, colWidths=SIMPLE_COL_WIDTHS, repeatRows=1)
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.75, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def _amount_due_section(inv: SimpleInvoice) -> Table:
    symbol = CURRENCY_SYMBOLS.get(inv.currency, "")
    value = f"{symbol}{money_smart(inv.amount_due())} {inv.currency}"
    rows = [[p("Amount Due", AMOUNT_LABEL), p(value, AMOUNT_VALUE)]]
    table = Table(rows, colWidths=[TOTAL_WIDTH * 0.55, TOTAL_WIDTH * 0.45])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SIMPLE_BOX_GREY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    return table


def _footer_columns(inv: SimpleInvoice) -> Table:
    col_width = TOTAL_WIDTH / 3

    left = Table(
        [[p(inv.vendor.name, FOOTER_BOLD)], [p(inv.vendor.email, FOOTER_NORMAL)]],
        colWidths=[col_width],
    )
    middle = Table(
        [[p("Invoice to", FOOTER_BOLD)], [p(inv.bill_to_name, FOOTER_NORMAL)]],
        colWidths=[col_width],
    )
    right_rows = []
    if inv.note:
        right_rows.append([p(inv.note, FOOTER_RIGHT)])
    if inv.closing:
        right_rows.append([p(inv.closing, FOOTER_RIGHT_BOLD)])
    right = Table(right_rows or [[""]], colWidths=[col_width])

    cell_style = TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ])
    for t in (left, middle, right):
        t.setStyle(cell_style)

    footer_row = Table([[left, middle, right]], colWidths=[col_width] * 3)
    footer_row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
    ]))
    return footer_row


def build(config: Config, inv: SimpleInvoice) -> List:
    return [
        _header_section(inv),
        Spacer(1, 14),
        _meta_section(inv),
        Spacer(1, 22),
        _items_section(inv),
        Spacer(1, 24),
        _amount_due_section(inv),
        Spacer(1, 140),
        rule_bar(TOTAL_WIDTH),
        Spacer(1, 8),
        _footer_columns(inv),
    ]


def _prepare(config: Config, inv: SimpleInvoice) -> None:
    if not inv.bill_to_name:
        inv.bill_to_name = config.business.name or config.business.company


def _doc_meta(config: Config, inv: SimpleInvoice) -> dict:
    return {"title": f"Invoice {inv.invoice_number}", "author": inv.vendor.name}


def _filename(config: Config, inv: SimpleInvoice) -> str:
    who = (inv.vendor.name or "Invoice").strip()
    who = "".join(c for c in who if c.isalnum() or c in " _-").strip().replace(" ", "_")
    number = "".join(c for c in inv.invoice_number if c.isalnum() or c in "_-")
    return f"INVOICE_{number}_{who}.pdf"


SPEC = TemplateSpec(
    name="simple",
    data_model=SimpleInvoice,
    build=build,
    doc_meta=_doc_meta,
    filename=_filename,
    margins={"left": 40, "right": 40, "top": 40, "bottom": 40},
    prepare=_prepare,
)
