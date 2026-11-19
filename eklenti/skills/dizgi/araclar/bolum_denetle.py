#!/usr/bin/env python3
"""Editörlü kitap bölüm denetimi (dizgi skill'i).

PDF'ten: her bölümün sayfa sayısı (PDF yer imlerinden) ve yayınevinin sınırına uyup uymadığı.
Metinden: #bolum(...) çağrılarında her yazarın unvan, kurum ve ORCID bilgisi; ORCID numaralarının
sağlama hanesi (ISO 7064 11,2). Metne dokunmaz; yalnız rapor verir.

Kullanım:
  py bolum_denetle.py cikti/kitap.pdf metin/*.typ --sayfa 10-25
Gerekli paket: pymupdf
"""
import argparse
import re
import sys
from pathlib import Path

ORCID = re.compile(r"\b(\d{4})-(\d{4})-(\d{4})-(\d{3}[\dX])\b")
ORCID_YAZIMI = re.compile(r"ORCID\s*:?\s*([^\s,;\]]+)", re.I)
UNVAN = re.compile(r"\b(Prof|Doç|Dr|Öğr|Arş|Uzm|Öğretim|Araştırma|Okutman|Öğretmen|Prof\.|Lect|Assoc|Assist)", re.I)
ON_SON = {"ön söz", "önsöz", "takdim", "takdim yazıları", "içindekiler", "katkıda bulunanlar", "dizin",
          "editörden", "kaynakça", "kaynaklar", "sunuş", "teşekkür"}


def orcid_gecerli(numara):
    """ORCID sağlama hanesi: ISO 7064 11,2."""
    rakamlar = numara.replace("-", "")
    if not re.fullmatch(r"\d{15}[\dX]", rakamlar):
        return False
    toplam = 0
    for r in rakamlar[:-1]:
        toplam = (toplam + int(r)) * 2
    sonuc = (12 - toplam % 11) % 11
    return rakamlar[-1] == ("X" if sonuc == 10 else str(sonuc))


def bolum_cagrilari(metin):
    """#bolum(...) çağrılarını dengeli parantezle bulur: [(başlık parçası, yazarlar parçası)]."""
    sonuc, i = [], metin.find("#bolum(")
    while i >= 0:
        j, derin = i + len("#bolum("), 1
        while j < len(metin) and derin:
            derin += {"(": 1, ")": -1}.get(metin[j], 0)
            j += 1
        govde = metin[i + len("#bolum("):j - 1]
        baslik = re.match(r"\s*\[([^\]]*)\]", govde)
        yazarlar = re.findall(r'\(\s*"([^"]+)"\s*,\s*\[([^\]]*)\]\s*\)', govde)
        sonuc.append((baslik.group(1) if baslik else govde[:40], yazarlar))
        i = metin.find("#bolum(", j)
    return sonuc


def metin_denetle(yol):
    metin = Path(yol).read_text(encoding="utf-8-sig")
    sorunlar = []
    for baslik, yazarlar in bolum_cagrilari(metin):
        if not yazarlar:
            sorunlar.append((baslik, "yazar bilgisi yok"))
        for ad, bilgi in yazarlar:
            if not re.search(r"\b[A-ZÇĞİÖŞÜ]{2,}\b", ad):
                sorunlar.append((baslik, f"{ad}: soyadı büyük harfle yazılmamış (Ad SOYAD)"))
            if not UNVAN.search(bilgi):
                sorunlar.append((baslik, f"{ad}: unvan yok"))
            if not re.search(r"Üniversite|University|Enstitü|Hastane|Bakanlığı|Okulu|Lisesi|Kurum", bilgi, re.I):
                sorunlar.append((baslik, f"{ad}: kurum bilgisi bulunamadı"))
            if "orcid" not in bilgi.lower():
                sorunlar.append((baslik, f"{ad}: ORCID yok"))
    for e in ORCID_YAZIMI.finditer(metin):
        numara = e.group(1).rstrip(".")
        if not ORCID.fullmatch(numara):
            sorunlar.append(("ORCID", f"{numara}: biçim 0000-0000-0000-0000 değil"))
        elif not orcid_gecerli(numara):
            sorunlar.append(("ORCID", f"{numara}: sağlama hanesi tutmuyor (yanlış yazılmış olabilir)"))
    return sorunlar


def sayfa_denetle(pdf, en_az, en_cok):
    import pymupdf
    belge = pymupdf.open(pdf)
    bolumler = [(baslik, sayfa) for duzey, baslik, sayfa in belge.get_toc() if duzey == 1]
    sonuc = []
    for k, (baslik, bas) in enumerate(bolumler):
        son = bolumler[k + 1][1] - 1 if k + 1 < len(bolumler) else len(belge)
        uzunluk = son - bas + 1
        on_son = baslik.strip().replace("I", "ı").replace("İ", "i").lower() in ON_SON
        sonuc.append((baslik, bas, uzunluk, None if on_son else (en_az <= uzunluk <= en_cok)))
    return sonuc


def main():
    for akis in (sys.stdout, sys.stderr):
        akis.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Editörlü kitap bölüm denetimi")
    p.add_argument("pdf")
    p.add_argument("metinler", nargs="*")
    p.add_argument("--sayfa", default="10-25", help="bölüm başına sayfa sınırı, kaynakça dahil (varsayılan 10-25)")
    a = p.parse_args()
    en_az, en_cok = (int(x) for x in a.sayfa.split("-"))
    uyari = 0
    print(f"| Bölüm | Başladığı fiziksel sayfa | Sayfa | {a.sayfa} |")
    print("| --- | --- | --- | --- |")
    for baslik, bas, uzunluk, uygun in sayfa_denetle(a.pdf, en_az, en_cok):
        isaret = "—" if uygun is None else ("✓" if uygun else "⚠")
        uyari += uygun is False
        print(f"| {baslik[:60]} | {bas} | {uzunluk} | {isaret} |")
    for m in a.metinler:
        for baslik, ne in metin_denetle(m):
            print(f"⚠ {Path(m).name} · {baslik[:50]}: {ne}")
            uyari += 1
    print(f"Sonuç: {uyari} uyarı. Sayfa sınırı yayınevinin kuralıdır; aşan bölüm için editöre bilgi verilir.")
    return 1 if uyari else 0


if __name__ == "__main__":
    sys.exit(main())
