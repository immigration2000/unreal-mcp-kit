# unreal-mcp-kit — Windows 설치 스크립트
# 두 스킬을 ~/.claude/skills 로 복사 (플러그인 방식 대신 직접 설치)
# 사용: 리포 루트에서  ->  powershell -ExecutionPolicy Bypass -File .\install.ps1

$ErrorActionPreference = "Stop"
$src = Join-Path $PSScriptRoot "plugins\unreal-mcp-kit\skills"
$dst = Join-Path $env:USERPROFILE ".claude\skills"

if (-not (Test-Path $src)) { Write-Error "skills 폴더를 못 찾음: $src"; exit 1 }
New-Item -ItemType Directory -Force -Path $dst | Out-Null

foreach ($skill in @("ue5-8-mcp", "setup-ue58-mcp")) {
    $from = Join-Path $src $skill
    $to   = Join-Path $dst $skill
    if (Test-Path $to) { Remove-Item -Recurse -Force $to }
    Copy-Item -Recurse -Force $from $to
    Write-Host "설치됨: $to"
}

Write-Host ""
Write-Host "완료. Claude Code 재시작(또는 /reload-plugins) 후:"
Write-Host "  UE 프로젝트 폴더에서 Claude Code 열고 -> '이 프로젝트 UE MCP 셋업해줘'"
