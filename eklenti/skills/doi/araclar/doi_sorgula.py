#!/usr/bin/env python3
"""Crossref'te durum sorgusu (doi skill'i): kayıttaki kitap ve bölüm DOI'leri kayıtlı mı, kitabın Crossref'teki
kaydında yeniden yüklemede kaybolacak bilgi var mı.

Yalnız okur: api.crossref.org'a GET isteği atar, başka adrese bağlanmaz, kimlik bilgisi kullanmaz, Crossref'e
bir şey yüklemez. Test sistemindeki (test.crossref.org) kayıtlar burada görünmez; onlar yönetim panelinden izlenir.

Kullanım:
  py doi_sorgula.py doi/kayit.json             durum tablosu ve karşılaştırma
  py doi_sorgula.py doi/kayit.json --doldur    kitabın kayıtta boş alanlarını Crossref'teki kayıttan doldur
                                               (özet, adres, ISBN, tarih, editör ORCID'leri; doluya dokunmaz)
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from doi_ortak import DOI, isbn_duz, kayit_oku, kayit_yaz, tr_kucuk  # noqa: E402

ADRES = "https://api.crossref.org/works/"  # izinli tek adres
TARAYICI = "yayinevi-dizgi-doi/1.2 (+https://github.com/ahmetmetintr/yayinevi-dizgi)"


def crossref_kaydi(doi):
    """(durum, kayıt): durum 'kayıtlı', 'yok' ya da 'hata: …'. DOI biçimi denetlenmeden istek atılmaz."""
    if not DOI.match(doi or ""):
        return "hata: DOI biçimi geçersiz", None
    istek = urllib.request.Request(ADRES + urllib.parse.quote(doi, safe="/"), headers={"User-Agent": TARAYICI})
    try:
        with urllib.request.urlopen(istek, timeout=20) as yanit:
            return "kayıtlı", json.loads(yanit.read().decode("utf-8"))["message"]
    except urllib.error.HTTPError as e:
        return ("yok", None) if e.code == 404 else (f"hata: HTTP {e.code}", None)
    except (urllib.error.URLError, TimeoutError) as e:
        return f"hata: bağlantı ({e})", None


def duz_ozet(jats):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", jats or "")).strip()


def karsilastir(kitap, cr):
    """Kayıt ile Crossref'teki kitap kaydının farkları: [(alan, açıklama)]."""
    farklar = []
    if (cr.get("title") or [""])[0].strip() != kitap.get("baslik", "").strip():
        farklar.append(("başlık", f"Crossref'te «{(cr.get('title') or [''])[0]}»"))
    if cr.get("abstract") and not kitap.get("ozet"):
        farklar.append(("özet", "Crossref'te özet var, kayıtta yok: yeniden yüklemede SİLİNİR (--doldur)"))
    adres = cr.get("resource", {}).get("primary", {}).get("URL")
    if adres and adres != kitap.get("adres"):
        farklar.append(("adres", f"Crossref'te {adres}"))
    cr_isbn = {isbn_duz(i) for i in cr.get("ISBN", [])}
    kayit_isbn = {isbn_duz(i) for i in (kitap.get("isbn_basili"), kitap.get("isbn_elektronik")) if i}
    if cr_isbn - kayit_isbn:
        farklar.append(("ISBN", f"Crossref'te {', '.join(sorted(cr_isbn - kayit_isbn))} var, kayıtta yok"))
    yazarlar = cr.get("author", [])
    if kitap.get("tur") == "editorlu" and yazarlar:
        farklar.append(("kişiler", f"Crossref'te kitap düzeyinde {len(yazarlar)} yazar var; bölümlerle yüklenince "
                                   "kitapta yalnız editörler kalır, yazarlar kendi bölümlerine geçer"))
    return farklar


def doldur(kitap, cr):
    """Kayıttaki boş kitap alanlarını Crossref kaydından doldurur; değişenlerin listesi."""
    degisen = []
    if not kitap.get("ozet") and cr.get("abstract"):
        kitap["ozet"] = duz_ozet(cr["abstract"])
        degisen.append("özet")
    adres = cr.get("resource", {}).get("primary", {}).get("URL")
    if adres and (not kitap.get("adres") or "[DOLDUR" in kitap["adres"]):
        kitap["adres"] = adres
        degisen.append("adres")
    for tur in cr.get("isbn-type", []):
        alan = "isbn_elektronik" if tur.get("type") == "electronic" else "isbn_basili"
        if not kitap.get(alan):
            kitap[alan] = tur.get("value", "")
            degisen.append(alan)
    parcalar = (cr.get("published") or {}).get("date-parts", [[]])[0]
    if parcalar and (not kitap.get("yayim_tarihi") or "[DOLDUR" in kitap["yayim_tarihi"]):
        kitap["yayim_tarihi"] = "-".join(f"{p:02d}" if i else str(p) for i, p in enumerate(parcalar))
        degisen.append("yayım tarihi")
    return degisen + orcid_doldur(kitap.get("kisiler", []), cr.get("editor", []))


def orcid_doldur(kisiler, cr_editorler):
    """ORCID'i boş editörlere, soyadı eşleşen Crossref editörünün ORCID'i."""
    orcidler = {tr_kucuk(e.get("family", "")): (e.get("ORCID") or "").rsplit("/", 1)[-1] for e in cr_editorler}
    degisen = []
    for kisi in kisiler:
        bulunan = orcidler.get(tr_kucuk(kisi.get("soyad", "")))
        if bulunan and not kisi.get("orcid"):
            kisi["orcid"] = bulunan
            degisen.append(f"ORCID ({kisi['soyad']})")
    return degisen


def main():
    for akis in (sys.stdout, sys.stderr):
        akis.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Crossref'te DOI durumu (yalnız okur)")
    p.add_argument("kayit", help="doi/kayit.json")
    p.add_argument("--doldur", action="store_true", help="kitabın boş alanlarını Crossref'teki kayıttan doldur")
    a = p.parse_args()
    kayit = kayit_oku(a.kayit)
    kitap = kayit["kitap"]
    durum, cr = crossref_kaydi(kitap.get("doi"))
    print("| DOI | Crossref'te |\n| --- | --- |")
    print(f"| {kitap.get('doi')} (kitap) | {durum} |")
    kayitli = 0
    for b in kayit.get("bolumler", []):
        b_durum, _ = crossref_kaydi(b.get("doi"))
        kayitli += b_durum == "kayıtlı"
        print(f"| {b.get('doi')} | {b_durum} |")
    print(f"\nBölümler: {kayitli}/{len(kayit.get('bolumler', []))} kayıtlı.")
    if cr is None:
        return 0 if durum == "yok" else 1
    for alan, ne in karsilastir(kitap, cr):
        print(f"⚠ {alan}: {ne}")
    if a.doldur:
        degisen = doldur(kitap, cr)
        kayit_yaz(a.kayit, kayit)
        print("Dolduruldu: " + (", ".join(degisen) if degisen else "boş alan yoktu"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
