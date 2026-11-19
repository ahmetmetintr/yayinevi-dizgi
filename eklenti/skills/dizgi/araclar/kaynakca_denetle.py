#!/usr/bin/env python3
"""Kaynakça denetimi (dizgi skill'i): APA 7 biçimi, DOI, Türkçe alfabe sırası, yinelenen kaynak ve
metin içi atıf ↔ kaynakça eşleşmesi. Metne dokunmaz; yalnız rapor verir.

Kaynakça, metindeki #kaynakca[ … ] bloklarından ya da "Kaynaklar / Kaynakça" başlığının altındaki
paragraflardan okunur. Her dosya ayrı değerlendirilir (editörlü kitapta bölüm başına bir dosya).

Kullanım:
  py kaynakca_denetle.py metin/bolum-01.typ metin/bolum-02.typ
  py kaynakca_denetle.py metin/*.typ --crossref     DOI'leri Crossref'te de sınar (internet gerekir)
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ALFABE = "abcçdefgğhıijklmnoöpqrsştuüvwxyz"
DOI = re.compile(r"10\.\d{4,9}/[^\s\]\)>]+")
APA = re.compile(r"^(?P<yazar>[^()]+?)\s*\((?P<yil>\d{4}[a-z]?|t\.y\.|n\.d\.)[^)]*\)")
BASLIK = re.compile(r"^=+\s*(kaynaklar|kaynakça|kaynakca|references)\s*$", re.I | re.M)
KAYNAKCA_BLOGU = re.compile(r"#kaynakca(?:\((?:[^()\[\]]|\[[^\]]*\])*\))?\[")
ATIF_PARANTEZ = re.compile(r"\(([^()]*?\d{4}[a-z]?[^()]*?)\)")
ATIF_ANLATI = re.compile(r"([A-ZÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜâîû'’-]+)(?:\s+(?:ve|&)\s+[A-ZÇĞİÖŞÜ][\w'’-]+|\s+vd\.|\s+et al\.)?\s+\((\d{4}[a-z]?)\)")
PARCA = re.compile(r"^\s*(?:bkz\.\s*|örn\.\s*|aktaran\s*)?([A-ZÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜâîû'’ -]*?)(?:,|\s+ve\s|\s+&\s|\s+vd\.)[^;]*?(\d{4}[a-z]?)")


def tr_kucuk(s):
    return s.replace("I", "ı").replace("İ", "i").lower()


def sira_anahtari(s):
    return [ALFABE.index(c) for c in tr_kucuk(s) if c in ALFABE]


def sade(s):
    """Typst işaretlerini atar: _italik_, *kalın*, \\ kaçışlar, ~ bölünmez boşluk."""
    s = re.sub(r"\\(.)", r"\1", s)
    return " ".join(s.replace("_", "").replace("*", "").replace("~", " ").split())


def paragraflar(metin):
    return [sade(p) for p in re.split(r"\n\s*\n", metin) if p.strip()]


def bolumler(metin):
    """[(gövde, kaynaklar)]: her #kaynakca[…] bloğu kendinden önceki metinle bir bölüm sayılır.
    Blok yoksa "Kaynaklar / Kaynakça" başlığının altı okunur."""
    sonuc, onceki = [], 0
    for m in KAYNAKCA_BLOGU.finditer(metin):         # #kaynakca[…] ya da #kaynakca(baslik: […])[…]
        if m.start() < onceki:
            continue
        bas = j = m.end()
        derin = 1
        while j < len(metin) and derin:
            derin += {"[": 1, "]": -1}.get(metin[j], 0) if metin[j - 1] != "\\" else 0
            j += 1
        sonuc.append((metin[onceki:m.start()], paragraflar(metin[bas:j - 1])))
        onceki = j
    if not sonuc:
        b = BASLIK.search(metin)
        if b:
            son = re.search(r"^=+\s", metin[b.end():], re.M)
            sonuc.append((metin[:b.start()], paragraflar(metin[b.end(): b.end() + son.start()] if son else metin[b.end():])))
    return sonuc


def ilk_soyad(yazar):
    return tr_kucuk(re.split(r",|\s+ve\s|\s+&\s", yazar.strip())[0].strip())


def atiflar(govde):
    govde = sade(re.sub(r"#\w+\(|\)\[|//[^\n]*", " ", govde))
    bulunan = set()
    for p in ATIF_PARANTEZ.finditer(govde):
        for parca in p.group(1).split(";"):
            e = PARCA.match(parca)
            if e:
                bulunan.add((tr_kucuk(e.group(1).strip()), e.group(2)))
    for e in ATIF_ANLATI.finditer(govde):
        bulunan.add((tr_kucuk(e.group(1)), e.group(2)))
    return bulunan


def crossref(doi):
    istek = urllib.request.Request(f"https://api.crossref.org/works/{doi}", headers={"User-Agent": "dizgi-kaynakca-denetimi/1.0"})
    try:
        with urllib.request.urlopen(istek, timeout=15) as y:
            w = json.load(y)["message"]
        yil = (w.get("issued", {}).get("date-parts") or [[None]])[0][0]
        soyad = tr_kucuk((w.get("author") or [{}])[0].get("family", ""))
        return "var", yil, soyad
    except urllib.error.HTTPError as h:
        return ("yok" if h.code == 404 else f"hata {h.code}"), None, ""
    except Exception as h:  # ağ yok
        return f"denetlenemedi ({type(h).__name__})", None, ""


def denetle(govde, kaynaklar, crossref_sorgula=False):
    sorunlar, anahtarlar, gorulen = [], [], {}
    for no, k in enumerate(kaynaklar, 1):
        e, d = APA.match(k), DOI.search(k)
        kisa = k[:70] + ("…" if len(k) > 70 else "")
        if not e:
            sorunlar.append((no, "APA biçimi tanınmadı (Yazar, A. (Yıl). …)", kisa))
        else:
            anahtarlar.append((ilk_soyad(e.group("yazar")), e.group("yil"), no))
        if not d:
            sorunlar.append((no, "DOI yok", kisa))
        elif not re.search(r"https://doi\.org/10\.", k):
            sorunlar.append((no, "DOI bağlantı biçiminde değil (https://doi.org/…)", kisa))
        ozet = tr_kucuk(re.sub(r"\W", "", k))[:80]
        if ozet in gorulen:
            sorunlar.append((no, f"yinelenen kaynak ({gorulen[ozet]}. ile aynı)", kisa))
        gorulen.setdefault(ozet, no)
        if crossref_sorgula and d:
            durum, yil, soyad = crossref(d.group().rstrip(".,;"))
            if durum != "var":
                sorunlar.append((no, f"DOI Crossref'te: {durum}", d.group()))
            elif e and yil and str(yil) != e.group("yil")[:4]:
                sorunlar.append((no, f"yıl uyuşmuyor: kaynakçada {e.group('yil')}, Crossref'te {yil}", kisa))
            elif e and soyad and soyad not in tr_kucuk(e.group("yazar")):
                sorunlar.append((no, f"ilk yazar uyuşmuyor: Crossref'te «{soyad}»", kisa))
    for (s1, y1, n1), (s2, y2, n2) in zip(anahtarlar, anahtarlar[1:]):
        if (sira_anahtari(s1), y1) > (sira_anahtari(s2), y2):
            sorunlar.append((n2, f"alfabe sırası: «{s2}» «{s1}» kaynağından önce gelmeli", ""))
    atif = atiflar(govde)
    kaynak_anahtar = {(s, y) for s, y, _ in anahtarlar}
    for s, y in sorted(atif - kaynak_anahtar):
        if not any(s in ks and y == ky for ks, ky in kaynak_anahtar):
            sorunlar.append(("—", "metinde atıf var, kaynakçada yok", f"{s.title()}, {y}"))
    for s, y, no in anahtarlar:
        if not any(s == a or s in a or a in s for a, ay in atif if ay == y):
            sorunlar.append((no, "kaynakçada var, metinde atıf bulunamadı", f"{s.title()}, {y}"))
    return len(kaynaklar), len(atif), sorunlar


def main():
    for akis in (sys.stdout, sys.stderr):
        akis.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Kaynakça denetimi: APA, DOI, sıra, atıf eşleşmesi")
    p.add_argument("dosyalar", nargs="+")
    p.add_argument("--crossref", action="store_true", help="DOI'leri Crossref'te sına (internet gerekir)")
    a = p.parse_args()
    toplam = 0
    for d in a.dosyalar:
        parcalar = bolumler(Path(d).read_text(encoding="utf-8-sig"))
        if not parcalar:
            print(f"\n## {Path(d).name}: kaynakça bulunamadı (#kaynakca[…] bloğu ya da Kaynaklar başlığı yok)")
        for k, (govde, kaynaklar) in enumerate(parcalar, 1):
            n, atif, sorunlar = denetle(govde, kaynaklar, a.crossref)
            etiket = f"{Path(d).name}" + (f" · {k}. kaynakça" if len(parcalar) > 1 else "")
            print(f"\n## {etiket}: {n} kaynak, {atif} atıf, {len(sorunlar)} sorun")
            for no, ne, ornek in sorunlar:
                print(f"  ⚠ [{no}] {ne}" + (f" — {ornek}" if ornek else ""))
            toplam += len(sorunlar)
    print(f"\nToplam sorun: {toplam}. Kaynakçayı düzeltmek yazarın işidir; dizgici listeyi yazara iletir.")
    return 1 if toplam else 0


if __name__ == "__main__":
    sys.exit(main())
