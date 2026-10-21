# Automatic Invoice Maker

Generates PDF invoices from a pluggable set of **templates**. Your
business details (including your ABN **18 504 904 415**) live in
`config.json` and are reused for every invoice — you only supply the
per-invoice data (dates, line items, etc.).

Two templates ship today:

- **`glitch`** (default) — the Glitch Productions contractor timesheet
  invoice: a day-by-day grid with rate/dates, payment details, and
  totals. Used for `--preset`, `--new`, and any data file that doesn't
  set a `"template"` field.
- **`simple`** — a plain item/qty/price/total invoice (an "invoice"
  wordmark, invoice #/date due/pay method, an item table, an amount-due
  box, and a vendor/bill-to footer), for one-off invoices *you receive*
  from a vendor or artist. See `data/example_simple_invoice.json`.

Pick a template by setting `"template": "glitch"` or `"template":
"simple"` in the data JSON, or override it with `--template` on the
command line. Adding a new invoice style means adding one module under
`invoice_maker/templates/` and registering it in
`invoice_maker/templates/__init__.py` — the CLI and renderer don't
need to change.

## Setup

```powershell
cd invoice-maker
pip install -r requirements.txt
```

## 1. Fill in your details once

Edit [`config.json`](config.json):

- `business` – your name, ABN (already set), address, email, phone.
- `payment` – bank name, account, Swift/BSB/Routing/IBAN, PayPal, branch address.
- `bill_to` – already set to Glitch Productions (change if needed).
- `gst.registered` – set to `true` only if you are registered for GST.
  When `true`, the heading becomes **TAX INVOICE** and a GST line is added.

## 2. Make an invoice

**From a data file** (copy `data/example_invoice.json` and edit it):

```powershell
python make_invoice.py data/example_invoice.json
```

**Interactive wizard** (prompts you for each field, also saves a reusable
JSON in `data/`):

```powershell
python make_invoice.py --new
```

The finished PDF is written to the `invoices/` folder, e.g.
`invoices/INVOICE_0001_YOUR_NAME.pdf`.

## Automatic fortnightly invoices (preset)

The `preset` block in `config.json` lets the tool build a whole period
invoice by itself:

- **1st–15th** of the month, and **16th–end of month** (two invoices/month).
- One line item per **working day**, automatically **skipping weekends and
  Australian public holidays** for your state (`VIC`). Holidays are computed
  fresh for whatever year the period is in, so it keeps working every year.

Generate the invoice for the current period:

```powershell
python make_invoice.py --preset
```

The period is chosen from today's date: on/before the 15th it bills the
1st–15th; after the 15th it bills the 16th–end of month. To test another
date use `--as-of`:

```powershell
python make_invoice.py --preset --as-of 2026-12-31
```

Invoice numbers are auto-generated like `RCS-202612-2` (prefix + year +
month + half). **Set your day rate** in `config.json` (`preset.rate`) —
it starts at `0`.

### Run it automatically on the 15th and last day of the month

A one-time setup registers two Windows scheduled tasks:

```powershell
.\schedule_tasks.ps1
```

This creates:

- **RubyCube Invoice - 15th** — runs on the 15th (bills 1st–15th).
- **RubyCube Invoice - Last Day** — runs on the last day (bills 16th–EOM).

Both run at 09:00 and call `run_preset.ps1`. Change the time with
`-Time "07:30"`, or remove the tasks with `.\schedule_tasks.ps1 -Remove`.

## Fields reference

### Preset (`config.json` → `preset`)

| Field | Meaning |
|-------|---------|
| `state` | Australian state for public holidays (`VIC`, `NSW`, ...) |
| `exclude_weekends` | Skip Sat/Sun when building days |
| `exclude_public_holidays` | Skip public holidays for `state` |
| `rate_type` / `currency` / `rate` | Defaults for the generated invoice |
| `hours_per_day` | Units billed per working day (1 for a daily rate) |
| `default_project` / `default_episode` / `default_description` | Filled into each row |
| `invoice_number_prefix` | Prefix for the auto invoice number |

### `glitch` template invoice data

| Field | Meaning |
|-------|---------|
| `invoice_number` | Your invoice number |
| `invoice_date` | `YYYY-MM-DD` |
| `rate_type` | `Hourly`, `Daily`, or `By Piece` |
| `currency` | `AUD`, `USD`, `CAD`, `PHP`, `GBP`, `EUR` |
| `rate` | Default rate applied to each line item |
| `work_start_date` / `work_end_date` | `YYYY-MM-DD` |
| `line_items[]` | One row per day/task (see below) |
| `comments` | Notes for accounting/production |

Each line item:

| Field | Meaning |
|-------|---------|
| `date` | `YYYY-MM-DD` (blank = auto from work start date) |
| `project` | `GOV`, `KOG`, `DC`, `GD`, `LD`, `PP`, `Marketing` |
| `episode` | Episode number |
| `description` | Task / description |
| `sick_vacation_hrs` | Sick / vacation hours |
| `hours_worked` | Days / hours worked |
| `rate` | Optional; overrides the invoice-wide `rate` |

**Daily Total** = (`sick_vacation_hrs` + `hours_worked`) × `rate`.
The Grand Total and hour totals are calculated automatically.

### `simple` template invoice data

```powershell
python make_invoice.py data/example_simple_invoice.json
```

| Field | Meaning |
|-------|---------|
| `template` | Must be `"simple"` to use this layout |
| `vendor.name` / `vendor.email` | Who the invoice is from (shown bottom-left) |
| `invoice_number` | The vendor's invoice number |
| `date_due` | `YYYY-MM-DD` |
| `pay_method` | Free text, e.g. `"ACH / Wire / CC"` |
| `payment_link_text` / `payment_link_url` | Optional "Payment" link top-right; omit `payment_link_url` to show plain (non-clickable) text |
| `installment.current` / `.total` / `.label` | Optional installment badge (e.g. "Installment 1 of 4 (Deposit)"); hidden when `total` is `1` |
| `items[]` | One row per line item (see below) |
| `currency` | `USD`, `AUD`, `CAD`, `EUR`, `GBP`, `PHP` |
| `note` | Footer note (e.g. terms-of-service reference) |
| `closing` | Bold closing line, e.g. `"Thank you!"` |
| `bill_to_name` | Optional; defaults to `business.name` from `config.json` |

Each item:

| Field | Meaning |
|-------|---------|
| `description` | Bold item name |
| `credit` | Optional italic credit shown after the description (e.g. an artist name) |
| `qty` | Quantity |
| `unit_price` | Price per unit |
| `total` | Optional; defaults to `qty × unit_price` |
| `current_due` | Optional; defaults to `total` (use a smaller value for a partial/installment payment) |

**Amount Due** = the sum of every item's `current_due`.
