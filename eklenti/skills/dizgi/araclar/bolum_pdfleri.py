#!/usr/bin/env python3
"""Teslim PDF'leri (dizgi skill'i): kitabın jeneriği, her bölümün ayrı PDF'i ve atıf bülteni dosyası.

Sayfalar PDF'ten tahmin edilmez: şablon her derlemede kitabın haritasını bırakır (<dizgi-harita>, harita.typ:
jenerik, bölümlerin ilk ve son sayfası, kaynakça sayfaları, başlık ve yazarlar); araç onu Typst'ten okur.
  <Kitap>, Jenerik.pdf              ana metinden önceki sayfalar: iç kapak, künye, ön söz, içindekiler
  bolumler/<Yazar>, <Bölüm>.pdf     her bölüm; araya giren boş sayfa ve kısım sayfası katılmaz
  <Kitap>, Atıf bülteni.pdf         jenerik + her bölümün ilk sayfası ve kaynakçası (yer imli)

Kullanım (kitap klasöründe; PDF aynı kitap.typ'nin son derlemesi olmalı, sayfa sayısı denetlenir):
  py bolum_pdfleri.py kitap.typ cikti/kitap-2026-11-20.pdf
  py bolum_pdfleri.py kitap.typ cikti/kitap.pdf --cikti cikti/teslim --input e-kitap=evet
Gerekli: typst ve pymupdf
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

YASAK = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
EN_UZUN = 150  # Windows yol sınırı için dosya adı üst sınırı (uzantısız)


# --- Saf işlevler (testlenir) ----------------------------------------------------------------

def yazar_listesi(yazarlar):
    """["A", "B", "C"] → "A, B ve C"."""
    if len(yazarlar) < 2:
        return "".join(yazarlar)
    return ", ".join(yazarlar[:-1]) + " ve " + yazarlar[-1]


def dosya_adi(yazarlar, baslik):
    """Vizetek örneği: "Yazar İsmi, Bölüm Adı" (Windows'ta geçersiz karakterler atılır, uzunsa kısaltılır)."""
    ad = ", ".join(p for p in (yazar_listesi(yazarlar), baslik) if p)
    ad = " ".join(YASAK.sub(" ", ad).split()).rstrip(". ")
    return ad if len(ad) <= EN_UZUN else ad[:EN_UZUN - 1].rstrip(" ,") + "…"


def benzersiz(adlar):
    """Aynı ad iki kez çıkarsa ikincisine " (2)" eklenir."""
    goruldu, sonuc = {}, []
    for ad in adlar:
        goruldu[ad] = goruldu.get(ad, 0) + 1
        sonuc.append(ad if goruldu[ad] == 1 else f"{ad} ({goruldu[ad]})")
    return sonuc


def kaynakca_sayfalari(bolum):
    sayfalar = []
    for k in bolum["kaynakca"]:
        sayfalar += [s for s in range(k["ilk"], k["son"] + 1) if s not in sayfalar]
    return sayfalar


def bolum_etiketi(bolum):
    return f"{bolum['numara']}. Bölüm: {bolum['baslik']}" if bolum.get("numara") else bolum["baslik"]


def bulten_plani(harita, jenerik):
    """Atıf bülteni: [(sayfa, yer imi ya da None)]; yer imi (düzey, ad)."""
    plan = [(s, (1, "Jenerik") if i == 0 else None) for i, s in enumerate(jenerik)]
    for b in harita["bolumler"]:
        plan.append((b["ilk"], (1, bolum_etiketi(b))))
        plan += [(s, (2, "Kaynaklar") if i == 0 else None)
                 for i, s in enumerate(s for s in kaynakca_sayfalari(b) if s != b["ilk"])]
    return plan


def denetle(harita, sayfa_sayisi):
    """→ (hatalar, uyarılar). Hata varsa dosya yazılmaz."""
    hatalar, uyarilar = [], []
    if harita.get("sayfa-sayisi") != sayfa_sayisi:
        hatalar.append(f"PDF {sayfa_sayisi} sayfa, harita {harita.get('sayfa-sayisi')} sayfa: PDF bu kitap.typ'nin son "
                       "derlemesi değil. Kitabı yeniden derleyip tekrar çalıştırın.")
    if not harita.get("bolumler"):
        hatalar.append("haritada bölüm yok (numaralı bölüm ya da #bolum bulunamadı)")
    if harita.get("jenerik", {}).get("son", 0) < 1:
        uyarilar.append("jenerik boş: #ana-metin-baslat() içindekilerden sonra yazılmamış olabilir")
    for b in harita.get("bolumler", []):
        if not b["yazarlar"]:
            uyarilar.append(f"{bolum_etiketi(b)}: yazar yok (dosya adı yalnız başlıktan)")
        if not b["kaynakca"]:
            uyarilar.append(f"{bolum_etiketi(b)}: kaynakça yok (#kaynakca ile yazılmamış); bültende yalnız ilk sayfa")
    return hatalar, uyarilar


# --- Dış dünya: typst ve PDF -----------------------------------------------------------------

def harita_oku(kitap, kok=None, girdiler=()):
    """Haritayı Typst'ten okur: önce `typst eval` (0.14+), olmazsa eski `typst query` (0.13)."""
    ek = ["--root", str(Path(kok).resolve())] if kok else []
    for g in girdiler:
        ek += ["--input", g]
    ad = Path(kitap).name
    komutlar = (["typst", "eval", "query(<dizgi-harita>).first().value", "--in", ad, *ek],
                ["typst", "query", ad, "<dizgi-harita>", "--field", "value", "--one", *ek])
    for komut in komutlar:
        sonuc = subprocess.run(komut, cwd=Path(kitap).resolve().parent, capture_output=True, text=True, encoding="utf-8")
        if sonuc.returncode == 0:
            return json.loads(sonuc.stdout)
    sys.exit(f"Kitabın haritası okunamadı (şablon <dizgi-harita> bırakmıyorsa sablon/*.typ eski olabilir):\n{sonuc.stderr}")


def bos_mu(sayfa):
    return not sayfa.get_text().strip() and not sayfa.get_images() and not sayfa.get_drawings()


def pdf_yaz(kaynak, plan, yol, baslik, yazar, konu):
    """plan: [(sayfa, yer imi ya da None)] → yer imli PDF."""
    import pymupdf
    yeni, toc = pymupdf.open(), []
    for i, (sayfa, yer_imi) in enumerate(plan):
        yeni.insert_pdf(kaynak, from_page=sayfa - 1, to_page=sayfa - 1)
        if yer_imi:
            toc.append([yer_imi[0], yer_imi[1], i + 1])
    if toc and toc[0][0] != 1:
        toc[0][0] = 1
    yeni.set_toc(toc)
    yeni.set_metadata({"title": baslik, "author": yazar, "subject": konu, "creator": "Typst", "producer": "dizgi"})
    yol.parent.mkdir(parents=True, exist_ok=True)
    yeni.save(yol, garbage=3, deflate=True)
    return len(yeni)


def main():
    for akis in (sys.stdout, sys.stderr):
        akis.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Jenerik, bölüm PDF'leri ve atıf bülteni")
    p.add_argument("kitap", help="kitabın ana dosyası (kitap.typ)")
    p.add_argument("pdf", help="kitabın son derlenmiş PDF'i")
    p.add_argument("--cikti", help="çıktı klasörü (varsayılan: PDF'in yanında teslim/)")
    p.add_argument("--root", help="typst --root (şablon kitap klasörünün dışındaysa)")
    p.add_argument("--input", action="append", default=[], help="typst --input (derlemede verildiyse aynısı)")
    p.add_argument("--harita", help="hazır harita JSON'u (Typst çalıştırılmaz)")
    a = p.parse_args()
    try:
        import pymupdf
    except ImportError:
        sys.exit("pymupdf yüklü değil: py -m pip install pymupdf")
    harita = json.loads(Path(a.harita).read_text(encoding="utf-8")) if a.harita else harita_oku(a.kitap, a.root, a.input)
    kaynak = pymupdf.open(a.pdf)
    hatalar, uyarilar = denetle(harita, len(kaynak))
    for u in uyarilar:
        print(f"⚠ {u}")
    if hatalar:
        sys.exit("DURDU: " + " · ".join(hatalar))
    cikti = Path(a.cikti) if a.cikti else Path(a.pdf).parent / "teslim"
    kitap_adi = harita["baslik"]
    # Boş sayfalar (bölümü sağ sayfada açmak için eklenenler) jeneriğe girmez.
    jenerik = [s for s in range(harita["jenerik"]["ilk"], harita["jenerik"]["son"] + 1) if not bos_mu(kaynak[s - 1])]
    on = dosya_adi([], kitap_adi)
    satirlar = []
    if jenerik:
        n = pdf_yaz(kaynak, [(s, (1, "Jenerik") if i == 0 else None) for i, s in enumerate(jenerik)],
                    cikti / f"{on}, Jenerik.pdf", f"{kitap_adi} — Jenerik", harita["yazar"], kitap_adi)
        satirlar.append(("Jenerik", f"{on}, Jenerik.pdf", n))
    adlar = benzersiz([dosya_adi(b["yazarlar"], b["baslik"]) for b in harita["bolumler"]])
    for b, ad in zip(harita["bolumler"], adlar):
        plan = [(s, (1, b["baslik"]) if s == b["ilk"] else None) for s in range(b["ilk"], b["son"] + 1)]
        n = pdf_yaz(kaynak, plan, cikti / "bolumler" / f"{ad}.pdf", b["baslik"], yazar_listesi(b["yazarlar"]), kitap_adi)
        satirlar.append((bolum_etiketi(b)[:50], f"bolumler/{ad}.pdf", n))
    n = pdf_yaz(kaynak, bulten_plani(harita, jenerik), cikti / f"{on}, Atıf bülteni.pdf",
                f"{kitap_adi} — Atıf bülteni", harita["yazar"], "jenerik, bölümlerin ilk sayfası ve kaynakçası")
    satirlar.append(("Atıf bülteni", f"{on}, Atıf bülteni.pdf", n))
    print(f"| Parça | Dosya ({cikti}) | Sayfa |\n| --- | --- | --- |")
    for parca, dosya, sayfa in satirlar:
        print(f"| {parca} | {dosya} | {sayfa} |")
    print(f"✓ {len(satirlar)} dosya yazıldı.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
