# ==============================================================================
# One-click SSH Connect to Colab GPU via Tailscale
# ==============================================================================

$TargetHost = "dervgen-colab-gpu"

Write-Host "🔍 Checking Tailscale status for $TargetHost..." -ForegroundColor Cyan

# 检查本地 Tailscale 客户端状态
$tsStatus = & tailscale status 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error: Tailscale is not running locally. Please launch Tailscale first." -ForegroundColor Red
    exit 1
}

# 查找 Colab 节点信息
$colabNode = $tsStatus | Where-Object { $_ -match $TargetHost }

if ($colabNode) {
    Write-Host "✅ Found Colab node in Tailnet: $colabNode" -ForegroundColor Green
    Write-Host "🚀 Launching SSH session to root@$TargetHost..." -ForegroundColor Yellow
    ssh root@$TargetHost
} else {
    Write-Host "⚠️ Warning: Node '$TargetHost' not found in current Tailnet." -ForegroundColor Yellow
    Write-Host "Current Tailnet nodes:"
    $tsStatus
    Write-Host "`nTrying direct SSH connection anyway..." -ForegroundColor Cyan
    ssh root@$TargetHost
}
