# Registers two Windows scheduled tasks that auto-generate your invoices:
#   * "RubyCube Invoice - 15th"      runs on the 15th of every month (1st-15th period)
#   * "RubyCube Invoice - Last Day"  runs on the last day of every month (16th-EOM period)
#
# Run this ONCE from PowerShell (in this folder):
#   .\schedule_tasks.ps1
# Tasks run at 09:00. To remove them later, run:  .\schedule_tasks.ps1 -Remove

param(
    [string]$Time = "09:00",
    [switch]$Remove
)

$dir = $PSScriptRoot
$script = Join-Path $dir "run_preset.ps1"
$runner = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$script`""

$task15 = "RubyCube Invoice - 15th"
$taskEnd = "RubyCube Invoice - Last Day"

if ($Remove) {
    schtasks /Delete /TN $task15 /F
    schtasks /Delete /TN $taskEnd /F
    Write-Host "Removed scheduled invoice tasks."
    return
}

# 15th of every month
schtasks /Create /TN $task15 /SC MONTHLY /D 15 /ST $Time /TR $runner /F

# Last day of every month (all months)
schtasks /Create /TN $taskEnd /SC MONTHLY /MO LASTDAY /M "*" /ST $Time /TR $runner /F

Write-Host ""
Write-Host "Scheduled tasks created. They will run at $Time on the 15th and last day of each month."
Write-Host "Check them in Task Scheduler, or run:  schtasks /Query /TN `"$task15`""
