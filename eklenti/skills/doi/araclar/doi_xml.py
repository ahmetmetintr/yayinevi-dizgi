#!/usr/bin/env python3
"""Crossref yükleme XML'i (doi skill'i): kayıt dosyasını denetler, onay tablosunu yazar, XML'i üretir.

Kitap ve bölümleri tek dosyada: <book> + book_metadata + her bölüme bir content_item (Crossref şeması 5.3.1).
Var olan bir kitaba bölüm eklemek de böyle yapılır: kitabın bütün kaydı bölümleriyle yeniden yüklenir.
Hata varsa XML yazılmaz. Ağa çıkmaz, Crossref'e kendisi yüklemez (yükleme yetkili kişinin işidir).

Kullanım:
  py doi_xml.py doi/kayit.json                    denetle, tabloyu göster, doi/crossref-<zaman>.xml yaz
  py doi_xml.py doi/kayit.json --yalniz-denetle   yalnız denetim ve tablo
"""
import argparse
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from doi_ortak import DOI, ROLLER, doldur_yerleri, isbn_duz, isbn_gecerli, kayit_oku, orcid_gecerli  # noqa: E402

SURUM = "5.3.1"
NS = f"http://www.crossref.org/schema/{SURUM}"
JATS = "http://www.ncbi.nlm.nih.gov/JATS1"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
SEMA = f"{NS} https://www.crossref.org/schemas/crossref{SURUM}.xsd"
KITAP_TURU = {"editorlu": "edited_book", "telif": "monograph"}
TARIH = re.compile(r"^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?$")
EPOSTA = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

for onek, ad in (("", NS), ("jats", JATS), ("xsi", XSI)):
    ET.register_namespace(onek, ad)


# ---------------------------------------------------------------- denetim
def kisi_denetle(kisi, yer, hatalar, uyarilar):
    if not (kisi.get("soyad") or "").strip():
        hatalar.append((yer, "soyad yok"))
    if kisi.get("rol") not in ROLLER:
        hatalar.append((yer, f"rol «{kisi.get('rol')}»: editor ya da yazar olmalı"))
    if kisi.get("orcid") and not orcid_gecerli(kisi["orcid"]):
        hatalar.append((yer, f"ORCID {kisi['orcid']}: biçim ya da sağlama hanesi tutmuyor"))
    if not kisi.get("orcid"):
        uyarilar.append((yer, f"{kisi.get('ad', '')} {kisi.get('soyad', '')}: ORCID yok"))


def kitap_denetle(kitap, hatalar, uyarilar):
    for alan in ("baslik", "doi", "adres", "yayim_tarihi", "yayinevi"):
        if not kitap.get(alan):
            hatalar.append(("kitap", f"{alan} boş"))
    if kitap.get("tur") not in KITAP_TURU:
        hatalar.append(("kitap", "tur: editorlu ya da telif olmalı"))
    if kitap.get("doi") and not DOI.match(kitap["doi"]):
        hatalar.append(("kitap", f"DOI biçimi geçersiz: {kitap['doi']}"))
    if kitap.get("adres") and not kitap["adres"].startswith("https://"):
        hatalar.append(("kitap", "adres https:// ile başlamalı"))
    if kitap.get("yayim_tarihi") and not TARIH.match(kitap["yayim_tarihi"]):
        hatalar.append(("kitap", "yayim_tarihi YYYY-AA-GG (ya da YYYY-AA, YYYY) olmalı"))
    isbnler = [kitap.get("isbn_basili"), kitap.get("isbn_elektronik")]
    if not any(isbnler):
        hatalar.append(("kitap", "en az bir ISBN gerekir (isbn_basili ya da isbn_elektronik)"))
    for isbn in filter(None, isbnler):
        if not isbn_gecerli(isbn):
            hatalar.append(("kitap", f"ISBN {isbn}: sağlama hanesi tutmuyor"))
    roller = {k.get("rol") for k in kitap.get("kisiler", [])}
    if kitap.get("tur") == "editorlu" and "editor" not in roller:
        hatalar.append(("kitap", "editörlü kitapta kitap düzeyinde en az bir editör olmalı"))
    if kitap.get("tur") == "editorlu" and "yazar" in roller:
        uyarilar.append(("kitap", "editörlü kitapta bölüm yazarları kitap düzeyine değil kendi bölümüne yazılır"))
    for i, kisi in enumerate(kitap.get("kisiler", [])):
        kisi_denetle(kisi, f"kitap · kişi {i + 1}", hatalar, uyarilar)
    if not kitap.get("ozet"):
        uyarilar.append(("kitap", "özet yok (kitap Crossref'te özetliyse yeniden yüklemede silinir)"))


