"""Command-line interface for the invoice maker."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime

from .constants import CURRENCIES, PROJECTS, RATE_TYPES
from .models import Config, Invoice
from .preset import build_preset_invoice
from .render import invoice_filename, render_invoice
from .templates import get_template


def _generate(template_name: str, config: Config, invoice, out_arg: str = None) -> str:
    os.makedirs(config.output_dir, exist_ok=True)
    output = out_arg or os.path.join(config.output_dir, invoice_filename(template_name, config, invoice))
    render_invoice(template_name, config, invoice, output)
    return output


def _ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    answer = input(f"{prompt}{suffix}: ").strip()
    return answer or default


def _wizard(config: Config) -> Invoice:
    print("\nCreate a new invoice (press Enter to accept defaults)\n" + "-" * 45)
    number = _ask("Invoice number", datetime.now().strftime("%Y%m%d"))
    inv_date = _ask("Invoice date (YYYY-MM-DD)", datetime.now().strftime("%Y-%m-%d"))
    print(f"Rate types: {', '.join(RATE_TYPES)}")
    rate_type = _ask("Rate type", "Daily")
    print(f"Currencies: {', '.join(CURRENCIES)}")
    currency = _ask("Currency", "AUD")
    rate = float(_ask("Default rate (number)", "0") or 0)
    work_start = _ask("Work start date (YYYY-MM-DD)", "")
    work_end = _ask("Work end date (YYYY-MM-DD)", "")

    print(f"\nAdd line items. Projects: {', '.join(PROJECTS)}")
    print("Leave 'Description' empty to finish.\n")
    items = []
    while True:
        description = _ask("  Task / Description", "")
        if not description:
            break
        item = {
            "date": _ask("  Date (YYYY-MM-DD, blank = auto)", ""),
            "project": _ask("  Project", ""),
            "episode": _ask("  Ep #", ""),
            "description": description,
            "sick_vacation_hrs": float(_ask("  Sick/Vacation hrs", "0") or 0),
            "hours_worked": float(_ask("  Day/Hours worked", "1") or 0),
        }
        item_rate = _ask("  Rate (blank = default)", "")
        if item_rate:
            item["rate"] = float(item_rate)
        items.append(item)
        print("  ---")

    comments = _ask("\nAdditional comments", "")

    raw = {
        "invoice_number": number,
        "invoice_date": inv_date,
        "rate_type": rate_type,
        "currency": currency,
        "rate": rate,
        "work_start_date": work_start,
        "work_end_date": work_end,
        "comments": comments,
        "line_items": items,
    }

    # Save the data so it can be reused / edited later.
    os.makedirs("data", exist_ok=True)
    data_path = os.path.join("data", f"invoice_{number}.json")
    with open(data_path, "w", encoding="utf-8") as handle:
        json.dump(raw, handle, indent=2)
    print(f"\nSaved invoice data to {data_path}")

    return Invoice.from_dict(raw)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        description="Automatic invoice maker (pluggable invoice templates)."
    )
    parser.add_argument("data", nargs="?", help="Path to an invoice data JSON file.")
    parser.add_argument("--config", default="config.json", help="Path to config.json.")
    parser.add_argument(
        "--template",
        help="Invoice template to use (overrides the data file's \"template\" field). "
        "Defaults to 'glitch'.",
    )
    parser.add_argument("--new", action="store_true", help="Interactively create a new invoice.")
    parser.add_argument(
        "--preset",
        action="store_true",
        help="Auto-generate the current period invoice (1st-15th or 16th-EOM), "
        "excluding weekends and public holidays.",
    )
    parser.add_argument(
        "--as-of",
        metavar="YYYY-MM-DD",
        help="Pretend today is this date (for --preset). Defaults to today.",
    )
    parser.add_argument(
        "--start",
        metavar="YYYY-MM-DD",
        help="Override the period start date (for --preset), e.g. a mid-period start.",
    )
    parser.add_argument(
        "--end",
        metavar="YYYY-MM-DD",
        help="Override the period end date (for --preset).",
    )
    parser.add_argument("--out", help="Explicit output PDF path.")
    args = parser.parse_args(argv)

    config = Config.load(args.config)

    if args.preset:
        as_of = datetime.strptime(args.as_of, "%Y-%m-%d").date() if args.as_of else None
        start_override = datetime.strptime(args.start, "%Y-%m-%d").date() if args.start else None
        end_override = datetime.strptime(args.end, "%Y-%m-%d").date() if args.end else None
        if as_of is None and start_override:
            as_of = start_override
        invoice = build_preset_invoice(config, as_of, start_override, end_override)
        if config.preset.rate in (0, 0.0):
            print("WARNING: preset.rate is 0 in config.json - set your day rate before invoicing.")
        if not invoice.line_items:
            print("WARNING: no working days in this period (all weekends/holidays?).")
        output = _generate(args.template or "glitch", config, invoice, args.out)
    elif args.new:
        invoice = _wizard(config)
        output = _generate(args.template or "glitch", config, invoice, args.out)
    elif args.data:
        with open(args.data, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
        template_name = args.template or raw.get("template", "glitch")
        spec = get_template(template_name)
        invoice = spec.data_model.from_dict(raw)
        output = _generate(template_name, config, invoice, args.out)
    else:
        parser.error("Provide an invoice data JSON path, or use --new / --preset.")
        return

    print(f"Created invoice PDF: {output}")


if __name__ == "__main__":
    main()
