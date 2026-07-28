#!/bin/sh
# Build Ashwin_Iyer_CV.pdf and verify it stays one page with no overfull lines.
# Usage: ./build.sh
set -e
cd "$(dirname "$0")"

latexmk -lualatex -g -interaction=nonstopmode Ashwin_Iyer_CV.tex

failed=0

pages=$(sed -n 's/.*Output written on .*(\([0-9]*\) page.*/\1/p' Ashwin_Iyer_CV.log | tail -1)
echo "Built Ashwin_Iyer_CV.pdf (${pages} page(s))"
if [ "$pages" != "1" ]; then
    echo "WARNING: resume is ${pages} pages - it must fit on ONE page. Trim content." >&2
    failed=1
fi

overfull=$(grep -c "Overfull" Ashwin_Iyer_CV.log || true)
if [ "$overfull" -gt 0 ]; then
    echo "WARNING: ${overfull} overfull line(s) poke past the margin - search 'Overfull' in Ashwin_Iyer_CV.log." >&2
    failed=1
else
    echo "No overfull lines."
fi

exit $failed
