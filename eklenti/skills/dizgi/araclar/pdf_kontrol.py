#!/usr/bin/env python3
"""Baskı öncesi PDF kontrolü (dizgi skill'i).

Denetler: sayfa ölçüsü, forma (sayfa sayısı), yazı tiplerinin gömülü olup olmadığı ve
beklenmeyen yazı tipi (eksik Türkçe harf yüzünden başka yazı tipine kayma), tek renk baskıda
renkli içerik, tire merdiveni (art arda tireyle biten satırlar), sayfa sonunda bölünmüş sözcük,
doldurulmamış [DOLDUR] yerleri.

Kullanım:
  py pdf_kontrol.py kitap.pdf --olcu 135x210 --forma 16 --tek-renk --yazi-tipi "Libertinus Serif"
Gerekli paket: pypdf  (pip install pypdf)
"""
import argparse
import re
import sys
from collections import defaultdict

try:
    from pypdf import PdfReader
except ImportError:
    sys.exit("pypdf yüklü değil: py -m pip install pypdf")

MM = 25.4 / 72
RENK = re.compile(rb"(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(?:(-?[\d.]+)\s+)?(rg|RG|sc|SC|scn|SCN|k|K)\b")
TIRELI = re.compile(r"[a-zçğıöşüâîû]-$")


def yazi_tipleri(sayfa):
    sonuc = []
    kaynak = sayfa.get("/Resources")
    fontlar = kaynak.get_object().get("/Font") if kaynak is not None else None
    for f in (fontlar.get_object().values() if fontlar is not None else []):
        f = f.get_object()
        ad = str(f.get("/BaseFont", "?")).lstrip("/")
        ad = ad.split("+", 1)[-1]
        tanim = f.get("/FontDescriptor")
        if "/DescendantFonts" in f:
            tanim = f["/DescendantFonts"][0].get_object().get("/FontDescriptor")
        tanim = tanim.get_object() if tanim is not None else {}
        gomulu = any(k in tanim for k in ("/FontFile", "/FontFile2", "/FontFile3"))
        sonuc.append((ad.replace("-Identity-H", ""), gomulu))
    return sonuc


def renkli_mi(sayfa):
    veri = sayfa.get_contents()
    veri = veri.get_data() if veri is not None else b""  # akış nesnesinin doğruluk değeri boş olabilir
    for e in RENK.finditer(veri):
        sayilar = [float(x) for x in e.groups()[:4] if x is not None]
        op = e.group(5).decode()
        if op in ("k", "K") and len(sayilar) == 4 and any(sayilar[:3]):
            return True
        if op not in ("k", "K") and e.group(4) is None and len(set(sayilar)) > 1:
            return True
    kaynak = sayfa.get("/Resources")
    gorseller = kaynak.get_object().get("/XObject") if kaynak is not None else None
    for g in (gorseller.get_object().values() if gorseller is not None else []):
        g = g.get_object()
        if g.get("/Subtype") == "/Image" and renk_kanali(g.get("/ColorSpace")) > 1:
            return True
    return False


def renk_kanali(uzay):
    """Görsel renk uzayının kanal sayısı: 1 gri, 3 RGB, 4 CMYK."""
    uzay = uzay.get_object() if uzay is not None else None
    if uzay is None:
        return 1
    if not isinstance(uzay, list):
        return {"/DeviceGray": 1, "/CalGray": 1, "/DeviceRGB": 3, "/CalRGB": 3, "/DeviceCMYK": 4}.get(str(uzay), 1)
    tur = str(uzay[0])
    if tur == "/ICCBased":
        return int(uzay[1].get_object().get("/N", 1))
    if tur == "/Indexed":
        return renk_kanali(uzay[1])
    return 3 if tur in ("/Lab", "/DeviceN") else 1


