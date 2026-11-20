#!/usr/bin/env python3
"""Boşlukla dizilmiş tabloyu gerçek tabloya çevirme taslağı (dizgi skill'i).

Bazı Word dosyalarında (çoğu eski .doc) tablo, tablo nesnesiyle değil boşluk ya da sekmeyle hizalanarak yazılır.
Ekranda tablo gibi görünür ama yapısı paragraftır: pandoc onu düz metne çevirir, dizgide tablo çizilmez (Klinik
Çocuk Cerrahisi, 36. bölüm). Bu araç Word'ün XML'inden boşlukları koruyarak "Tablo N." yazısından sonraki hizalı
satırları okur ve Typst tablo taslağı yazar:
  - iki ya da daha çok boşluk ya da sekme sütun sınırıdır;
  - kısa, tek parçalı satır (ör. "karsinom") önceki satırdaki en uzun yazılı hücrenin devamı sayılır;
  - sütun sayısı tutmayan satırlar "// DENETLE" yorumuyla işaretlenir (ör. iki satıra bölünmüş başlık).
Hiçbir harf eklenmez ya da atılmaz: hücrelerin harf dizisi kaynak satırlarınkiyle karşılaştırılır. Taslak,
Word'e bakılarak editörle birlikte düzeltilir ve bölüm dosyasında düz metin hâlindeki tablonun yerine konur.

Kullanım:
  py tablo_kur.py metin/donusum/36.docx                 aday tabloları listeler
  py tablo_kur.py metin/donusum/36.docx --tablo 1 3     Tablo 1 ve 3'ün Typst taslağı
.doc dosyası önce çevrilir (LibreOffice): soffice --headless --convert-to docx --outdir metin/donusum kaynak/36.doc
"""
import argparse
import re
from collections import Counter
import sys
import zipfile
import xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
YAZI = re.compile(r"\s*Tablo\s+(\d+)\s*[.:]\s*(.*)")
NOT_SATIRI = re.compile(r"\s*(\*|\(\*\)|not\b|notlar\b|kaynak|kısaltma)", re.I)
SINIR = re.compile(r"\t+| {2,}")
DEVAM_UZUNLUGU = 40
KACIS = re.compile(r"([\\#$\[\]*_@<>`])")


def docx_satirlari(yol):
    """Gövdedeki paragrafların yazısı, boşluk ve sekmeler korunarak; satır sonu (w:br) ayrı satır."""
    kok = ET.fromstring(zipfile.ZipFile(yol).read("word/document.xml"))
    satirlar = []
    for p in kok.iter(W + "p"):
        s = ""
        for el in p.iter():
            if el.tag == W + "t":
                s += el.text or ""
            elif el.tag == W + "tab":
                s += "\t"
            elif el.tag in (W + "br", W + "cr"):
                s += "\n"
        satirlar += s.split("\n")
    return satirlar


def hucreler(satir):
    return [h for h in SINIR.split(satir.strip()) if h]


def devam_mi(satirlar, j):
    """Kısa, tek parçalı satır: ardından (boş ve kısa satırlar atlanınca) yeniden hizalı satır geliyorsa devamdır."""
    for s in satirlar[j:]:
        h = hucreler(s)
        if len(h) >= 2:
            return True
        if h and (len(h[0]) > DEVAM_UZUNLUGU or NOT_SATIRI.match(s)):
            return False
    return False


def tablo_bul(satirlar, i):
    """satirlar[i] tablo yazısı: → (satırlar, uyarılar, okunan son satırın sırası)."""
    satir_listesi, uyarilar, j, son = [], [], i + 1, i
    while j < len(satirlar):
        h = hucreler(satirlar[j])
        if not h:
            j += 1
            continue
        if len(h) >= 2:
            satir_listesi.append(h)
        elif satir_listesi and len(h[0]) <= DEVAM_UZUNLUGU and not NOT_SATIRI.match(satirlar[j]) and devam_mi(satirlar, j + 1):
            onceki = satir_listesi[-1]
            k = max(range(len(onceki)), key=lambda n: (bool(re.search(r"[^\W\d]{3}", onceki[n])), len(onceki[n])))
            onceki[k] = f"{onceki[k]} {h[0]}"
            uyarilar.append(f"\"{h[0]}\" önceki satırın \"{onceki[k]}\" hücresine eklendi")
        else:
            if satir_listesi and NOT_SATIRI.match(satirlar[j]):
                uyarilar.append(f"tablo notu olabilir (#notlu-sekil ile tabloya bağlanır): \"{satirlar[j].strip()[:60]}\"")
            elif satir_listesi and len(h[0]) <= DEVAM_UZUNLUGU:
                uyarilar.append(f"son satırın devamı olabilir, taslağa alınmadı: \"{h[0]}\"")
            break
        son = j
        j += 1
    return satir_listesi, uyarilar, son


def kac(s):
    return KACIS.sub(r"\\\1", s)


def typst_taslagi(no, baslik, satir_listesi):
    sutun = max((len(s) for s in satir_listesi), default=1)
    govde = []
    for n, s in enumerate(satir_listesi):
        not_ = f"  // DENETLE: {len(s)} hücre, {sutun} sütun" if len(s) != sutun else ""
        hucre = ", ".join(f"[{kac(h)}]" for h in s + [""] * (sutun - len(s)))
        govde.append(f"    table.header({hucre}),{not_}" if n == 0 else f"    {hucre},{not_}")
    return (f"#figure(numbering: none, caption: [#strong[Tablo {no}.] {kac(baslik)}],\n"
            f"  table(\n    columns: {sutun},\n" + "\n".join(govde) + "\n  ),\n)")


def harf_dizisi(s):
    return [c for c in s if c.isalnum()]


def main():
    for akis in (sys.stdout, sys.stderr):
        akis.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Boşlukla dizilmiş tabloyu Typst tablosuna çevirme taslağı")
    p.add_argument("docx", help="Word dosyası (.docx; .doc önce LibreOffice ile çevrilir)")
    p.add_argument("--tablo", nargs="*", type=int, help="taslağı yazılacak tablo numaraları")
    a = p.parse_args()
    if a.docx.lower().endswith(".doc"):
        sys.exit("Eski .doc: önce çevirin → soffice --headless --convert-to docx --outdir metin/donusum " + a.docx)
    satirlar = docx_satirlari(a.docx)
    bulunan = 0
    for i, satir in enumerate(satirlar):
        e = YAZI.match(satir)
        if not e:
            continue
        no, baslik = int(e.group(1)), e.group(2).strip()
        satir_listesi, uyarilar, son = tablo_bul(satirlar, i)
        if not satir_listesi:
            continue  # ardından hizalı satır gelmiyor: gerçek tablo ya da metin içi atıf
        bulunan += 1
        if a.tablo is None:
            print(f"Tablo {no}: {len(satir_listesi)} satır, {max(map(len, satir_listesi))} sütun — {baslik[:60]}")
            continue
        if no not in a.tablo:
            continue
        kaynak = "".join(satirlar[i + 1:son + 1])
        tutuyor = Counter(harf_dizisi(kaynak)) == Counter(harf_dizisi("".join(h for s in satir_listesi for h in s)))
        print(f"// Tablo {no}: {len(satir_listesi)} satır · harfler {'AYNI ✓' if tutuyor else 'DEĞİŞTİ ✗ (elle bakın)'}")
        for u in uyarilar:
            print(f"// DENETLE: {u}")
        print(typst_taslagi(no, baslik, satir_listesi) + "\n")
    if not bulunan:
        print("Boşlukla dizilmiş tablo bulunamadı.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
