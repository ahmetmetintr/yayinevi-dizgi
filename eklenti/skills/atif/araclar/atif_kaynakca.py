"""Kaynakça satırlarını tek tek kaynaklara ayırır ve her kaynağın alanlarını (ilk yazar, yıl, başlık, DOI) çıkarır.

Saf modül: PDF, dosya, saat ve ağ kullanmaz. Satır biçimi: {"sayfa": 1 tabanlı fiziksel sayfa, "x": sol kenar,
"y": üst kenar (pt), "s": punto, "t": metin}; atif_hazirla.py satırları PDF'ten okuyup buraya verir.

Kaynaklar satırın sol kenarından ayrılır: APA'nın asılı girintisinde kaynak sol kenarda başlar, devam satırları
içeridedir (ilk satır girintili düzende tersi). Girinti yoksa yazar kalıbı ve paragraf aralığı kullanılır.
"""
import re

from atif_ortak import anahtar, kaynakca_basligi_mi

GIRINTI = 4.0  # pt: sol kenardan bu kadar içeride başlayan satır girintili sayılır
NUMARALI = re.compile(r"^\s*(?:\[\d+\]|\d+[.)])\s+")
NUMARA = re.compile(r"^\s*(?:\[(\d{1,4})\]|(\d{1,4})[.)])\s*(?=\S)")
YAZAR_BASI = re.compile(r"^[A-ZÇĞİÖŞÜÂÎÛ][\w'’.\-]*(?:\s+[\w'’\-]+){0,3}\s*,\s*(?:[A-ZÇĞİÖŞÜ]\.|[A-ZÇĞİÖŞÜ][a-zçğıöşü]+)")
KURUM_BASI = re.compile(r"^[^()]{2,150}?\(\s*(?:\d{4}|t\.\s?y\.|n\.\s?d\.)")
URLIMSI = re.compile(r"https?://|www\.|doi\.org|^10\.\d{4,9}/|^doi:", re.I)
DOI = re.compile(r"10\.\d{4,9}/\S+")
APA = re.compile(r"^(?P<yazarlar>(?:[^()]|\([^()]*\))+?)\s*\((?P<yil>\d{4}[a-zçğ]?|t\.\s?y\.|n\.\s?d\.|baskıda|in press)"
                 r"(?:,[^)]*)?\)\s*\.?\s*(?P<kalan>.*)$", re.I)
YIL_PARANTEZ = re.compile(r"\((1[5-9]\d{2}|20\d{2})[a-z]?[,)]")
YIL = re.compile(r"(?<![\d/.])(1[5-9]\d{2}|20\d{2})(?!\d)")
ALT_BASLIK = re.compile(r"^(?:[\wçğıöşü]+\s+){0,3}(?:kaynaklar|kaynakları|kaynakça|eserler|yayınlar|belgeler|"
                        r"references|sources)$")
YALNIZ_ADRES = re.compile(r"(?:https?://|doi:\s*|10\.\d{4,9}/)\S+", re.I)
BITIS = re.compile(r"ek(?:ler)?(?:\s*[-–]?\s*\d+.*)?|yazar(?:lar)? hakkında|extended (?:abstract|summary)|"
                   r"genişletilmiş özet|summary|dizin")


def bitis_basligi_mi(metin):
    """Kaynakçadan sonra gelen başlık ('Ekler', 'Ek 1. …', 'Yazar Hakkında', 'Extended Abstract'): kaynakça biter."""
    return len(metin) < 80 and bool(BITIS.fullmatch(anahtar(metin)))


def alt_baslik_mi(metin):
    """'Türkçe Kaynaklar', 'İnternet Kaynakları' gibi kaynakçanın içindeki ara başlıklar."""
    a = anahtar(metin)
    return len(metin) < 50 and "(" not in metin and "," not in metin and bool(ALT_BASLIK.match(a))


