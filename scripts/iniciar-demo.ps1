$ErrorActionPreference = 'Stop'
$appRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $appRoot
$pythonRuntime = Join-Path $appRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonRuntime)) { throw 'Create .venv and install requirements-lock.txt first.' }
& $pythonRuntime 'scripts\preparar_demo.py'
if ($LASTEXITCODE -ne 0) { throw 'Demo preparation failed.' }
& $pythonRuntime 'manage.py' 'runserver' '127.0.0.1:8013' '--noreload'
