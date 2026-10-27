# 炮王识别指南 · 一键安装脚本（Windows，默认装到 Codex）
# 用法（PowerShell）：
#   .\install.ps1                       # 装到 ~/.codex/skills（默认）
#   .\install.ps1 -Claude               # 装到 ~/.claude/skills
#   .\install.ps1 -Dir "D:\my-skills"

param(
    [switch]$Codex,
    [switch]$Claude,
    [string]$Dir
)

$Repo = "https://github.com/yguo3557-sketch/paowang-guide.git"

if ($Claude) {
    $Target = Join-Path $HOME ".claude\skills"
} elseif ($Dir) {
    $Target = $Dir
} else {
    # 默认：Codex
    $Target = Join-Path $HOME ".codex\skills"
}

$Tmp = Join-Path $env:TEMP ("pwguide_" + [guid]::NewGuid().ToString("N").Substring(0, 8))

Write-Host "→ 拉取仓库..." -ForegroundColor Cyan
git clone --depth 1 $Repo $Tmp 2>$null

if (-not (Test-Path $Tmp)) {
    Write-Host "克隆失败，请确认已安装 git 且能访问 GitHub" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $Target)) { New-Item -ItemType Directory -Path $Target -Force | Out-Null }
Write-Host "→ 安装到 $Target" -ForegroundColor Cyan

$dst = Join-Path $Target "paowang-detector"
if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
Copy-Item (Join-Path $Tmp "paowang-detector") $dst -Recurse -Force
Write-Host "  ✓ paowang-detector" -ForegroundColor Green

Remove-Item $Tmp -Recurse -Force

Write-Host ""
Write-Host "安装完成。" -ForegroundColor Green
