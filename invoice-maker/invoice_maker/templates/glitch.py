"""The Glitch Productions contractor timesheet template.

A grid of DAY/DATE/Project/.../Daily Total rows over a billing period,
with from/bill-to, rate/dates, payment-details, and totals sections
above and below it. This is the original (and default) invoice style;
see ``simple.py`` for the plain item/qty/total style.
"""

from __future__ import annotations

from typing import List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Spacer, Table, TableStyle

from ..blocks import fmt_date, money, p
from ..constants import COL_WIDTHS, DARK, HEADER_BLUE, LIGHT_BLUE
from ..models import Config, Invoice
from .base import TemplateSpec

# --- text styles -----------------------------------------------------------
VALUE_STYLE = ParagraphStyle("value", fontName="Helvetica", fontSize=8, leading=10)
VALUE_WHITE = ParagraphStyle(
    "value_white", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=colors.white
)
TITLE_STYLE = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=22, leading=24)
HDR_LABEL = ParagraphStyle(
    "hdr_label", fontName="Helvetica-Bold", fontSize=8, leading=9, alignment=TA_CENTER
)
HDR_VALUE = ParagraphStyle(
    "hdr_value", fontName="Helvetica", fontSize=8, leading=9, alignment=TA_CENTER
)
PAY_LABEL = ParagraphStyle(
    "pay_label", fontName="Helvetica-Bold", fontSize=7.5, leading=9, alignment=TA_RIGHT
)
HDR_DARK = ParagraphStyle(
    "hdr_dark", fontName="Helvetica-Bold", fontSize=7.5, leading=8.5,
    alignment=TA_CENTER, textColor=colors.white,
)
HDR_BLUE = ParagraphStyle(
    "hdr_blue", fontName="Helvetica-Bold", fontSize=7.5, leading=8.5,
    alignment=TA_CENTER, textColor=colors.black,
)


def _day_name(value) -> str:
    return value.strftime("%A").upper() if value else ""


def _hrs(value) -> str:
    if value in (None, ""):
        return ""
    return f"{float(value):g}"


