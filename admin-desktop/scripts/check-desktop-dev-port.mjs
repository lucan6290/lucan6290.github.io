import { spawnSync } from 'node:child_process'

if (process.platform === 'win32') {
  const result = spawnSync('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', String.raw`
    $ErrorActionPreference = 'Stop'
    $vite = [IO.Path]::GetFullPath((Join-Path (Get-Location) 'node_modules/vite/bin/vite.js'))
    $desktop = Join-Path (Get-Location) 'src-tauri\target\debug\admin-desktop.exe'
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort 14200 -ErrorAction SilentlyContinue)
    $processIds = @($listeners | Select-Object -ExpandProperty OwningProcess -Unique)
    foreach ($processId in $processIds) {
      $owner = Get-CimInstance Win32_Process -Filter "ProcessId=$processId"
      if (-not $owner) { continue }
      $match = [regex]::Match($owner.CommandLine, '(?i)\s+"?([^"\r\n]+?vite\.js)"?(?:\s|$)')
      $script = if ($match.Success) { $match.Groups[1].Value.Trim() } else { '' }
      $isLocalVite = $owner.Name -eq 'node.exe' -and [IO.Path]::IsPathRooted($script) -and [IO.Path]::GetFullPath($script) -ieq $vite
      $parent = Get-CimInstance Win32_Process -Filter "ProcessId=$($owner.ParentProcessId)"
      $orphan = -not $parent -or $parent.CreationDate -gt $owner.CreationDate
      $runningDesktop = Get-Process -Name admin-desktop -ErrorAction SilentlyContinue | Where-Object { $_.Path -ieq $desktop }
      if ($processIds.Count -ne 1 -or -not $isLocalVite -or -not $orphan -or $runningDesktop) {
        [Console]::Error.WriteLine("14200 is in use by $($owner.Name) (PID $processId). If this is your old Vite session, stop it with Ctrl+C in its terminal and retry.")
        exit 1
      }
      $live = Get-CimInstance Win32_Process -Filter "ProcessId=$processId"
      if (-not $live -or $live.CreationDate -ne $owner.CreationDate) { continue }
      $stillListening = Get-NetTCPConnection -State Listen -LocalPort 14200 -OwningProcess $processId -ErrorAction SilentlyContinue
      if (-not $stillListening) { continue }
      $viteProcess = Get-Process -Id $processId -ErrorAction SilentlyContinue
      if (-not $viteProcess -or [Math]::Abs(($viteProcess.StartTime - $live.CreationDate).TotalMilliseconds) -gt 1) { continue }
      Stop-Process -InputObject $viteProcess
      Wait-Process -InputObject $viteProcess -Timeout 5 -ErrorAction SilentlyContinue
      Write-Output "Stopped orphaned desktop Vite process $processId on port 14200."
    }
  `], { stdio: 'inherit', windowsHide: true })
  if (result.error) throw result.error
  process.exitCode = result.status ?? 1
}
