param([Parameter(Mandatory=$true)][string]$Project)
# Run on Windows with the installed HEC-RAS 6.6 COM controller.
# Preserve its messages; computation success does not validate the hydraulics.
$ErrorActionPreference = 'Stop'
$path = (Resolve-Path $Project).Path
if ([IO.Path]::GetExtension($path) -ne '.prj') { throw 'Select one exported .prj file.' }
$ras = $null
try {
  $ras = New-Object -ComObject RAS66.HECRASController
  $ras.Project_Open($path)
  [int]$count = 0
  [System.Array]$messages = @()
  $ok = $ras.Compute_CurrentPlan([ref]$count, [ref]$messages, $true)
  $record = [ordered]@{
    intended_version = '6.6'; controller = 'RAS66.HECRASController'
    project = [IO.Path]::GetFileName($path); engine_returned_success = [bool]$ok
    message_count = $count; messages = @($messages)
    timestamp_utc = [DateTime]::UtcNow.ToString('o')
    note = 'Retain native outputs and verify hydraulic settings in the GUI. This is not a water-surface accuracy certificate.'
  }
  $record | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path ([IO.Path]::GetDirectoryName($path)) 'hec66_compute.json')
  if (!$ok) { throw 'HEC-RAS did not report success. See hec66_compute.json and the native calculation log.' }
  Write-Host 'HEC-RAS calculation completed. Export SI profile values and preserve the calculation log.'
} finally {
  if ($null -ne $ras) {
    try { $ras.QuitRas() } catch { Write-Warning 'Close the HEC-RAS window manually if it remains open.' }
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($ras)
  }
}
