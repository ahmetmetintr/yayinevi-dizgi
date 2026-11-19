#!/usr/bin/env python3
"""E-kitap PDF'i (dizgi skill'i): iç sayfaların önüne ön kapağı koyar, PDF bilgilerini (başlık, yazar,
konu, anahtar sözcük) yazar ve yer imlerini (içindekiler) korur.

Ön kapak, kapak skill'inin tam kapak PDF'inden kesilir (ön panel) ya da tek sayfalık bir ön kapak
PDF'i / görseli olarak verilir. İç PDF'i e-kitap için derlerken Typst'e `e-kitap: true` verin
(bağlantılar tıklanır kalır).

Kullanım:
  py e_kitap.py cikti/kitap.pdf --tam-kapak kapak/tam-kapak.pdf --genislik 160 --yukseklik 240 --tasma 3 \
      --baslik "…" --yazar "…" --cikti cikti/kitap-e-kitap.pdf
  py e_kitap.py cikti/kitap.pdf --on-kapak kapak/on-kapak.png --baslik "…" --yazar "…" --cikti …
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
    p = argparse.ArgumentParser(description="E-kitap PDF'i: ön kapak + iç sayfalar + PDF bilgileri")
    p.add_argument("ic", help="iç sayfalar PDF'i")
    kapak = p.add_mutually_exclusive_group()
    kapak.add_argument("--tam-kapak", help="tam kapak PDF'i (arka + sırt + ön); ön panel kesilir")
    kapak.add_argument("--on-kapak", help="tek sayfalık ön kapak (PDF ya da PNG/JPG)")
    p.add_argument("--genislik", type=float, help="kesim genişliği mm (tam kapaktan kesmek için)")
    p.add_argument("--yukseklik", type=float, help="kesim yüksekliği mm")
    p.add_argument("--tasma", type=float, default=3.0)
    p.add_argument("--baslik", required=True)
    p.add_argument("--yazar", required=True)
    p.add_argument("--konu", default="")
    p.add_argument("--anahtar", default="", help="anahtar sözcükler, virgülle")
    p.add_argument("--cikti", required=True)
    a = p.parse_args()

    ic = pymupdf.open(a.ic)
    toc = ic.get_toc()
    sonuc = pymupdf.open()
    eklenen = 0
    if a.tam_kapak:
        if not (a.genislik and a.yukseklik):
            sys.exit("--tam-kapak için --genislik ve --yukseklik gerekli (kesim ölçüsü, mm).")
        tam = pymupdf.open(a.tam_kapak)
        r = tam[0].rect
        t, g, y = a.tasma * MM, a.genislik * MM, a.yukseklik * MM
        kesit = pymupdf.Rect(r.width - t - g, t, r.width - t, t + y)  # ön panel sağdadır
        sayfa = sonuc.new_page(width=g, height=y)
        sayfa.show_pdf_page(sayfa.rect, tam, 0, clip=kesit)
        eklenen = 1
    elif a.on_kapak:
        if a.on_kapak.lower().endswith(".pdf"):
            sonuc.insert_pdf(pymupdf.open(a.on_kapak), from_page=0, to_page=0)
        else:
            sayfa = sonuc.new_page(width=ic[0].rect.width, height=ic[0].rect.height)
            sayfa.insert_image(sayfa.rect, filename=a.on_kapak, keep_proportion=False)
        eklenen = 1
    sonuc.insert_pdf(ic)
    if eklenen and toc:
        sonuc.set_toc([[duzey, baslik, sayfa + eklenen] + ek for duzey, baslik, sayfa, *ek in toc])
    elif toc:
        sonuc.set_toc(toc)
    sonuc.set_metadata({"title": a.baslik, "author": a.yazar, "subject": a.konu, "keywords": a.anahtar,
                        "creator": "Typst", "producer": "dizgi"})
    sonuc.save(a.cikti, garbage=3, deflate=True)
    print(f"✓ {a.cikti}: {len(sonuc)} sayfa (kapak {eklenen}), {len(toc)} yer imi, başlık ve yazar yazıldı")
    return 0


if __name__ == "__main__":
    sys.exit(main())
