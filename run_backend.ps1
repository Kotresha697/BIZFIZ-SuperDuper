<#
Activate virtualenv and start uvicorn with the app module path.
Usage: In PowerShell run `./run_backend.ps1`
#>
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force
. .venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload --port 8000