def main():
    for akis in (sys.stdout, sys.stderr):  # Windows konsolunda Türkçe ve ✓ için
        akis.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Baskı öncesi PDF kontrolü")
    p.add_argument("pdf")
    p.add_argument("--olcu", help="beklenen kesim ölçüsü mm, örn. 135x210")
    p.add_argument("--forma", type=int, default=16, help="forma sayfa sayısı (varsayılan 16)")
    p.add_argument("--tek-renk", action="store_true", help="tek renk (siyah) baskı: renkli içerik uyarısı ver")
    p.add_argument("--yazi-tipi", help="beklenen yazı tipi aileleri, virgülle: \"Libertinus Serif,Source Sans 3\"")
    a = p.parse_args()
    r = PdfReader(a.pdf)
    n = len(r.pages)
    uyari = 0

    def yaz(tamam, metin):
        nonlocal uyari
        uyari += not tamam
        print(f"{'✓' if tamam else '⚠'} {metin}")

    print(f"PDF kontrolü: {a.pdf}")
    eksik = (-n) % a.forma
    yaz(eksik == 0, f"{n} sayfa" + ("" if eksik == 0 else f" — {a.forma}'lık formaya {eksik} boş sayfa eksik (ya da {n % a.forma} sayfa fazla)"))

    olculer = {(round(float(s.mediabox.width) * MM, 1), round(float(s.mediabox.height) * MM, 1)) for s in r.pages}
    olcu_metni = ", ".join(f"{g:g} × {y:g} mm" for g, y in sorted(olculer))
    if a.olcu:
        g, y = (float(x) for x in a.olcu.lower().split("x"))
        yaz(all(abs(og - g) <= 0.5 and abs(oy - y) <= 0.5 for og, oy in olculer), f"Sayfa ölçüsü: {olcu_metni} (beklenen {g:g} × {y:g} mm)")
    else:
        yaz(len(olculer) == 1, f"Sayfa ölçüsü: {olcu_metni}")

    fontlar, gomulu_degil = defaultdict(list), set()
    for i, s in enumerate(r.pages, 1):
        for ad, gomulu in yazi_tipleri(s):
            fontlar[ad].append(i)
            if not gomulu:
                gomulu_degil.add(ad)
    yaz(not gomulu_degil, "Yazı tipleri gömülü" if not gomulu_degil else f"Gömülü OLMAYAN yazı tipi: {', '.join(sorted(gomulu_degil))}")
    if a.yazi_tipi:
        sade = lambda s: re.sub(r"[\s_-]", "", s).lower()
        beklenen = [sade(x) for x in a.yazi_tipi.split(",") if x.strip()]
        yabanci = sorted(ad for ad in fontlar if not any(sade(ad).startswith(b) for b in beklenen))
        yaz(not yabanci, "Yalnız beklenen yazı tipleri var" if not yabanci else
            "Beklenmeyen yazı tipi (eksik harf yüzünden kayma olabilir): "
            + "; ".join(f"{ad} s. {', '.join(map(str, fontlar[ad][:10]))}" for ad in yabanci))
    print("  Kullanılan yazı tipleri:")
    for ad, sayfalar in sorted(fontlar.items()):
        print(f"   - {ad}: {len(sayfalar)} sayfa (ilk s. {sayfalar[0]})")

    if a.tek_renk:
        renkli = [i for i, s in enumerate(r.pages, 1) if renkli_mi(s)]
        yaz(not renkli, "Renkli içerik yok" if not renkli else f"Renkli içerik var (tek renk baskı): s. {', '.join(map(str, renkli[:20]))}")

    merdiven, sayfa_sonu, doldur = [], [], []
    for i, s in enumerate(r.pages, 1):
        satirlar = [x.rstrip() for x in (s.extract_text() or "").split("\n") if x.strip()]
        if any("DOLDUR" in x for x in satirlar):
            doldur.append(i)
        art_arda = 0
        for x in satirlar:
            art_arda = art_arda + 1 if TIRELI.search(x) else 0
            if art_arda == 3:
                merdiven.append(i)
        govde = [x for x in satirlar if not x.strip().isdigit()]
        if govde and TIRELI.search(govde[-1]):
            sayfa_sonu.append(i)
    yaz(not doldur, "Doldurulmamış yer yok" if not doldur else f"[DOLDUR] yazan sayfa: s. {', '.join(map(str, doldur))}")
    yaz(not merdiven, "Tire merdiveni yok" if not merdiven else f"Art arda 3+ tireli satır: s. {', '.join(map(str, sorted(set(merdiven))))}")
    yaz(not sayfa_sonu, "Sayfa sonunda bölünen sözcük yok" if not sayfa_sonu else f"Sayfa son satırı tireyle bitiyor: s. {', '.join(map(str, sayfa_sonu[:20]))}")
    print("Görsel kontrol gerekenler: dul/öksüz satır, sayfa dibinde başlık, görsel çözünürlüğü (300 dpi).")
    print(f"Sonuç: {uyari} uyarı.")
    return 1 if uyari else 0


if __name__ == "__main__":
    sys.exit(main())
