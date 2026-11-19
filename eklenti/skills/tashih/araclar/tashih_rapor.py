#!/usr/bin/env python3
"""Düzeltme turunun dönüşünü hazırlar (tashih skill'i).

Yeni PDF'te uygulanan her düzeltmeyi bulur ve sayfasını yazar; istenirse PDF'in işaretli bir kopyasını
üretir: uygulanan yerler vurgulu ve yorumlu ("Uygulandı: «eski» → «yeni»"), uygulanamayanlar için sorular
not olarak. Yanına yazar ya da hoca için kısa bir rapor (Markdown) yazar.

Kullanım:
  py tashih_rapor.py cikti/kitap.pdf tashih/tur-02/liste.sonuc.json \
      --isaretli cikti/kitap-tur-02-isaretli.pdf --rapor tashih/tur-02/rapor.md --imza "Yayınevi Dizgi"
Gerekli paket: pymupdf
"""
import argparse
import json
import sys
from pathlib import Path

try:
    import pymupdf
except ImportError:
    sys.exit("pymupdf yüklü değil: py -m pip install pymupdf")

TIPOGRAFIK = [("'", "’"), ('"', "“"), ('"', "”"), ("-", "–"), ("...", "…")]


def adaylar(metin):
    """Aranacak biçimler: olduğu gibi, tipografik işaretlerle, en uzun sözcük."""
    yield metin
    for duz, tip in TIPOGRAFIK:
        if duz in metin:
            yield metin.replace(duz, tip)
    sozcukler = sorted((s.strip(".,;:!?()«»\"'“”’") for s in metin.split()), key=len, reverse=True)
    if sozcukler and len(sozcukler[0]) >= 4 and sozcukler[0] != metin:
        yield sozcukler[0]


def bul(belge, madde):
    """Uygulanan düzeltmenin yeni PDF'teki yeri: (sayfa no, dikdörtgen) ya da None."""
    hedefler = [madde.get("yeni", "")] if madde.get("yeni", "").strip() else []
    if not hedefler:  # silmede çevredeki metne bak
        hedefler = [madde.get("once", "").split()[-1]] if madde.get("once", "").split() else []
    for hedef in hedefler:
        for aday in adaylar(" ".join(hedef.split())):
            for sayfa in belge:
                alanlar = sayfa.search_for(aday)
                if alanlar:
                    return sayfa.number, alanlar
    return None


def soru_metni(madde):
    if madde.get("soru"):
        return madde["soru"]
    neden = {
        "bulunamadı": "Metinde bulamadık; yerini ve doğru biçimini belirtir misiniz?",
        "birden çok yer": "Bu ifade metinde birden çok yerde geçiyor; hangisinin değişeceğini belirtir misiniz?",
        "zaten uygulanmış olabilir": "Bu düzeltme metinde zaten var görünüyor; başka bir yer mi kastedildi?",
        "çakışma": "Aynı yerdeki başka bir düzeltmeyle çakışıyor; hangisi geçerli?",
    }
    durum = madde.get("durum", "")
    for anahtar, metin in neden.items():
        if durum.startswith(anahtar):
            return metin
    return "Bu düzeltmeyi dizgide elle uygulayacağız; anlamı açık değilse lütfen belirtin."


def main():
    for akis in (sys.stdout, sys.stderr):
        akis.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Düzeltme turunun dönüş raporu ve işaretli PDF")
    p.add_argument("pdf", help="düzeltmeler uygulandıktan sonra üretilen yeni PDF")
    p.add_argument("sonuc", help="tashih_uygula.py'nin yazdığı liste.sonuc.json")
    p.add_argument("--isaretli", help="işaretli PDF kopyasının yolu")
    p.add_argument("--rapor", help="Markdown raporun yolu")
    p.add_argument("--imza", default="Dizgi", help="PDF yorumlarında görünecek ad")
    a = p.parse_args()
    belge = pymupdf.open(a.pdf)
    maddeler = json.loads(Path(a.sonuc).read_text(encoding="utf-8"))
    uygulanan, bekleyen = [], []
    for m in maddeler:
        if m.get("durum", "").startswith("uygulandı"):  # "uygulandı (elle)" dahil
            yer = bul(belge, m)
            m["yeni_sayfa"] = yer[0] + 1 if yer else None
            uygulanan.append(m)
            if a.isaretli and yer:
                sayfa = belge[yer[0]]
                isaret = sayfa.add_highlight_annot(yer[1][0])
                ozet = f"Uygulandı: «{m.get('eski', '')}» → «{m.get('yeni', '')}»" if m.get("yeni") else f"Silindi: «{m.get('eski', '')}»"
                isaret.set_info(content=ozet, title=a.imza)
                isaret.update()
        elif m.get("islem") in ("Değiştir", "Sil", "Ekle", "Biçim", "Not") and m.get("durum") != "atlandı (karar)":
            bekleyen.append(m)

    if a.isaretli:
        for m in bekleyen:
            yer = m.get("yer", "")
            no = int(yer[3:]) - 1 if yer.startswith("s. ") and yer[3:].isdigit() else 0
            sayfa = belge[min(no, len(belge) - 1)]
            nokta = pymupdf.Point(m["alan"][2], m["alan"][1]) if m.get("alan") else pymupdf.Point(sayfa.rect.width - 40, 40)
            isaret = sayfa.add_text_annot(nokta, f"Soru (madde {m.get('no', '')}): {soru_metni(m)}\n«{m.get('eski', '')}» → «{m.get('yeni', '')}»")
            isaret.set_info(title=a.imza)
            isaret.update()
        belge.save(a.isaretli, garbage=3, deflate=True)
        print(f"İşaretli PDF: {a.isaretli}")

    satirlar = [f"# Düzeltme turu: {Path(a.sonuc).parent.name}", "",
                f"Uygulanan düzeltme: {len(uygulanan)} · yanıt bekleyen: {len(bekleyen)}", "",
                "## Uygulananlar", "", "| No | Yeni sayfa | Düzeltme |", "| --- | --- | --- |"]
    for m in uygulanan:
        satirlar.append(f"| {m.get('no', '')} | {m.get('yeni_sayfa') or '—'} | «{m.get('eski', '')}» → «{m.get('yeni', '')}» |")
    satirlar += ["", "## Yanıt bekleyenler", "", "| No | Yer | Düzeltme | Soru |", "| --- | --- | --- | --- |"]
    for m in bekleyen:
        duzeltme = f"«{m.get('eski', '')}» → «{m.get('yeni', '')}»" if m.get("eski") or m.get("yeni") else (m.get("yorum") or "")[:80]
        satirlar.append(f"| {m.get('no', '')} | {m.get('yer', '')} | {duzeltme.replace('|', '/')} | {soru_metni(m)} |")
    metin = "\n".join(satirlar) + "\n"
    if a.rapor:
        Path(a.rapor).write_text(metin, encoding="utf-8")
        print(f"Rapor: {a.rapor}")
    else:
        print(metin)
    bulunamayan = [m.get("no") for m in uygulanan if not m.get("yeni_sayfa")]
    if bulunamayan:
        print(f"Not: uygulanan şu maddelerin yeni PDF'teki yeri bulunamadı (elle bakın): {bulunamayan}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
