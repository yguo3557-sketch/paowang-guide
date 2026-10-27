#!/usr/bin/env bash
# 炮王识别指南 · 一键安装脚本（默认装到 Codex）
# 用法：
#   bash install.sh                 # 装到 ~/.codex/skills（默认）
#   bash install.sh --claude        # 装到 ~/.claude/skills
#   bash install.sh --dir ~/my-skills
#   bash install.sh --only paowang-detector
#   curl -fsSL <raw链接>/install.sh | bash

set -e

REPO="https://github.com/yguo3557-sketch/paowang-guide.git"
ALL_SKILLS=("paowang-detector")

TARGET=""
SELECTED=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --codex) TARGET="$HOME/.codex/skills"; shift ;;
    --claude) TARGET="$HOME/.claude/skills"; shift ;;
    --dir) TARGET="$2"; shift 2 ;;
    --only) SELECTED="$2"; shift 2 ;;
    -h|--help)
      echo "用法: bash install.sh [--codex|--claude|--dir <路径>] [--only <skill名>]"
      exit 0 ;;
    *) echo "未知参数: $1"; exit 1 ;;
  esac
done

# 默认：Codex
TARGET="${TARGET:-$HOME/.codex/skills}"

if [[ -n "$SELECTED" ]]; then
  IFS=',' read -ra LIST <<< "$SELECTED"
else
  LIST=("${ALL_SKILLS[@]}")
fi

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

echo "→ 拉取仓库..."
git clone --depth 1 "$REPO" "$TMP/repo" >/dev/null 2>&1

mkdir -p "$TARGET"
echo "→ 安装到 $TARGET"

for s in "${LIST[@]}"; do
  s=$(echo "$s" | xargs)
  if [[ -d "$TMP/repo/$s" ]]; then
    rm -rf "$TARGET/$s"
    cp -r "$TMP/repo/$s" "$TARGET/$s"
    echo "  ✓ $s"
  else
    echo "  ✗ 找不到 $s（可选：${ALL_SKILLS[*]}）"
  fi
done

echo ""
echo "安装完成。可用 skill："
ls -1 "$TARGET" | grep -E "paowang-detector" | sed 's/^/  · /'
