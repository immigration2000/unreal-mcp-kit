#!/usr/bin/env bash
# unreal-mcp-kit — macOS/Linux 설치 스크립트
# 두 스킬을 ~/.claude/skills 로 복사 (플러그인 방식 대신 직접 설치)
# 사용: 리포 루트에서  ->  bash install.sh
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)/plugins/unreal-mcp-kit/skills"
DST="$HOME/.claude/skills"

[ -d "$SRC" ] || { echo "skills 폴더를 못 찾음: $SRC"; exit 1; }
mkdir -p "$DST"

for skill in ue5-8-mcp setup-ue58-mcp; do
  rm -rf "$DST/$skill"
  cp -R "$SRC/$skill" "$DST/$skill"
  echo "설치됨: $DST/$skill"
done

echo
echo "완료. Claude Code 재시작(또는 /reload-plugins) 후:"
echo "  UE 프로젝트 폴더에서 Claude Code 열고 -> '이 프로젝트 UE MCP 셋업해줘'"
