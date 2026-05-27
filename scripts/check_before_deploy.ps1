param(
    [switch]$SkipFrontendBuild,
    [switch]$SkipDocker
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RepoRoot "backend"
$FrontendDir = Join-Path $RepoRoot "frontend"

function Write-Step {
    param([string]$Message)
    Write-Host "`n[MISSIO CHECK] $Message" -ForegroundColor Cyan
}

function Fail {
    param([string]$Message)
    Write-Host "`n[FAIL] $Message" -ForegroundColor Red
    exit 1
}

function Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Ok {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

Write-Step "Firebase/FCM aktif kalıntı kontrolü"

$ForbiddenChecks = @(
    @{ Path = "backend/requirements.txt"; Pattern = "firebase-admin"; Label = "backend requirements içinde firebase-admin" },
    @{ Path = "frontend/package.json"; Pattern = '"firebase"'; Label = "frontend package.json içinde firebase paketi" },
    @{ Path = "frontend/src"; Pattern = "firebase/messaging"; Label = "frontend src içinde Firebase Messaging importu" },
    @{ Path = "frontend/public"; Pattern = "firebase-app-compat"; Label = "frontend public içinde Firebase service worker importu" }
)

foreach ($Check in $ForbiddenChecks) {
    $TargetPath = Join-Path $RepoRoot $Check.Path
    if (-not (Test-Path $TargetPath)) {
        continue
    }

    if ((Get-Item $TargetPath) -is [System.IO.DirectoryInfo]) {
        $SearchFiles = Get-ChildItem -Path $TargetPath -File -Recurse
    } else {
        $SearchFiles = @(Get-Item $TargetPath)
    }

    $Match = $SearchFiles | Select-String -Pattern $Check.Pattern -SimpleMatch -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($Match) {
        Fail "$($Check.Label) bulundu: $($Match.Path):$($Match.LineNumber)"
    }
}

Ok "Aktif Firebase/FCM bağımlılığı görünmüyor."

Write-Step "Backend Python syntax kontrolü"
Push-Location $BackendDir
try {
    python -m compileall app | Out-Host
    if ($LASTEXITCODE -ne 0) {
        Fail "Backend compileall başarısız."
    }
    Ok "Backend Python dosyaları derlenebiliyor."
}
finally {
    Pop-Location
}

Write-Step "Production/live güvenlik kapısı kontrolü"
Push-Location $BackendDir
try {
    $SecurityCheckScript = @'
from app.core.production_safety import validate_production_settings

class Settings:
    environment = "live"
    debug = True
    secret_key = "change-this-secret-key-before-production"
    database_url = "sqlite:///./missio_local.db"
    default_timezone = "Asia/Nicosia"
    cors_allowed_origins = "http://localhost:5175"

try:
    validate_production_settings(Settings())
except RuntimeError:
    print("live ortamı production güvenlik kapısına takılıyor: OK")
else:
    raise SystemExit("live ortamı production güvenlik kapısına takılmadı: FAIL")
'@
    $SecurityCheckScript | python -
    if ($LASTEXITCODE -ne 0) {
        Fail "Production/live güvenlik kapısı kontrolü başarısız."
    }
    Ok "live ortamı production kabul ediliyor."
}
finally {
    Pop-Location
}

if (-not $SkipFrontendBuild) {
    Write-Step "Frontend production build kontrolü"
    Push-Location $FrontendDir
    try {
        if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
            Write-Host "node_modules bulunamadı; npm ci çalıştırılıyor..." -ForegroundColor Yellow
            npm ci | Out-Host
            if ($LASTEXITCODE -ne 0) {
                Fail "npm ci başarısız."
            }
        }

        npm run build | Out-Host
        if ($LASTEXITCODE -ne 0) {
            Fail "Frontend build başarısız."
        }
        Ok "Frontend build başarılı."
    }
    finally {
        Pop-Location
    }
} else {
    Warn "Frontend build kontrolü atlandı."
}

if (-not $SkipDocker) {
    Write-Step "Docker image build kontrolü"

    $DockerCommand = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $DockerCommand) {
        Fail "Docker bulunamadı. Docker kontrolünü atlamak için -SkipDocker kullanabilirsin."
    }

    Push-Location $BackendDir
    try {
        docker build -t missio-backend:p0-check . | Out-Host
        if ($LASTEXITCODE -ne 0) {
            Fail "Backend Docker build başarısız."
        }
        Ok "Backend Docker image build başarılı."
    }
    finally {
        Pop-Location
    }

    Push-Location $FrontendDir
    try {
        docker build -t missio-frontend:p0-check . | Out-Host
        if ($LASTEXITCODE -ne 0) {
            Fail "Frontend Docker build başarısız."
        }
        Ok "Frontend Docker image build başarılı."
    }
    finally {
        Pop-Location
    }
} else {
    Warn "Docker build kontrolü atlandı."
}

Write-Host "`n[SUCCESS] Missio deploy öncesi lokal kontrol tamamlandı." -ForegroundColor Green