def sayi(deger):
    return int(deger) if str(deger or "").isdigit() else None


def bolumleri_denetle(kayit, hatalar, uyarilar):
    kitap, bolumler = kayit.get("kitap", {}), kayit.get("bolumler", [])
    if not bolumler:
        hatalar.append(("bölümler", "hiç bölüm yok"))
    onek = (kitap.get("doi") or "").split("/")[0] + "/"
    gorulen, onceki_son = set(), None
    for i, b in enumerate(bolumler):
        yer = f"bölüm {b.get('no', i + 1)}"
        if b.get("no") != i + 1:
            hatalar.append((yer, f"no {b.get('no')}: bölümler 1'den sırayla numaralanmalı"))
        if not b.get("baslik"):
            hatalar.append((yer, "başlık boş"))
        doi = b.get("doi") or ""
        if not DOI.match(doi):
            hatalar.append((yer, f"DOI biçimi geçersiz: «{doi}»"))
        elif not doi.startswith(onek) or doi == kitap.get("doi"):
            hatalar.append((yer, f"DOI {doi}: kitapla aynı önekte olmalı ve kitap DOI'sinden farklı olmalı"))
        if doi in gorulen:
            hatalar.append((yer, f"DOI {doi} iki kez kullanılmış"))
        gorulen.add(doi)
        if b.get("adres") and not b["adres"].startswith("https://"):
            hatalar.append((yer, "adres https:// ile başlamalı"))
        ilk, son = sayi(b.get("ilk_sayfa")), sayi(b.get("son_sayfa"))
        if not b.get("ilk_sayfa"):
            uyarilar.append((yer, "sayfa aralığı yok"))
        elif ilk and son and son < ilk:
            hatalar.append((yer, f"son sayfa ({son}) ilk sayfadan ({ilk}) küçük"))
        elif ilk and onceki_son and ilk <= onceki_son:
            uyarilar.append((yer, f"ilk sayfa {ilk}, önceki bölümün son sayfasından ({onceki_son}) önce"))
        onceki_son = son or ilk or onceki_son
        kisiler = b.get("kisiler", [])
        if kitap.get("tur") == "editorlu" and not any(k.get("rol") == "yazar" for k in kisiler):
            hatalar.append((yer, "editörlü kitapta her bölümün en az bir yazarı olmalı"))
        for j, kisi in enumerate(kisiler):
            kisi_denetle(kisi, f"{yer} · kişi {j + 1}", hatalar, uyarilar)


def denetle(kayit):
    """(hatalar, uyarılar): her biri (yer, açıklama). Hata varsa XML üretilmez."""
    hatalar, uyarilar = [], []
    for yol in doldur_yerleri(kayit):
        hatalar.append((yol, "[DOLDUR] kalmış"))
    yatiran = kayit.get("yatiran", {})
    if not yatiran.get("ad"):
        hatalar.append(("yatıran", "ad boş (Crossref'e yükleyen yayınevi)"))
    if not EPOSTA.match(yatiran.get("eposta") or ""):
        hatalar.append(("yatıran", "e-posta geçersiz (yükleme sonucu bu adrese gelir)"))
    kitap_denetle(kayit.get("kitap", {}), hatalar, uyarilar)
    bolumleri_denetle(kayit, hatalar, uyarilar)
    return hatalar, uyarilar


# ---------------------------------------------------------------- XML
def alt(ust, ad, metin=None, **nitelik):
    oge = ET.SubElement(ust, f"{{{NS}}}{ad}", {k: str(v) for k, v in nitelik.items()})
    if metin is not None:
        oge.text = str(metin)
    return oge


def kisiler_ogesi(ust, kisiler):
    if not kisiler:
        return
    grup = alt(ust, "contributors")
    for i, kisi in enumerate(kisiler):
        p = alt(grup, "person_name", sequence="first" if i == 0 else "additional",
                contributor_role=ROLLER[kisi["rol"]])
        if kisi.get("ad"):
            alt(p, "given_name", kisi["ad"])
        alt(p, "surname", kisi["soyad"])
        if kisi.get("kurum"):
            kurum = alt(alt(p, "affiliations"), "institution")
            alt(kurum, "institution_name", kisi["kurum"])
            if kisi.get("birim"):
                alt(kurum, "institution_department", kisi["birim"])
        if kisi.get("orcid"):
            alt(p, "ORCID", f"https://orcid.org/{kisi['orcid']}")


