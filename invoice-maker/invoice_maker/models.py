"""Data models for the invoice maker.

`Config` holds the details that stay the same across invoices (your
business info, payment details, who you bill, GST settings). `Invoice`
holds the data for a single invoice.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import List, Optional


def _to_date(value) -> Optional[date]:
    """Parse a value into a date. Accepts date/datetime objects or 'YYYY-MM-DD'."""
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d").date()


@dataclass
class Business:
    company: str = ""
    name: str = ""
    abn: str = ""
    address: str = ""
    email: str = ""
    phone: str = ""


@dataclass
class Payment:
    bank_name: str = ""
    account_name: str = ""
    account_number: str = ""
    swift_code: str = ""
    bsb: str = ""
    routing_number: str = ""
    iban: str = ""
    paypal_email: str = ""
    bank_branch_address: str = ""


@dataclass
class BillTo:
    name: str = "Glitch Productions"
    address_lines: List[str] = field(
        default_factory=lambda: ["12/32 Phillip Street", "Parramatta, NSW, 2150", "Australia"]
    )


@dataclass
class Gst:
    registered: bool = False
    rate_percent: float = 10.0


@dataclass
class Preset:
    """Settings for auto-generating a fortnightly period invoice."""

    enabled: bool = True
    state: str = "VIC"                       # Australian state for public holidays
    exclude_weekends: bool = True
    exclude_public_holidays: bool = True
    rate_type: str = "Daily"
    currency: str = "AUD"
    rate: float = 0.0
    period_rate: float = 0.0  # fixed bimonthly total; overrides daily rate for preset invoices
    hours_per_day: float = 1.0
    default_project: str = ""
    default_episode: str = ""
    default_description: str = ""
    invoice_number_prefix: str = "RCS-"
    comments: str = ""


@dataclass
class Config:
    business: Business
    payment: Payment
    bill_to: BillTo
    gst: Gst
    preset: Preset
    output_dir: str = "invoices"

    @classmethod
    def load(cls, path: str) -> "Config":
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
        return cls(
            business=Business(**raw.get("business", {})),
            payment=Payment(**raw.get("payment", {})),
            bill_to=BillTo(**raw.get("bill_to", {})),
            gst=Gst(**raw.get("gst", {})),
            preset=Preset(**raw.get("preset", {})),
            output_dir=raw.get("output_dir", "invoices"),
        )


@dataclass
class LineItem:
    date: Optional[date] = None
    project: str = ""
    episode: str = ""
    description: str = ""
    sick_vacation_hrs: float = 0.0
    hours_worked: float = 0.0
    rate: Optional[float] = None  # falls back to the invoice rate when None

    @classmethod
    def from_dict(cls, data: dict) -> "LineItem":
        raw_rate = data.get("rate")
        return cls(
            date=_to_date(data.get("date")),
            project=str(data.get("project", "")),
            episode=str(data.get("episode", "")),
            description=str(data.get("description", "")),
            sick_vacation_hrs=float(data.get("sick_vacation_hrs", 0) or 0),
            hours_worked=float(data.get("hours_worked", 0) or 0),
            rate=(float(raw_rate) if raw_rate not in (None, "") else None),
        )

    def effective_rate(self, default_rate: float) -> float:
        return self.rate if self.rate is not None else default_rate

    def total(self, default_rate: float) -> float:
        return (self.sick_vacation_hrs + self.hours_worked) * self.effective_rate(default_rate)


@dataclass
class Invoice:
    invoice_number: str
    invoice_date: date
    rate_type: str = "Daily"
    currency: str = "AUD"
    rate: float = 0.0
    work_start_date: Optional[date] = None
    work_end_date: Optional[date] = None
    line_items: List[LineItem] = field(default_factory=list)
    comments: str = ""

    @classmethod
    def load(cls, path: str) -> "Invoice":
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: dict) -> "Invoice":
        items = [LineItem.from_dict(x) for x in raw.get("line_items", [])]
        start = _to_date(raw.get("work_start_date"))

        # Mirror the template behaviour: rows without an explicit date get
        # sequential dates counting up from the work start date.
        for offset, item in enumerate(items):
            if item.date is None and start is not None:
                item.date = start + timedelta(days=offset)

        return cls(
            invoice_number=str(raw.get("invoice_number") or datetime.now().strftime("INV-%Y%m%d")),
            invoice_date=_to_date(raw.get("invoice_date")) or datetime.now().date(),
            rate_type=str(raw.get("rate_type", "Daily")),
            currency=str(raw.get("currency", "AUD")),
            rate=float(raw.get("rate", 0) or 0),
            work_start_date=start,
            work_end_date=_to_date(raw.get("work_end_date")),
            line_items=items,
            comments=str(raw.get("comments", "")),
        )

    def subtotal(self) -> float:
        return sum(item.total(self.rate) for item in self.line_items)

    def total_sick_hours(self) -> float:
        return sum(item.sick_vacation_hrs for item in self.line_items)

    def total_worked_hours(self) -> float:
        return sum(item.hours_worked for item in self.line_items)


# ---------------------------------------------------------------------------
# "Simple" item invoice (e.g. a one-off vendor/artist invoice you receive) --
# a plain item/qty/price/total layout with an optional payment-installment
# badge, rather than the Glitch Productions timesheet template above.
# ---------------------------------------------------------------------------
@dataclass
class Vendor:
    name: str = ""
    email: str = ""


@dataclass
class Installment:
    current: int = 1
    total: int = 1
    label: str = ""  # e.g. "Deposit"

    @property
    def is_multi(self) -> bool:
        return self.total > 1


@dataclass
class SimpleItem:
    description: str = ""
    credit: str = ""  # optional italic credit shown after the description
    qty: float = 1.0
    unit_price: float = 0.0
    total: float = 0.0
    current_due: float = 0.0

    @classmethod
    def from_dict(cls, data: dict) -> "SimpleItem":
        qty = float(data.get("qty", 1) or 1)
        unit_price = float(data.get("unit_price", 0) or 0)
        raw_total = data.get("total")
        total = float(raw_total) if raw_total not in (None, "") else qty * unit_price
        raw_due = data.get("current_due")
        current_due = float(raw_due) if raw_due not in (None, "") else total
        return cls(
            description=str(data.get("description", "")),
            credit=str(data.get("credit", "")),
            qty=qty,
            unit_price=unit_price,
            total=total,
            current_due=current_due,
        )


@dataclass
class SimpleInvoice:
    invoice_number: str
    date_due: Optional[date] = None
    pay_method: str = ""
    payment_link_text: str = "Payment"
    payment_link_url: str = ""
    vendor: Vendor = field(default_factory=Vendor)
    bill_to_name: str = ""
    installment: Installment = field(default_factory=Installment)
    items: List[SimpleItem] = field(default_factory=list)
    currency: str = "USD"
    note: str = ""
    closing: str = "Thank you!"

    @classmethod
    def load(cls, path: str) -> "SimpleInvoice":
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: dict) -> "SimpleInvoice":
        return cls(
            invoice_number=str(raw.get("invoice_number") or datetime.now().strftime("INV-%Y%m%d")),
            date_due=_to_date(raw.get("date_due")),
            pay_method=str(raw.get("pay_method", "")),
            payment_link_text=str(raw.get("payment_link_text", "Payment")),
            payment_link_url=str(raw.get("payment_link_url", "")),
            vendor=Vendor(**raw.get("vendor", {})),
            bill_to_name=str(raw.get("bill_to_name", "")),
            installment=Installment(**raw.get("installment", {})),
            items=[SimpleItem.from_dict(x) for x in raw.get("items", [])],
            currency=str(raw.get("currency", "USD")),
            note=str(raw.get("note", "")),
            closing=str(raw.get("closing", "Thank you!")),
        )

    def amount_due(self) -> float:
        return sum(item.current_due for item in self.items)
