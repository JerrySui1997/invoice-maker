# Runs the preset invoice for the current period.
# Called automatically by the scheduled tasks on the 15th and last day of the month.
Set-Location -Path $PSScriptRoot
python make_invoice.py --preset
