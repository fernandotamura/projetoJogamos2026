Set-ExecutionPolicy RemoteSigned -Scope CurrentUser@'
param(
  [switch]$BackendOnly = $false,
  [switch]$FrontendOnly = $false,
  [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

function Write-Section($msg) {
  Write-Host ""
  Write-Host "=== $msg ===" -ForegroundColor Cyan
}

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Ensure-File($Path, $Content) {
  if (-not (Test-Path $Path)) {
    $Content | Out-File -FilePath $Path -Encoding utf8
    Write-Host "Criado: $Path"
  } else {
    Write-Host "Já existe: $Path"
  }
}

Write-Section "Checando venv"
if (-not (Test-Path "$Root\venv")) {
  Write-Host "Criando venv..."
  try { py -3 -m venv venv } catch { python -m venv venv }
} else {
  Write-Host "venv já existe."
}

$Python = Join-Path $Root "venv\Scripts\python.exe"
$Pip    = Join-Path $Root "venv\Scripts\pip.exe"

Write-Section "Atualizando pip/setuptools/wheel"
& $Python -m pip install --upgrade pip setuptools wheel

Write-Section "Garantindo requirements"
$BackendReq = @'
fastapi==0.115.5
uvicorn[standard]==0.30.6
pydantic[email]==2.8.2
pyjwt[crypto]==2.9.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.12
'@
Ensure-File -Path "$Root\requirements.txt" -Content $BackendReq

$FrontendReq = @'
kivy[base]
kivymd==1.2.0
httpx==0.27.2
keyring
watchdog
'@
Ensure-File -Path "$Root\requirements-frontend.txt" -Content $FrontendReq

if (-not $FrontendOnly) {
  Write-Section "Instalando dependências do backend"
  & $Pip install -r "$Root\requirements.txt"
}

if (-not $BackendOnly) {
  Write-Section "Instalando dependências do frontend"
  & $Pip install -r "$Root\requirements-frontend.txt"
}

if (-not $FrontendOnly) {
  Write-Section "Subindo backend (Uvicorn) em http://127.0.0.1:$Port"
  Start-Process -FilePath $Python -ArgumentList "-m","uvicorn","server:app","--reload","--host","127.0.0.1","--port",$Port `
    -WorkingDirectory $Root -WindowStyle Normal
}

if (-not $BackendOnly) {
  if (Test-Path "$Root\main.py") {
    Write-Section "Iniciando frontend (KivyMD)"
    Start-Process -FilePath $Python -ArgumentList "main.py" -WorkingDirectory $Root -WindowStyle Normal
  } else {
    Write-Host "Aviso: main.py não encontrado; pulei o frontend."
  }
}

Write-Host ""
Write-Host "Tudo pronto! Para encerrar, feche as janelas abertas ou use CTRL+C nelas." -ForegroundColor Green
'@ | Out-File -FilePath dev.ps1 -Encoding utf8
