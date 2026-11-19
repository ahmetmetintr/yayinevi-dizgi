#!/usr/bin/env python3
"""Tam kapak PDF'ine baskı kutularını yazar ve ölçüyü denetler (kapak skill'i).

Typst taşma paylı sayfayı doğru ölçüde üretir ama TrimBox ve BleedBox yazmaz; matbaa yazılımı kesim
çizgisini bu kutulardan okur. Araç, kesim ölçüsünü ve sırtı verilen değerlerle karşılaştırır, kutuları yazar
ve kullanılan yazı tiplerinin gömülü olduğunu gösterir.

Kullanım:
  py kapak_kutulari.py kapak/tam-kapak.pdf --genislik 135 --yukseklik 210 --sirt 15.2 --tasma 3
Gerekli paket: pymupdf
"""
import argparse
import sys

try:
    import pymupdf
except ImportError:
    sys.exit("pymupdf yüklü değil: py -m pip install pymupdf")

MM = 72 / 25.4


def main():
    for akis in (sys.stdout, sys.stderr):
        akis.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Tam kapak PDF'ine TrimBox ve BleedBox yaz")
    p.add_argument("pdf")
    p.add_argument("--genislik", type=float, required=True, help="kitabın kesim genişliği, mm")
    p.add_argument("--yukseklik", type=float, required=True, help="kitabın kesim yüksekliği, mm")
    p.add_argument("--sirt", type=float, required=True, help="sırt kalınlığı, mm")
    p.add_argument("--tasma", type=float, default=3.0, help="taşma payı, mm")
    p.add_argument("--cikti", help="yeni dosya (verilmezse aynı dosyanın üzerine yazılır)")
    a = p.parse_args()

    belge = pymupdf.open(a.pdf)
    if len(belge) != 1:
        sys.exit(f"Tam kapak tek sayfa olmalı; bu dosyada {len(belge)} sayfa var.")
    sayfa = belge[0]
    beklenen = (2 * a.genislik + a.sirt + 2 * a.tasma, a.yukseklik + 2 * a.tasma)
    gercek = (sayfa.mediabox.width / MM, sayfa.mediabox.height / MM)
    if any(abs(g - b) > 0.3 for g, b in zip(gercek, beklenen)):
        sys.exit(f"Ölçü tutmuyor: dosya {gercek[0]:.1f} × {gercek[1]:.1f} mm, beklenen "
                 f"{beklenen[0]:.1f} × {beklenen[1]:.1f} mm. Sırtı ve kesim ölçüsünü kontrol edin.")
    t = a.tasma * MM
    sayfa.set_bleedbox(sayfa.mediabox)
    sayfa.set_trimbox(pymupdf.Rect(t, t, sayfa.mediabox.width - t, sayfa.mediabox.height - t))
    fontlar = sorted({f[3] for f in sayfa.get_fonts()})
    gomulu_degil = sorted({f[3] for f in sayfa.get_fonts() if f[1] in ("n/a", "")})
    hedef = a.cikti or a.pdf
    if a.cikti:
        belge.save(hedef, garbage=3, deflate=True)
    else:
        belge.saveIncr()
    print(f"✓ Açılım {beklenen[0]:.1f} × {beklenen[1]:.1f} mm (ön/arka {a.genislik:g} × {a.yukseklik:g}, sırt {a.sirt:g}, taşma {a.tasma:g})")
    print(f"✓ TrimBox ve BleedBox yazıldı: {hedef}")
    print("  Yazı tipleri: " + ", ".join(f.split("+")[-1] for f in fontlar))
    if gomulu_degil:
        print("⚠ Gömülü olmayan yazı tipi: " + ", ".join(gomulu_degil))
    return 0


if __name__ == "__main__":
    sys.exit(main())