def satir_araligi(satirlar):
    farklar = sorted(b["y"] - a["y"] for a, b in zip(satirlar, satirlar[1:])
                     if a["sayfa"] == b["sayfa"] and 0 < b["y"] - a["y"] < 40)
    return farklar[(len(farklar) - 1) // 2] if farklar else 0  # alt ortanca: paragraf aralıkları ortancayı büyütmesin


def basliyor_mu(metin):
    return bool(YAZAR_BASI.match(metin) or KURUM_BASI.match(metin) or NUMARALI.match(metin))


def bitti_mi(metin):
    m = metin.rstrip()
    return m.endswith((".", ")")) or bool(URLIMSI.search(m.rsplit(" ", 1)[-1]))


def url_devami(onceki, sonraki):
    """Önceki satır bir adresin (DOI, URL) içinde bittiyse sonraki satır boşluksuz eklenir."""
    son = onceki.rsplit(" ", 1)[-1]
    if not URLIMSI.search(son):
        return False
    ilk = sonraki.split(" ", 1)[0]
    if ilk.startswith("(") or re.fullmatch(r"[A-ZÇĞİÖŞÜ][a-zçğıöşü]+[.,:]?", ilk):
        return False
    return bool(re.search(r"[/._\-=?&%#\d]", ilk)) or son.endswith(("/", ".", "-", "_", "=", "?", "&"))


def birlestir(parcalar):
    """Satırları tek kaynağa birleştirir: yumuşak tire ve heceleme tiresi kalkar, bölünen adres ve sayfa aralığı
    ('1475–' + '1479.') boşluksuz birleşir."""
    metin = ""
    for p in (p.strip() for p in parcalar):
        if not p:
            continue
        if not metin:
            metin = p
        elif metin.endswith("­"):
            metin = metin[:-1] + p
        elif url_devami(metin, p):
            metin += p
        elif (re.search(r"\d[–—-]$", metin) and p[:1].isdigit()) or metin.endswith("—"):
            metin += p
        elif re.search(r"[^\W\d_]-$", metin) and p[:1].islower():
            metin = metin[:-1] + p
        else:
            metin += " " + p
    return " ".join(metin.replace("­", "").split())


def numara(metin):
    e = NUMARA.match(metin)
    return int(e.group(1) or e.group(2)) if e else None


def numarali_gruplar(satirlar):
    """Numaralı kaynakça (1., 2. … ya da [1], [2] …): yeni kaynak yalnız sıradaki numarayla başlayan satırdır
    (numaralar sağa hizalı dizilebildiği için girintiye bakılmaz). Numaralı değilse None."""
    ilk = numara(satirlar[0]["t"])
    if ilk is None or not any(numara(s["t"]) == ilk + 1 for s in satirlar[1:]):
        return None
    gruplar, beklenen = [], ilk
    for s in satirlar:
        if numara(s["t"]) == beklenen:
            gruplar.append([NUMARA.sub("", s["t"], count=1)])
            beklenen += 1
        else:
            gruplar[-1].append(s["t"])
    return gruplar


def girinti_gruplari(satirlar):
    sol = {}
    for s in satirlar:  # sol kenar tek ve çift sayfada ayrı (aynalı kenar boşluğu)
        sol[s["sayfa"] % 2] = min(sol.get(s["sayfa"] % 2, s["x"]), s["x"])

    def girintili(s):
        return s["x"] - sol[s["sayfa"] % 2] > GIRINTI

    girintili_duzen = any(girintili(s) for s in satirlar)
    ilk_girintili = girintili(satirlar[0])
    aralik = satir_araligi(satirlar)
    gruplar, onceki = [], None
    for s in satirlar:
        if onceki is None:
            yeni = True
        elif girintili_duzen:
            yeni = girintili(s) == ilk_girintili
        else:
            bosluk = s["sayfa"] == onceki["sayfa"] and aralik and s["y"] - onceki["y"] > 1.5 * aralik
            yeni = bool(bosluk) or (basliyor_mu(s["t"]) and bitti_mi(onceki["t"]))
        if yeni:
            gruplar.append([])
        gruplar[-1].append(s["t"])
        onceki = s
    return gruplar


def kaynaklara_ayir(satirlar):
    """Kaynakça başlığından sonraki satırlar → kaynak metinleri (sırayla)."""
    satirlar = [s for s in satirlar if s["t"].strip() and not alt_baslik_mi(s["t"])]
    if not satirlar:
        return []
    gruplar = numarali_gruplar(satirlar) or girinti_gruplari(satirlar)
    kaynaklar = []
    for k in (birlestir(g) for g in gruplar):
        if kaynaklar and YALNIZ_ADRES.fullmatch(k):  # kendi satırına düşmüş DOI/URL önceki kaynağındır
            kaynaklar[-1] += " " + k
        elif k:
            kaynaklar.append(k)
    return kaynaklar


def doi_bul(metin):
    e = DOI.search(metin)
    if not e:
        return ""
    d = e.group().rstrip(".,;")
    while d.endswith(")") and d.count("(") < d.count(")"):
        d = d[:-1]
    return d.rstrip(".,;")


def ilk_yazar(yazarlar):
    """'Kaya, M., & Demir, A.' → 'Kaya'; kurum yazarında kurumun adı."""
    parca = yazarlar.split(",")[0] if "," in yazarlar else yazarlar
    return parca.strip(" .")[:80]


def kaynak_alanlari(metin):
    """Kaynak metninden alanlar. APA biçimi tanınmazsa yalnız yıl ve DOI aranır; metin her zaman olduğu gibi kalır."""
    a = APA.match(metin)
    if a:
        kalan = a.group("kalan")
        b = re.match(r"(.+?[.?!])(?=\s|$)", kalan)
        baslik = (b.group(1) if b else kalan).strip().rstrip(".")
        return {"ilk_yazar": ilk_yazar(a.group("yazarlar")), "yil": a.group("yil"), "baslik": baslik,
                "doi": doi_bul(metin), "bicim": "APA"}
    y = YIL_PARANTEZ.search(metin) or YIL.search(metin)
    return {"ilk_yazar": ilk_yazar(metin.split(".")[0]), "yil": y.group(1) if y else "", "baslik": "",
            "doi": doi_bul(metin), "bicim": "tanınmadı"}


def kaynakca_parcalari(satirlar):
    """Bölümün (üst bilgisiz) satırları → her kaynakça başlığının altındaki satırlar. Kaynakça bir sonraki kaynakça
    başlığında, bitiş başlığında ('Ekler', 'Yazar Hakkında') ya da gövde puntosuna dönülünce biter (alt kısımlı
    bölümde her kısmın ayrı kaynakçası olabilir)."""
    parcalar = []
    for h in [i for i, s in enumerate(satirlar) if kaynakca_basligi_mi(s["t"])]:
        sonraki = satirlar[h + 1:]
        ilk_bes = sorted(s["s"] for s in [x for x in sonraki if not alt_baslik_mi(x["t"])][:5])
        olcu = ilk_bes[len(ilk_bes) // 2] if ilk_bes else 0  # kaynakçanın puntosu
        parca = []
        for s in sonraki:
            if kaynakca_basligi_mi(s["t"]) or bitis_basligi_mi(s["t"]):
                break
            if not alt_baslik_mi(s["t"]) and len(parca) >= 3 and s["s"] > olcu + 1.0:
                break
            parca.append(s)
        parcalar.append((satirlar[h]["sayfa"], parca))
    return parcalar


def bolum_kaynaklari(satirlar):
    """Bölümün satırları → (kaynak kayıtları [{no, metin, ilk_yazar, yil, baslik, doi, bicim}], kaynakça sayfaları).
    Kaynakça başlığı yoksa ([], [])."""
    metinler, sayfalar = [], set()
    for baslik_sayfasi, parca in kaynakca_parcalari(satirlar):
        metinler += kaynaklara_ayir(parca)
        sayfalar.update(range(baslik_sayfasi, (parca[-1]["sayfa"] if parca else baslik_sayfasi) + 1))
    return [dict(no=no, metin=m, **kaynak_alanlari(m)) for no, m in enumerate(metinler, 1)], sorted(sayfalar)
