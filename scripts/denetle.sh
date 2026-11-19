#!/usr/bin/env bash
# Tek denetim komutu: testler, eklenti doğrulaması, sayfa üretimi, dosya boyutu.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m unittest discover -s testler -q
claude plugin validate . >/dev/null && claude plugin validate eklenti >/dev/null && echo "eklenti ve pazar yeri geçerli"
python3 egitim/uret.py
asim=0
while IFS= read -r dosya; do
  satir=$(wc -l < "$dosya"); sinir=400
  case "$dosya" in testler/test_*) sinir=600 ;; esac
  if [ "$satir" -gt "$sinir" ]; then echo "$dosya: $satir satır (sınır $sinir)"; asim=1; fi
done < <(find eklenti egitim testler scripts kurulum -type f \( -name '*.py' -o -name '*.typ' -o -name '*.html' -o -name '*.sh' -o -name '*.ps1' \) -not -path '*/__pycache__/*')
[ "$asim" -eq 0 ] && echo "dosya boyutları sınırda"
exit "$asim"
