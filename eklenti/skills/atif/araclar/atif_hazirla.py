#!/usr/bin/env python3
"""Atıf dizini kaydını hazırlar (atif skill'i): kitap PDF'lerinden atif-dizini/dizin.json.

Her kitaptan: künye sayfası (ISBN, E-ISBN, DOI, baskı tarihi ve yeri), bölümler (PDF yer imlerinden; yer imi yoksa
sayfa düzeninden ya da --bolum-sayfalari ile), her bölümün ilk sayfası, başlığı ve yazarları, kaynakça sayfaları ve
kaynakçadaki kaynaklar tek tek. Bilinmeyeni uydurmaz: bulunamayan alan boş kalır ve uyarı yazılır. Dizinde aynı
kodlu kitap varsa --uzerine-yaz verilmeden değiştirilmez (dizin.json'da elle yapılan düzeltmeler korunur).

Kullanım:
  py atif_hazirla.py atif-dizini/kitaplar [--dizin atif-dizini/dizin.json] [--donem 2026-01..2026-03]
  py atif_hazirla.py atif-dizini/kitaplar/kitap.pdf --bolum-sayfalari 9,23,41 --uzerine-yaz
Gerekli paket: pymupdf
"""
import argparse
import os
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from atif_kaynakca import bolum_kaynaklari, doi_bul  # noqa: E402
from atif_ortak import dizin_oku, dizin_yaz, kaynakca_basligi_mi, tr_kucuk  # noqa: E402
from atif_yapi import (ayni_satiri_birlestir, basili_numara, baslik_temizle, bolum_araliklari,  # noqa: E402
                       bolum_baslari_tahmini, bolum_basi, donemde_mi, govde, kenar_kumesi, kisiler, kitap_basligi,
                       kitap_birimi, kunye_alanlari, kunye_sayfasi_mi, yer_imi_baslari)

KITAP_BIRIMI = "kitap sonu kaynakçası (kitap tek birim)"


# ---------------------------------------------------------------- PDF okuma
def sayfa_satirlari(sayfa, no):
    ham = []
    for blok in sayfa.get_text("dict")["blocks"]:
        for satir in blok.get("lines", []):
            metin = "".join(p["text"] for p in satir["spans"])
            if metin.strip():
                x0, y0, x1, _ = satir["bbox"]
                ham.append({"sayfa": no, "x": round(x0, 1), "x1": round(x1, 1), "y": round(y0, 1),
                            "s": round(max(p["size"] for p in satir["spans"]), 1), "t": metin,
                            "h": sayfa.rect.height})
    return ayni_satiri_birlestir(ham)


def metin(satirlar):
    return "\n".join(s["t"] for s in satirlar)


class Kitap:
    """Bir PDF'in satırları: sayfalar[i] ham, temiz[i] üst/alt bilgisiz (i = fiziksel sayfa - 1)."""

    def __init__(self, pdf):
        import pymupdf
        self.belge = pymupdf.open(pdf)
        self.n = len(self.belge)
        self.sayfalar = [sayfa_satirlari(self.belge[i], i + 1) for i in range(self.n)]
        kume = kenar_kumesi([s for ss in self.sayfalar for s in ss])
        self.temiz = [govde(ss, kume) for ss in self.sayfalar]
        puntolar = Counter(round(s["s"]) for ss in self.sayfalar for s in ss if len(s["t"]) > 30)
        self.govde_punto = puntolar.most_common(1)[0][0] if puntolar else 11

    def numara(self, p):
        """Basılı sayfa numarası; açılış sayfasında numara basılmamışsa sonraki sayfanınkinden bir eksik."""
        n = basili_numara(self.belge[p - 1].get_label(), self.sayfalar[p - 1])
        if n is None and p < self.n:
            sonraki = basili_numara(self.belge[p].get_label(), self.sayfalar[p])
            n = str(int(sonraki) - 1) if sonraki and sonraki.isdigit() else None
        return n


# ---------------------------------------------------------------- kitap ve bölümler
def kunye_bul(k):
    adaylar = list(range(min(12, k.n))) + list(range(max(k.n - 4, 12), k.n))
    return next((i + 1 for i in adaylar if kunye_sayfasi_mi(metin(k.sayfalar[i]))), None)