def basliklar_ogesi(ust, baslik, alt_baslik=None):
    t = alt(ust, "titles")
    alt(t, "title", baslik)
    if alt_baslik:
        alt(t, "subtitle", alt_baslik)


def ozet_ogesi(ust, ozet):
    if ozet:
        ET.SubElement(ET.SubElement(ust, f"{{{JATS}}}abstract"), f"{{{JATS}}}p").text = ozet


def tarih_ogesi(ust, tarih, ortam):
    yil, ay, gun = TARIH.match(tarih).groups()
    d = alt(ust, "publication_date", media_type=ortam)
    if ay:
        alt(d, "month", ay)
    if gun:
        alt(d, "day", gun)
    alt(d, "year", yil)


def tarihler(ust, kitap):
    tarih_ogesi(ust, kitap["yayim_tarihi"], "online")
    if kitap.get("basili"):
        tarih_ogesi(ust, kitap["yayim_tarihi"], "print")


def doi_ogesi(ust, doi, adres):
    d = alt(ust, "doi_data")
    alt(d, "doi", doi)
    alt(d, "resource", adres)


def kitap_ogesi(govde, kitap):
    dil = kitap.get("dil", "tr")
    kitap_o = alt(govde, "book", book_type=KITAP_TURU[kitap["tur"]])
    m = alt(kitap_o, "book_metadata", language=dil)
    kisiler_ogesi(m, kitap.get("kisiler", []))
    basliklar_ogesi(m, kitap["baslik"], kitap.get("alt_baslik"))
    ozet_ogesi(m, kitap.get("ozet"))
    if kitap.get("baski_no"):
        alt(m, "edition_number", kitap["baski_no"])
    tarihler(m, kitap)
    if kitap.get("isbn_basili"):
        alt(m, "isbn", isbn_duz(kitap["isbn_basili"]), media_type="print")
    if kitap.get("isbn_elektronik"):
        alt(m, "isbn", isbn_duz(kitap["isbn_elektronik"]), media_type="electronic")
    yayinevi = alt(m, "publisher")
    alt(yayinevi, "publisher_name", kitap["yayinevi"])
    if kitap.get("yayin_yeri"):
        alt(yayinevi, "publisher_place", kitap["yayin_yeri"])
    doi_ogesi(m, kitap["doi"], kitap["adres"])
    return kitap_o, dil


def bolum_ogesi(kitap_o, kitap, b, dil):
    c = alt(kitap_o, "content_item", component_type="chapter", level_sequence_number=1,
            publication_type="full_text", language=dil)
    kisiler = b.get("kisiler") or (kitap.get("kisiler", []) if kitap["tur"] == "telif" else [])
    kisiler_ogesi(c, kisiler)
    basliklar_ogesi(c, b["baslik"], b.get("alt_baslik"))
    ozet_ogesi(c, b.get("ozet"))
    alt(c, "component_number", b["no"])
    tarihler(c, kitap)
    if b.get("ilk_sayfa"):
        s = alt(c, "pages")
        alt(s, "first_page", b["ilk_sayfa"])
        if b.get("son_sayfa"):
            alt(s, "last_page", b["son_sayfa"])
    doi_ogesi(c, b["doi"], b.get("adres") or kitap["adres"])


