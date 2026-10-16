# Ejecutar desde PowerShell con dot-sourcing para conservar la activación:
# . .\scripts\activar_windows.ps1
$raiz = Split-Path -Parent $PSScriptRoot
& "$raiz\.venv\Scripts\Activate.ps1"
