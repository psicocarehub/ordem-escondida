#!/usr/bin/env bash
# Gera o PDF de um relatório (pandoc + tectonic, mesmas fontes do Polar Sentinel).
# Uso: bash gerar_pdf.sh [relatorio|report-en]   (padrão: relatorio)
set -euo pipefail
cd "$(dirname "$0")"
NOME="${1:-relatorio}"
LINGUA=$([ "$NOME" = "report-en" ] && echo en-US || echo pt-BR)
pandoc "$NOME.md" -f markdown-implicit_figures --standalone --pdf-engine=xelatex \
  -V documentclass=article -V fontsize=11pt -V geometry:margin=1in -V linkcolor=blue -V urlcolor=blue -V lang="$LINGUA" \
  -V mainfont=texgyrepagella -V mainfontoptions="Extension=.otf,UprightFont=*-regular,BoldFont=*-bold,ItalicFont=*-italic,BoldItalicFont=*-bolditalic" \
  -V mathfont=texgyrepagella-math.otf -V monofont=DejaVuSansMono.ttf -V monofontoptions="Scale=0.84" \
  -V header-includes="\\usepackage{xurl}" -o "$NOME.tex"
tectonic --keep-logs "$NOME.tex" >/dev/null 2>tectonic.err || { cat tectonic.err; exit 1; }
grep -E "Missing character|Overfull" "$NOME.log" | sort | uniq -c | sort -rn | head || true
rm -f "$NOME.tex" "$NOME.log" tectonic.err
echo "$(pwd)/$NOME.pdf"