# --- section builders ------------------------------------------------------
def _title_section(config: Config, inv: Invoice) -> Table:
    title = "TAX INVOICE" if config.gst.registered else "INVOICE"
    rows = [[
        p(title, TITLE_STYLE), "", "", "", "",
        p("Invoice #:", HDR_LABEL), p(inv.invoice_number, HDR_VALUE),
        p("Invoice Date:", HDR_LABEL), p(fmt_date(inv.invoice_date), HDR_VALUE),
    ]]
    table = Table(rows, colWidths=COL_WIDTHS)
    table.setStyle(TableStyle([
        ("SPAN", (0, 0), (1, 0)),
        ("SPAN", (2, 0), (4, 0)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (5, 0), (-1, 0), 8),
        ("FONTNAME", (5, 0), (5, 0), "Helvetica-Bold"),
        ("FONTNAME", (7, 0), (7, 0), "Helvetica-Bold"),
        ("BACKGROUND", (5, 0), (5, 0), HEADER_BLUE),
        ("BACKGROUND", (7, 0), (7, 0), HEADER_BLUE),
        ("ALIGN", (5, 0), (8, 0), "CENTER"),
        ("GRID", (5, 0), (8, 0), 0.5, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def _from_billto_section(config: Config) -> Table:
    biz = config.business
    left = [
        ("Company:", biz.company),
        ("Name:", biz.name),
        ("ABN:", biz.abn),
        ("Address:", biz.address),
        ("Email:", biz.email),
        ("Phone:", biz.phone),
    ]
    billto = "<b>{}</b><br/>{}".format(
        config.bill_to.name, "<br/>".join(config.bill_to.address_lines)
    )

    rows = []
    for index, (label, value) in enumerate(left):
        row = [label, p(value, VALUE_STYLE), "", "", "", "", "", "", ""]
        if index == 0:
            row[5] = p("Billed To:", VALUE_WHITE)
            row[6] = p(billto, VALUE_STYLE)
        rows.append(row)

    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BLUE),
        ("BACKGROUND", (5, 0), (5, 0), DARK),
        ("SPAN", (6, 0), (8, 5)),
        ("BOX", (0, 0), (4, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (4, -1), 0.5, colors.grey),
        ("BOX", (5, 0), (8, -1), 0.5, colors.grey),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for r in range(len(left)):
        style.append(("SPAN", (1, r), (4, r)))
    table = Table(rows, colWidths=COL_WIDTHS)
    table.setStyle(TableStyle(style))
    return table


def _rate_dates_section(inv: Invoice) -> Table:
    rows = [
        ["Rate Type:", "Currency Type:", "Rate:", "", "",
         "Work Start Date:", "", "", "Work End Date:"],
        [inv.rate_type, inv.currency, money(inv.rate), "", "",
         fmt_date(inv.work_start_date), "", "", fmt_date(inv.work_end_date)],
    ]
    table = Table(rows, colWidths=COL_WIDTHS)
    table.setStyle(TableStyle([
        ("SPAN", (5, 0), (6, 0)),
        ("SPAN", (5, 1), (6, 1)),
        ("SPAN", (3, 0), (4, 0)),
        ("SPAN", (3, 1), (4, 1)),
        ("SPAN", (7, 0), (7, 0)),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (2, 0), HEADER_BLUE),
        ("BACKGROUND", (5, 0), (6, 0), HEADER_BLUE),
        ("BACKGROUND", (8, 0), (8, 0), HEADER_BLUE),
        ("GRID", (0, 0), (2, 1), 0.5, colors.grey),
        ("GRID", (5, 0), (6, 1), 0.5, colors.grey),
        ("GRID", (8, 0), (8, 1), 0.5, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def _payment_section(config: Config) -> Table:
    pay = config.payment
    labels = [
        ("Bank Name:", pay.bank_name),
        ("Account Name:", pay.account_name),
        ("Account #:", pay.account_number),
        ("Swift Code:", pay.swift_code),
        ("BSB # (AUS):", pay.bsb),
        ("Routing # (USD):", pay.routing_number),
        ("IBAN # (EUR):", pay.iban),
        ("Paypal Email:", pay.paypal_email),
    ]

    rows = [["PAYMENT DETAILS:", "", "", "", "", "Bank Branch Address:", "", "", ""]]
    for index, (label, value) in enumerate(labels):
        row = [p(label, PAY_LABEL), p(value, VALUE_STYLE), "", "", "", "", "", "", ""]
        if index == 0:
            row[5] = p(pay.bank_branch_address, VALUE_STYLE)
        rows.append(row)

    style = [
        ("SPAN", (0, 0), (4, 0)),
        ("SPAN", (5, 0), (8, 0)),
        ("SPAN", (5, 1), (8, len(labels))),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (0, 0), (8, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (4, 0), HEADER_BLUE),
        ("BACKGROUND", (5, 0), (8, 0), HEADER_BLUE),
        ("ALIGN", (0, 1), (0, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (4, -1), 0.5, colors.grey),
        ("LINEAFTER", (4, 0), (4, -1), 0.5, colors.grey),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for r in range(1, len(labels) + 1):
        style.append(("SPAN", (1, r), (4, r)))
    table = Table(rows, colWidths=COL_WIDTHS)
    table.setStyle(TableStyle(style))
    return table


def _line_items_section(inv: Invoice) -> Table:
    header = [
        p("DAY", HDR_DARK), p("DATE", HDR_DARK), p("Project", HDR_BLUE),
        p("Ep #", HDR_BLUE), p("Task / Description", HDR_BLUE),
        p("Sick / Vacation hrs", HDR_BLUE), p("Day / Hours Worked", HDR_BLUE),
        p("Rate", HDR_DARK), p("Daily Total", HDR_DARK),
    ]
    rows: List[list] = [header]
    for item in inv.line_items:
        rate = item.effective_rate(inv.rate)
        rows.append([
            _day_name(item.date),
            fmt_date(item.date),
            item.project,
            item.episode,
            p(item.description, VALUE_STYLE),
            _hrs(item.sick_vacation_hrs),
            _hrs(item.hours_worked),
            money(rate),
            money(item.total(inv.rate)),
        ])

    table = Table(rows, colWidths=COL_WIDTHS, repeatRows=1)
    table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (0, 1), (3, -1), "CENTER"),
        ("ALIGN", (5, 1), (-1, -1), "CENTER"),
        # header colours: DAY/DATE dark, middle blue, Rate/Daily Total dark
        ("BACKGROUND", (0, 0), (1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (1, 0), colors.white),
        ("BACKGROUND", (2, 0), (6, 0), HEADER_BLUE),
        ("BACKGROUND", (7, 0), (8, 0), DARK),
        ("TEXTCOLOR", (7, 0), (8, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def _totals_section(config: Config, inv: Invoice) -> Table:
    subtotal = inv.subtotal()
    rows = [[
        "", "", "", "", "GRAND TOTAL:",
        _hrs(inv.total_sick_hours()), _hrs(inv.total_worked_hours()), "",
        money(subtotal),
    ]]

    if config.gst.registered:
        gst_amount = subtotal * config.gst.rate_percent / 100.0
        rows.append(["", "", "", "", f"GST ({_hrs(config.gst.rate_percent)}%):",
                     "", "", "", money(gst_amount)])
        rows.append(["", "", "", "", "TOTAL DUE:", "", "", "", money(subtotal + gst_amount)])
    else:
        rows.append(["", "", "", "", "TOTAL DUE:", "", "", "", money(subtotal)])

    rows.append(["", "", "", "", "CURRENCY:", "", "", "", inv.currency])

    last = len(rows) - 1
    style = [
        ("FONTSIZE", (4, 0), (-1, -1), 11),
        ("FONTNAME", (4, 0), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (4, 0), (4, -1), "CENTER"),
        ("ALIGN", (5, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (4, 0), (4, 0), DARK),
        ("TEXTCOLOR", (4, 0), (4, 0), colors.white),
        ("BACKGROUND", (8, 0), (8, 0), DARK),
        ("TEXTCOLOR", (8, 0), (8, 0), colors.white),
        ("BACKGROUND", (4, last), (4, last), HEADER_BLUE),
        ("BACKGROUND", (8, last), (8, last), HEADER_BLUE),
        ("GRID", (4, 0), (8, -1), 0.5, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    # Highlight the final "TOTAL DUE" amount.
    total_row = last - 1
    style.append(("BACKGROUND", (4, total_row), (4, total_row), DARK))
    style.append(("TEXTCOLOR", (4, total_row), (4, total_row), colors.white))
    style.append(("BACKGROUND", (8, total_row), (8, total_row), DARK))
    style.append(("TEXTCOLOR", (8, total_row), (8, total_row), colors.white))
    style.append(("FONTSIZE", (4, total_row), (8, total_row), 13))

    table = Table(rows, colWidths=COL_WIDTHS)
    table.setStyle(TableStyle(style))
    return table


def _comments_section(inv: Invoice) -> Table:
    rows = [
        ["ADDITIONAL COMMENTS: (For Accounting/Production Only)", "", "", "", "", "", "", "", ""],
        [p(inv.comments, VALUE_STYLE), "", "", "", "", "", "", "", ""],
    ]
    table = Table(rows, colWidths=COL_WIDTHS, rowHeights=[16, 46])
    table.setStyle(TableStyle([
        ("SPAN", (0, 0), (8, 0)),
        ("SPAN", (0, 1), (8, 1)),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.grey),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def build(config: Config, inv: Invoice) -> List:
    return [
        _title_section(config, inv),
        Spacer(1, 8),
        _from_billto_section(config),
        Spacer(1, 8),
        _rate_dates_section(inv),
        Spacer(1, 8),
        _payment_section(config),
        Spacer(1, 8),
        _line_items_section(inv),
        Spacer(1, 6),
        _totals_section(config, inv),
        Spacer(1, 8),
        _comments_section(inv),
    ]


def _doc_meta(config: Config, inv: Invoice) -> dict:
    return {
        "title": f"Invoice {inv.invoice_number}",
        "author": config.business.name or config.business.company,
    }


def _filename(config: Config, inv: Invoice) -> str:
    who = (config.business.name or config.business.company or "Invoice").strip()
    who = "".join(c for c in who if c.isalnum() or c in " _-").strip().replace(" ", "_")
    number = "".join(c for c in inv.invoice_number if c.isalnum() or c in "_-")
    return f"INVOICE_{number}_{who}.pdf"


SPEC = TemplateSpec(
    name="glitch",
    data_model=Invoice,
    build=build,
    doc_meta=_doc_meta,
    filename=_filename,
    margins={"left": 28, "right": 28, "top": 28, "bottom": 28},
)
