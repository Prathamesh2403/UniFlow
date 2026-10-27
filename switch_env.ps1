# ═══════════════════════════════════════════════════════════════
# switch_env.ps1 — Quickly swap between local and production .env
# Usage:
#   .\switch_env.ps1 local       → Docker MongoDB + Redis (localhost)
#   .\switch_env.ps1 production  → Atlas + Upstash + Cloudinary
# ═══════════════════════════════════════════════════════════════

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("local", "production")]
    [string]$Target
)

$envDir = Join-Path $PSScriptRoot "backend"
$targetFile = Join-Path $envDir ".env.$Target"
$destFile   = Join-Path $envDir ".env"

if (-not (Test-Path $targetFile)) {
    Write-Error "Could not find $targetFile"
    exit 1
}

Copy-Item -Path $targetFile -Destination $destFile -Force

Write-Host ""
Write-Host "  ✅ Switched to [ $Target ] environment" -ForegroundColor Green
Write-Host ""

# Show what changed
$mongo  = (Select-String "^MONGO_URI="  $destFile).Line -replace "MONGO_URI=",""
$redis  = (Select-String "^REDIS_URL="  $destFile).Line -replace "REDIS_URL=",""

Write-Host "  MONGO_URI  → $mongo"  -ForegroundColor Cyan
Write-Host "  REDIS_URL  → $redis"  -ForegroundColor Cyan
Write-Host ""

if ($Target -eq "local") {
    Write-Host "  💡 Make sure Docker is running: docker-compose up -d mongodb redis" -ForegroundColor Yellow
} else {
    Write-Host "  💡 Production: Atlas + Upstash + Cloudinary" -ForegroundColor Yellow
}
Write-Host ""