def xml_uret(kayit, damga):
    """Kayıttan Crossref XML metni. damga: YYYYAAGGSSDDSS (her yeni yüklemede büyümeli; Crossref eskisini reddeder)."""
    kitap, yatiran = kayit["kitap"], kayit["yatiran"]
    kok = ET.Element(f"{{{NS}}}doi_batch", {"version": SURUM, f"{{{XSI}}}schemaLocation": SEMA})
    bas = alt(kok, "head")
    alt(bas, "doi_batch_id", f"{kitap['doi'].split('/', 1)[1]}-{damga}"[:100])
    alt(bas, "timestamp", damga)
    yatiran_o = alt(bas, "depositor")
    alt(yatiran_o, "depositor_name", yatiran["ad"])
    alt(yatiran_o, "email_address", yatiran["eposta"])
    alt(bas, "registrant", kitap["yayinevi"])
    kitap_o, dil = kitap_ogesi(alt(kok, "body"), kitap)
    for b in kayit["bolumler"]:
        bolum_ogesi(kitap_o, kitap, b, dil)
    ET.indent(kok, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(kok, encoding="unicode") + "\n"


# ---------------------------------------------------------------- onay tablosu
def kisi_yazisi(kisi):
    orcid = (" (ORCID yok)" if not kisi.get("orcid")
             else " (ORCID ✓)" if orcid_gecerli(kisi["orcid"]) else " (ORCID hatalı)")
    return f"{kisi.get('ad', '')} {kisi.get('soyad', '')}".strip() + orcid


def tablo(kayit):
    """Yüklemeden önce kullanıcıya onaylatılan özet (Markdown)."""
    kitap, satirlar = kayit.get("kitap", {}), []
    tur = {"editorlu": "Editörlü kitap", "telif": "Telif kitap"}.get(kitap.get("tur"), "?")
    ozet = f"var ({len(kitap['ozet'])} karakter)" if kitap.get("ozet") else "yok"
    alt_baslik = f": {kitap['alt_baslik']}" if kitap.get("alt_baslik") else ""
    kisiler = "; ".join(f"{kisi_yazisi(k)} · {k.get('rol', '')}" for k in kitap.get("kisiler", []))
    satirlar += ["## Kitap", "", "| Alan | Değer |", "| --- | --- |",
                 f"| Başlık | {kitap.get('baslik', '')}{alt_baslik} |",
                 f"| DOI | {kitap.get('doi', '')} |", f"| Tür | {tur} |",
                 f"| ISBN | basılı {kitap.get('isbn_basili') or '—'} · elektronik {kitap.get('isbn_elektronik') or '—'} |",
                 f"| Yayım tarihi | {kitap.get('yayim_tarihi', '')} ({'basılı + ' if kitap.get('basili') else ''}çevrim içi) |",
                 f"| Adres | {kitap.get('adres', '')} |",
                 f"| Kişiler | {kisiler} |", f"| Özet | {ozet} |",
                 "", "## Bölümler", "", "| No | DOI | Bölüm | Yazarlar | Sayfa | Adres |",
                 "| --- | --- | --- | --- | --- | --- |"]
    for b in kayit.get("bolumler", []):
        sayfa = f"{b.get('ilk_sayfa') or '—'}–{b.get('son_sayfa') or '—'}"
        adres = "ayrı sayfa" if b.get("adres") else "kitap sayfası"
        yazarlar = "; ".join(kisi_yazisi(k) for k in b.get("kisiler", []))
        satirlar.append(f"| {b.get('no')} | {b.get('doi')} | {b.get('baslik')} | {yazarlar} | {sayfa} | {adres} |")
    return "\n".join(satirlar)


def main():
    for akis in (sys.stdout, sys.stderr):
        akis.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Crossref yükleme XML'i: denetim, onay tablosu, XML")
    p.add_argument("kayit", help="doi/kayit.json")
    p.add_argument("--cikti", help="XML dosyası (varsayılan: kayıt klasöründe crossref-<zaman>.xml)")
    p.add_argument("--yalniz-denetle", action="store_true", help="XML yazma; yalnız denetim ve tablo")
    a = p.parse_args()
    kayit = kayit_oku(a.kayit)
    print(tablo(kayit))
    hatalar, uyarilar = denetle(kayit)
    print()
    for yer, ne in hatalar:
        print(f"✗ {yer}: {ne}")
    for yer, ne in uyarilar:
        print(f"⚠ {yer}: {ne}")
    print(f"Sonuç: {len(hatalar)} hata, {len(uyarilar)} uyarı.")
    if hatalar:
        print("Hata varken XML yazılmaz. Kayıt dosyasını düzeltip yeniden çalıştırın.")
        return 1
    if a.yalniz_denetle:
        return 0
    damga = datetime.now().strftime("%Y%m%d%H%M%S")
    cikti = Path(a.cikti or Path(a.kayit).parent / f"crossref-{damga}.xml")
    metin = xml_uret(kayit, damga)
    ET.fromstring(metin.encode("utf-8"))  # iyi biçimli mi
    cikti.write_text(metin, encoding="utf-8")
    print(f"Yazıldı: {cikti} ({len(kayit['bolumler'])} bölüm, Crossref şeması {SURUM}).")
    print("Önce test sistemine (test.crossref.org) yükleyip sonucu görün; sonra asıl sisteme (doi.crossref.org).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
