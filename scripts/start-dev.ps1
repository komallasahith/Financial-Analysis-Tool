<#
start-dev.ps1
Helper to pick free local ports and launch backend + frontend on Windows.

Usage: Run from repo root in PowerShell:
  .\scripts\start-dev.ps1

This opens two new PowerShell windows: one runs the Flask backend
and the other runs the React dev server. Ports are chosen automatically.
#>

function Get-FreePort {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
    $listener.Start()
    $endpoint = $listener.LocalEndpoint
    $port = $endpoint.Port
    $listener.Stop()
    return $port
}

Push-Location $PSScriptRoot\.. | Out-Null

# Pick distinct ports for backend and frontend
$backendPort = Get-FreePort
do { $frontendPort = Get-FreePort } while ($frontendPort -eq $backendPort)

Write-Host "Selected ports -> Backend: $backendPort   Frontend: $frontendPort"

# Start backend in a new PowerShell window
$backendCmd = "& { cd '$PWD'; `$env:FLASK_PORT='$backendPort'; `$env:FLASK_HOST='127.0.0.1'; python .\backend\api.py }"
Start-Process -FilePath powershell -ArgumentList '-NoExit','-Command',$backendCmd

# Start frontend in a new PowerShell window
$frontendCmd = "& { cd '$PWD\\frontend'; `$env:PORT='$frontendPort'; `$env:REACT_APP_API_BASE='http://127.0.0.1:$backendPort/api'; npm start }"
Start-Process -FilePath powershell -ArgumentList '-NoExit','-Command',$frontendCmd

Pop-Location | Out-Null

Write-Host "Launched backend and frontend processes."