def araliklari_bul(k, kunye_no, bolum_sayfalari, uyarilar):
    """Bölüm aralıkları ve nereden bulundukları. Sıra: elle verilen sayfalar → yer imlerinde kaynakçalı bölümler →
    yer imlerinin 1. düzeyi → sayfa düzeninden tahmin. Kaynakça yalnız kitabın sonundaysa kitap tek birimdir."""
    kaynakca_basliklari = [s["sayfa"] for ss in k.temiz for s in ss if kaynakca_basligi_mi(s["t"])]
    toc = k.belge.get_toc()
    if bolum_sayfalari:
        baslar, kaynak = bolum_sayfalari, "elle verilen sayfalar"
    else:
        araliklar = bolum_araliklari(toc, k.n, kaynakca_basliklari)
        if araliklar:
            return araliklar, "yer imleri"
        baslar, kaynak = yer_imi_baslari(toc, k.n, kunye_no or 0), "yer imleri"
        if not baslar:
            ozet = [(i + 1, ss[0]["t"].strip(), ss[0]["s"]) if ss else (i + 1, "", 0) for i, ss in enumerate(k.temiz)]
            baslar, kaynak = bolum_baslari_tahmini(ozet, k.govde_punto, kunye_no or 0), "sayfa düzeni (tahmin)"
            uyarilar.append("PDF'te yer imi yok: bölüm başları sayfa düzeninden tahmin edildi; içindekiler "
                            "sayfasıyla karşılaştırın, gerekirse --bolum-sayfalari verin")
        ilk = kitap_birimi(baslar, kaynakca_basliklari)
        if ilk:
            uyarilar.append("kaynakça yalnız kitabın sonunda (telif kitap): kitap tek birim alındı; ilk sayfa "
                            f"PDF s. {ilk}, metnin başladığı sayfa bu değilse --bolum-sayfalari ile verin")
            return [("", ilk, k.n)], KITAP_BIRIMI
    return [("", b, (baslar[i + 1] - 1 if i + 1 < len(baslar) else k.n)) for i, b in enumerate(baslar)], kaynak


def bolum_oku(k, toc_baslik, ilk, son):
    """Bir bölüm aralığı → bölüm kaydı; kaynakça başlığı yoksa None."""
    while ilk < son and not k.temiz[ilk - 1]:
        ilk += 1
    while son > ilk and not k.temiz[son - 1]:
        son -= 1
    kayitlar, kaynakca_sayfalari = bolum_kaynaklari([s for p in range(ilk, son + 1) for s in k.temiz[p - 1]])
    if not kaynakca_sayfalari:
        return None
    son_kaynak = kaynakca_sayfalari[-1]
    sayfa_baslik, yazarlar = bolum_basi(k.temiz[ilk - 1])
    return {"no": 0, "baslik": baslik_temizle(toc_baslik) if toc_baslik else sayfa_baslik, "yazarlar": yazarlar,
            "doi": doi_bul(metin(k.temiz[ilk - 1])), "ilk_sayfa": k.numara(ilk) or "", "son_sayfa":
            k.numara(son_kaynak) or "", "pdf_ilk": ilk, "pdf_son": son_kaynak,
            "kaynakca_sayfalari": kaynakca_sayfalari, "atla": False, "kaynaklar": kayitlar}


def kod_uret(kunye, pdf):
    rakam = re.sub(r"[^\dX]", "", (kunye["e_isbn"] or kunye["isbn"]).upper())
    return rakam or re.sub(r"[^a-z0-9çğıöşü]+", "-", tr_kucuk(Path(pdf).stem)).strip("-")


def kitap_oku(pdf, bolum_sayfalari=None):
    k = Kitap(pdf)
    uyarilar = []
    kunye_no = kunye_bul(k)
    kunye = kunye_alanlari(metin(k.sayfalar[kunye_no - 1]) if kunye_no else "")
    if not kunye_no:
        uyarilar.append("künye sayfası bulunamadı (ISBN ile sertifika, telif ya da baskı satırı olan sayfa)")
    ic_kapak = next((ss for ss in k.temiz[:kunye_no or 3] if ss), [])
    baslik, alt, editor = kitap_basligi(ic_kapak, k.govde_punto)
    araliklar, kaynak = araliklari_bul(k, kunye_no, bolum_sayfalari, uyarilar)
    bolumler, kaynakcasiz = [], []
    for toc_baslik, ilk, son in araliklar:
        b = bolum_oku(k, toc_baslik, ilk, son)
        if b is None:
            kaynakcasiz.append(f"{toc_baslik or 'başlıksız'} (PDF s. {ilk})")
            continue
        b["no"] = len(bolumler) + 1
        if b["doi"] == kunye["doi"]:
            b["doi"] = ""
        if kaynak == KITAP_BIRIMI:
            b["baslik"], b["yazarlar"] = baslik, kisiler(editor)
        bolumler.append(b)
    if kaynakcasiz:
        uyarilar.append("kaynakçası bulunamayan bölüm(ler) dizine alınmadı: " + "; ".join(kaynakcasiz))
    if any(not (b["ilk_sayfa"] and b["son_sayfa"]) for b in bolumler):
        uyarilar.append("bazı bölümlerde basılı sayfa numarası okunamadı (alanlar boş): PDF'e bakıp doldurun")
    for b in bolumler:
        if not b["yazarlar"]:
            uyarilar.append(f"{b['no']}. bölüm: yazar bulunamadı (bölümün ilk sayfasına bakın)")
        if not b["kaynaklar"]:
            uyarilar.append(f"{b['no']}. bölüm: kaynakça başlığı var ama kaynak okunamadı (taranmış sayfa olabilir)")
    return {"kod": kod_uret(kunye, pdf), "dosya": "", "baslik": baslik or k.belge.metadata.get("title", ""),
            "alt_baslik": alt, "editorler": editor, "isbn": kunye["isbn"], "e_isbn": kunye["e_isbn"],
            "doi": kunye["doi"], "yayin_yeri": kunye["yayin_yeri"], "yayim_tarihi": kunye["yayim_tarihi"],
            "kunye_sayfasi": kunye_no, "bolum_kaynagi": kaynak, "bolumler": bolumler, "uyarilar": uyarilar}


