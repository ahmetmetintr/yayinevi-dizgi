"""DOI becerisinin ortak yardımcıları: kayıt dosyası, sağlama haneleri, Türkçe ad biçimi.

doi_hazirla.py, doi_xml.py ve doi_sorgula.py bu modülü içe aktarır. Saat ve ağ kullanmaz; yalnız kayıt
dosyasını okur ve yazar. Kayıt dosyasının (doi/kayit.json) biçimi: sablon/kayit-ornegi.json.
"""
import json
import re
from pathlib import Path

DOLDUR = "[DOLDUR"
DOI = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$")
ORCID = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")
# Unvan kısaltması yalnız noktalıysa atılır ("Dr." atılır, "Dan" adı kalır); uzun unvan sözcükleri her zaman.
UNVAN_KISALTMA = re.compile(r"^(Prof|Doç|Dr|Öğr|Arş|Gör|Uzm|Psk|Dan|Lect|Assoc|Assist|Av|Ecz|Dt|Vet|Yrd|Ok)\.$", re.I)
UNVAN_SOZCUK = {"Üyesi", "Görevlisi", "Okutman", "Öğretmen", "Uzman", "Prof", "Doç", "Dr"}
ROLLER = {"editor": "editor", "yazar": "author"}


def kayit_oku(yol):
    return json.loads(Path(yol).read_text(encoding="utf-8-sig"))


def kayit_yaz(yol, kayit):
    Path(yol).parent.mkdir(parents=True, exist_ok=True)
    Path(yol).write_text(json.dumps(kayit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def tr_kucuk(metin):
    return metin.replace("I", "ı").replace("İ", "i").lower()


def tr_buyuk(metin):
    return metin.replace("i", "İ").replace("ı", "I").upper()


def bas_harf(sozcuk):
    """'YILMAZ' → 'Yılmaz', 'ÖZ-KAYA' → 'Öz-Kaya' (Türkçe i/İ, ı/I korunur)."""
    return "-".join(tr_buyuk(p[:1]) + tr_kucuk(p[1:]) for p in sozcuk.split("-"))


def buyuk_mu(sozcuk):
    harfler = [h for h in sozcuk if h.isalpha()]
    return len(harfler) >= 2 and all(h == tr_buyuk(h) for h in harfler)


def unvan_mi(parca):
    """'Prof. Dr.', 'Dr. Öğr. Üyesi' gibi yalnız unvandan oluşan parça mı."""
    sozcukler = parca.split()
    return bool(sozcukler) and all(UNVAN_KISALTMA.match(s) or s.rstrip(".") in UNVAN_SOZCUK for s in sozcukler)


def ad_ayir(tam_ad):
    """'Ad SOYAD' yazımından (ad, soyad, emin_mi). Sondaki büyük harfli sözcükler soyaddır; unvan atılır."""
    sozcukler = [s for s in tam_ad.replace(",", " ").split()
                 if not UNVAN_KISALTMA.match(s) and s.rstrip(".") not in UNVAN_SOZCUK]
    if not sozcukler:
        return "", "", False
    soyad = []
    while sozcukler and buyuk_mu(sozcukler[-1]):
        soyad.insert(0, sozcukler.pop())
    if not soyad or not sozcukler:  # ad da büyük yazılmış ya da hiç büyük yok: son sözcük soyad
        butun = (sozcukler + soyad)
        return " ".join(bas_harf(s) if buyuk_mu(s) else s for s in butun[:-1]), bas_harf(butun[-1]), False
    return " ".join(sozcukler), " ".join(bas_harf(s) for s in soyad), True


def orcid_gecerli(numara):
    """ORCID sağlama hanesi (ISO 7064 11,2)."""
    if not ORCID.match(numara or ""):
        return False
    rakamlar, toplam = numara.replace("-", ""), 0
    for r in rakamlar[:-1]:
        toplam = (toplam + int(r)) * 2
    sonuc = (12 - toplam % 11) % 11
    return rakamlar[-1] == ("X" if sonuc == 10 else str(sonuc))


def isbn_gecerli(isbn):
    """ISBN-13 ya da ISBN-10 sağlama hanesi; tire ve boşluk yok sayılır."""
    r = re.sub(r"[\s-]", "", isbn or "")
    if re.fullmatch(r"97[89]\d{10}", r):
        return sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(r)) % 10 == 0
    if re.fullmatch(r"\d{9}[\dX]", r):
        return sum((10 - i) * (10 if c == "X" else int(c)) for i, c in enumerate(r)) % 11 == 0
    return False


def isbn_duz(isbn):
    return re.sub(r"[\s-]", "", isbn or "")


def doldur_yerleri(deger, yol="kayıt"):
    """Kayıtta '[DOLDUR' kalan yerlerin yolları."""
    if isinstance(deger, dict):
        return [y for k, v in deger.items() for y in doldur_yerleri(v, f"{yol}.{k}")]
    if isinstance(deger, list):
        return [y for i, v in enumerate(deger) for y in doldur_yerleri(v, f"{yol}[{i}]")]
    return [yol] if isinstance(deger, str) and DOLDUR in deger else []
