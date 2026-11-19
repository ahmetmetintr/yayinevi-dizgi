#!/usr/bin/env python3
"""Atıf dizini dosyalarını üretir (atif skill'i): dizin.json → bölüm PDF'leri ve atif-dizini.xlsx.

Bölüm PDF'i: kitabın künye sayfası + bölümün ilk sayfası + bölümün kaynakça sayfaları, bu sırayla ve yer imli
(<dizin klasörü>/pdf/<kitap kodu>/<kod>-bolum-NN.pdf). atif-dizini.xlsx dizindeki bütün kitapları taşır: "Kaynaklar"
sayfasında her satır bir kaynak, "Bölümler" sayfasında her satır bir bölüm, "Kitaplar" sayfasında her satır bir
kitap. Üretilen dosyalar elle düzenlenmez: düzeltme dizin.json'da yapılır, araç yeniden çalıştırılır. Önce denetler;
hata varsa hiçbir dosya yazmaz.

Kullanım:
  py atif_uret.py atif-dizini/dizin.json --yalniz-denetle
  py atif_uret.py atif-dizini/dizin.json [--kitap <kitap kodu>]
Gerekli paket: pymupdf (bölüm PDF'leri için; tablo için gerekmez)
"""
import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from atif_ortak import dizin_oku  # noqa: E402
from atif_xlsx import xlsx_yaz  # noqa: E402

TABLO = "atif-dizini.xlsx"


def bolumler(kitap):
    return [b for b in kitap["bolumler"] if not b.get("atla")]


def pdf_yolu(kitap, b):
    return f"pdf/{kitap['kod']}/{kitap['kod']}-bolum-{b['no']:02d}.pdf"


def sayfa_araligi(b):
    return f"{b['ilk_sayfa']}–{b['son_sayfa']}" if b["ilk_sayfa"] and b["son_sayfa"] else ""


def kitap_adi(kitap):
    return kitap["baslik"] + (f": {kitap['alt_baslik']}" if kitap.get("alt_baslik") else "")


# ---------------------------------------------------------------- denetim
def kitap_denetle(kitap, klasor, hatalar, uyarilar):
    kod = kitap["kod"]
    if not (Path(klasor) / kitap["dosya"]).exists():
        hatalar.append(f"{kod}: kitabın PDF'i bulunamadı ({kitap['dosya']})")
    if not kitap.get("kunye_sayfasi"):
        hatalar.append(f"{kod}: künye sayfası yok (dizin.json'da kunye_sayfasi: PDF'teki sayfa numarası)")
    if not kitap.get("baslik"):
        hatalar.append(f"{kod}: kitabın adı yok")
    if not kitap.get("yayim_tarihi"):
        uyarilar.append(f"{kod}: yayım tarihi yok (künyedeki Baskı satırı)")
    if not (kitap.get("isbn") or kitap.get("e_isbn")):
        uyarilar.append(f"{kod}: ISBN ve E-ISBN yok")
    if not bolumler(kitap):
        hatalar.append(f"{kod}: dizine alınacak bölüm yok")
    for b in bolumler(kitap):
        yer = f"{kod} · {b['no']}. bölüm"
        if not b.get("baslik"):
            hatalar.append(f"{yer}: başlık yok")
        if not isinstance(b.get("pdf_ilk"), int) or b["pdf_ilk"] < 1:
            hatalar.append(f"{yer}: ilk sayfa (pdf_ilk) yok")
        if not b.get("kaynakca_sayfalari"):
            hatalar.append(f"{yer}: kaynakça sayfası yok (bölüm dizine alınmayacaksa \"atla\": true)")
        if not b.get("kaynaklar"):
            hatalar.append(f"{yer}: kaynak yok (bölüm dizine alınmayacaksa \"atla\": true)")
        if not b.get("yazarlar"):
            uyarilar.append(f"{yer}: yazar yok")
        if not sayfa_araligi(b):
            uyarilar.append(f"{yer}: basılı sayfa aralığı eksik")
        sayi = Counter("yilsiz" if not k.get("yil") else k.get("bicim") for k in b.get("kaynaklar", []))
        if sayi["yilsiz"]:
            uyarilar.append(f"{yer}: {sayi['yilsiz']} kaynakta yıl okunamadı")


