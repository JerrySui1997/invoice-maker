"""Shared constants: colours, column layout, and reference lists.

Colours and column widths are taken directly from the original
Glitch Productions "INVOICE TEMPLATE" spreadsheet so the generated
PDF matches its look.
"""

from reportlab.lib.colors import HexColor, white, black

# Colours pulled from the template's cell fills.
HEADER_BLUE = HexColor("#92CDDC")  # section header / label fill
LIGHT_BLUE = HexColor("#B6DDE8")   # "From" label fill
DARK = HexColor("#262626")         # dark bars (DAY/DATE/Rate/Daily Total/Grand Total)
WHITE = white
BLACK = black

# Column widths (points) mapped proportionally from template columns A..I.
# Sum ~= 539pt to fit an A4 page with 28pt side margins.
COL_WIDTHS = [61.2, 51.9, 37.9, 34.2, 136.4, 41.5, 50.8, 48.8, 76.2]

# Reference lists from the template's hidden "DO NOT SHARE" section.
CURRENCIES = ["AUD", "USD", "CAD", "PHP", "GBP", "EUR"]
RATE_TYPES = ["Hourly", "Daily", "By Piece"]
PROJECTS = ["GOV", "KOG", "DC", "GD", "LD", "PP", "Marketing"]

# Symbol shown alongside the currency code on the "simple" item-invoice template.
CURRENCY_SYMBOLS = {"USD": "$", "AUD": "$", "CAD": "$", "EUR": "€", "GBP": "£", "PHP": "₱"}

# Column widths (points) for the "simple" item-invoice template. Sums to the
# usable A4 width with 40pt side margins (595.27 - 80 = 515.27).
SIMPLE_COL_WIDTHS = [255, 55, 70, 70, 65]
SIMPLE_LINK_COLOR = HexColor("#1a7f8e")
SIMPLE_BOX_GREY = HexColor("#e9e9e9")