# ---------------------------------------------------------------- komut
def pdf_listesi(girdiler):
    for g in girdiler:
        p = Path(g)
        yield from (sorted(x for x in p.iterdir() if x.suffix.lower() == ".pdf") if p.is_dir() else [p])


def ozet_yaz(k):
    print(f"\n## {k['kod']} · {k['baslik'][:60]} · yayım {k['yayim_tarihi'] or '?'} · "
          f"künye PDF s. {k['kunye_sayfasi'] or '?'} · bölümler: {k['bolum_kaynagi']}")
    print("| No | Bölüm | Yazarlar | Basılı s. | PDF ilk s. | Kaynakça (PDF s.) | Kaynak |")
    print("| --- | --- | --- | --- | --- | --- | --- |")
    for b in k["bolumler"]:
        ks = b["kaynakca_sayfalari"]
        print(f"| {b['no']} | {b['baslik'][:55]} | {', '.join(b['yazarlar'])[:45]} | {b['ilk_sayfa']}–{b['son_sayfa']} "
              f"| {b['pdf_ilk']} | {ks[0]}–{ks[-1]} | {len(b['kaynaklar'])} |")
    for u in k["uyarilar"]:
        print(f"⚠ {u}")


def main():
    for akis in (sys.stdout, sys.stderr):
        akis.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Kitap PDF'lerinden atıf dizini kaydı (dizin.json)")
    p.add_argument("girdiler", nargs="+", help="PDF dosyaları ya da PDF'lerin olduğu klasör")
    p.add_argument("--dizin", default="atif-dizini/dizin.json")
    p.add_argument("--donem", help="yalnız bu dönemde yayımlananlar: 2026, 2026-01 ya da 2026-01..2026-03")
    p.add_argument("--bolum-sayfalari", help="bölümlerin başladığı PDF sayfaları (yer imi yoksa): 9,23,41")
    p.add_argument("--uzerine-yaz", action="store_true", help="dizinde aynı kodlu kitap varsa yenisiyle değiştir")
    a = p.parse_args()
    pdfler = list(pdf_listesi(a.girdiler))
    if a.bolum_sayfalari and len(pdfler) != 1:
        sys.exit("--bolum-sayfalari tek PDF ile kullanılır")
    sayfalar = [int(x) for x in a.bolum_sayfalari.split(",")] if a.bolum_sayfalari else None
    dizin = dizin_oku(a.dizin)
    klasor = Path(a.dizin).resolve().parent
    eklenen = 0
    for pdf in pdfler:
        k = kitap_oku(pdf, sayfalar)
        yol = Path(pdf).resolve()
        k["dosya"] = os.path.relpath(yol, klasor) if yol.drive == klasor.drive else str(yol)
        if a.donem and donemde_mi(k["yayim_tarihi"], a.donem) is not True:
            neden = "yayım tarihi künyeden okunamadı" if not k["yayim_tarihi"] else f"yayım {k['yayim_tarihi']}"
            print(f"\n— {Path(pdf).name}: {a.donem} dönemi dışında sayıldı ({neden}); dizine eklenmedi")
            continue
        var = [i for i, x in enumerate(dizin["kitaplar"]) if x["kod"] == k["kod"]]
        if var and not a.uzerine_yaz:
            print(f"\n— {Path(pdf).name}: {k['kod']} kodlu kitap dizinde zaten var; değiştirmek için --uzerine-yaz")
            continue
        dizin["kitaplar"] = [x for x in dizin["kitaplar"] if x["kod"] != k["kod"]] + [k]
        ozet_yaz(k)
        eklenen += 1
    dizin_yaz(a.dizin, dizin)
    print(f"\n{eklenen} kitap yazıldı → {a.dizin} (dizinde toplam {len(dizin['kitaplar'])} kitap)")
    print(f"Sonra: py atif_uret.py {a.dizin} --yalniz-denetle")
    return 0


if __name__ == "__main__":
    sys.exit(main())