def denetle(dizin, klasor):
    """(hatalar, uyarılar). Hata dosya yazmayı durdurur; uyarı yalnız bildirilir."""
    hatalar, uyarilar = [], []
    kodlar = Counter(k["kod"] for k in dizin["kitaplar"])
    hatalar += [f"{kod}: aynı kodlu {n} kitap var" for kod, n in kodlar.items() if n > 1]
    for kitap in dizin["kitaplar"]:
        kitap_denetle(kitap, klasor, hatalar, uyarilar)
    return hatalar, uyarilar


# ---------------------------------------------------------------- tablo
def sirali(dizin):
    return sorted(dizin["kitaplar"], key=lambda k: (k.get("yayim_tarihi") or "9999", k["kod"]))


def tablo_sayfalari(dizin):
    """atif-dizini.xlsx'in sayfaları: [(ad, başlıklar, satırlar, genişlikler)]."""
    kaynak, bolum, kitap_satirlari = [], [], []
    for k in sirali(dizin):
        ortak = [k["kod"], kitap_adi(k)]
        for b in bolumler(k):
            yazarlar = ", ".join(b["yazarlar"])
            for x in b["kaynaklar"]:
                kaynak.append(ortak + [k.get("editorler", ""), k.get("isbn", ""), k.get("e_isbn", ""), k.get("doi", ""),
                                       k.get("yayim_tarihi", ""), b["no"], b["baslik"], yazarlar, b.get("doi", ""),
                                       sayfa_araligi(b), x["no"], x["metin"], x.get("ilk_yazar", ""),
                                       x.get("yil", ""), x.get("doi", ""), pdf_yolu(k, b)])
            ks = b["kaynakca_sayfalari"]
            bolum.append(ortak + [k.get("yayim_tarihi", ""), b["no"], b["baslik"], yazarlar, b.get("doi", ""),
                                  sayfa_araligi(b), len(b["kaynaklar"]), k["kunye_sayfasi"], b["pdf_ilk"],
                                  f"{ks[0]}–{ks[-1]}" if ks else "", pdf_yolu(k, b)])
        kitap_satirlari.append(ortak + [k.get("editorler", ""), k.get("isbn", ""), k.get("e_isbn", ""),
                                        k.get("doi", ""), k.get("yayim_tarihi", ""), k.get("yayin_yeri", ""),
                                        len(bolumler(k)), sum(len(b["kaynaklar"]) for b in bolumler(k)),
                                        k["dosya"]])
    return [
        ("Kaynaklar", ["Kitap kodu", "Kitap", "Editör(ler)", "ISBN", "E-ISBN", "Kitap DOI", "Yayım", "Bölüm no",
                       "Bölüm", "Bölüm yazarları", "Bölüm DOI", "Bölüm sayfaları", "Kaynak no", "Kaynak",
                       "İlk yazar", "Yıl", "Kaynağın DOI'si", "Bölüm PDF'i"], kaynak,
         [16, 40, 28, 18, 18, 30, 9, 9, 45, 35, 30, 12, 9, 90, 20, 7, 32, 40]),
        ("Bölümler", ["Kitap kodu", "Kitap", "Yayım", "Bölüm no", "Bölüm", "Bölüm yazarları", "Bölüm DOI",
                      "Bölüm sayfaları", "Kaynak sayısı", "Künye (PDF s.)", "İlk sayfa (PDF s.)",
                      "Kaynakça (PDF s.)", "Bölüm PDF'i"], bolum, [16, 40, 9, 9, 45, 35, 30, 12, 10, 10, 10, 12, 40]),
        ("Kitaplar", ["Kitap kodu", "Kitap", "Editör(ler)", "ISBN", "E-ISBN", "DOI", "Yayım", "Yayın yeri",
                      "Bölüm sayısı", "Kaynak sayısı", "Kitabın PDF'i"], kitap_satirlari,
         [16, 45, 30, 18, 18, 30, 9, 12, 10, 10, 40]),
    ]


