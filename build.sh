#!/usr/bin/env bash
# Собирает книгу из глав в ru/ в форматы DOCX, EPUB и FB2 (нужен pandoc).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build
PANDOC="${PANDOC:-pandoc}"
CHAPTERS=(ru/*.md)
common=(metadata.yaml "${CHAPTERS[@]}" --top-level-division=chapter)
"$PANDOC" "${common[@]}" -o build/v-predelah-dopuska.docx
"$PANDOC" "${common[@]}" --toc --toc-depth=1 -o build/v-predelah-dopuska.epub
"$PANDOC" "${common[@]}" -o build/v-predelah-dopuska.fb2
ls -la build