# ---------------------------------------------------------------- bölüm PDF'i
def bolum_pdf(belge, kitap, b, hedef):
    """Künye + bölümün ilk sayfası + kaynakça sayfaları → tek PDF (yer imli)."""
    import pymupdf
    kaynakca = [p for p in b["kaynakca_sayfalari"] if p != b["pdf_ilk"]]
    sayfalar = [kitap["kunye_sayfasi"], b["pdf_ilk"]] + kaynakca
    for p in sayfalar:
        if not 1 <= p <= len(belge):
            raise ValueError(f"{kitap['kod']} · {b['no']}. bölüm: PDF'te {p}. sayfa yok ({len(belge)} sayfa)")
    yeni = pymupdf.open()
    for p in sayfalar:
        yeni.insert_pdf(belge, from_page=p - 1, to_page=p - 1, links=False)
    toc = [[1, "Künye", 1], [1, f"Bölümün ilk sayfası: {b['baslik']}", 2]]
    yeni.set_toc(toc + ([[1, "Kaynakça", 3]] if kaynakca else []))
    yeni.set_metadata({"title": b["baslik"], "author": ", ".join(b["yazarlar"]),
                       "subject": f"{kitap_adi(kitap)} · künye, bölümün ilk sayfası ve kaynakça",
                       "keywords": "; ".join(x for x in (kitap.get("isbn"), kitap.get("e_isbn"), b.get("doi")) if x),
                       "creator": "dizgi eklentisi · atif", "producer": "", "creationDate": "", "modDate": ""})
    hedef.parent.mkdir(parents=True, exist_ok=True)
    yeni.save(str(hedef), garbage=3, deflate=True, no_new_id=True)


def pdfleri_yaz(dizin, klasor, kod):
    import pymupdf
    yazilan = 0
    for kitap in sirali(dizin):
        if kod and kitap["kod"] != kod:
            continue
        belge = pymupdf.open(str(Path(klasor) / kitap["dosya"]))
        for b in bolumler(kitap):
            bolum_pdf(belge, kitap, b, Path(klasor) / pdf_yolu(kitap, b))
            yazilan += 1
    return yazilan


# ---------------------------------------------------------------- komut
def ozet(dizin):
    print("| Kitap | Ad | Yayım | Bölüm | Kaynak |")
    print("| --- | --- | --- | --- | --- |")
    for k in sirali(dizin):
        print(f"| {k['kod']} | {kitap_adi(k)[:60]} | {k.get('yayim_tarihi') or '?'} | {len(bolumler(k))} | "
              f"{sum(len(b['kaynaklar']) for b in bolumler(k))} |")


def main():
    for akis in (sys.stdout, sys.stderr):
        akis.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="dizin.json → bölüm PDF'leri ve atif-dizini.xlsx")
    p.add_argument("dizin")
    p.add_argument("--yalniz-denetle", action="store_true", help="yalnız denetim ve özet; dosya yazmaz")
    p.add_argument("--kitap", help="bölüm PDF'lerini yalnız bu kodlu kitap için yaz (tablo her zaman hepsini taşır)")
    a = p.parse_args()
    dizin = dizin_oku(a.dizin)
    klasor = Path(a.dizin).resolve().parent
    hatalar, uyarilar = denetle(dizin, klasor)
    ozet(dizin)
    for u in uyarilar:
        print(f"⚠ {u}")
    for h in hatalar:
        print(f"✗ {h}")
    if a.yalniz_denetle or hatalar:
        print(f"\n{len(hatalar)} hata, {len(uyarilar)} uyarı." + (" Dosya yazılmadı: hataları dizin.json'da düzeltin."
                                                                 if hatalar else ""))
        return 1 if hatalar else 0
    xlsx_yaz(klasor / TABLO, tablo_sayfalari(dizin))
    yazilan = pdfleri_yaz(dizin, klasor, a.kitap)
    print(f"\nYazıldı: {klasor / TABLO} ve {yazilan} bölüm PDF'i ({klasor / 'pdf'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
