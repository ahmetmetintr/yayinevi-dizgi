"""Kitabın yapısı (atıf dizini skill'i): künye alanları, üst ve alt bilgi, basılı sayfa numarası, PDF yer
imlerinden bölüm aralıkları, bölüm açılış sayfasından başlık ve yazarlar, yayım dönemi.

Saf modül: PDF, dosya, saat ve ağ kullanmaz. Satır biçimi atif_kaynakca.py'deki gibidir; ek olarak "h" sayfanın
yüksekliğidir (pt). Sayfa numaraları 1 tabanlı fiziksel sayfadır; basılı numara ayrıca hesaplanır.
"""
import re

from atif_ortak import AYLAR, ON_SON, anahtar, kaynakca_basligi_mi, tr_kucuk

KENAR = 0.10  # sayfanın üst ve alt %10'u: üst bilgi ve sayfa numarası bandı
ISBN_DEGER = r"(97[89](?:[ -]?\d){10}|\d(?:[ -]?\d){8}[ -]?[\dXx])"  # ISBN-13 ya da ISBN-10
BASKI = re.compile(r"^\s*(?:\d+\.\s*)?(?:Baskı|Basım|Yayın Tarihi|Yayım Tarihi)\s*[:：]?\s*(.+)$", re.I | re.M)
AY_YIL = re.compile(r"\b(" + "|".join(AYLAR) + r")\s+(\d{4})\b")
ETIKET = re.compile(r"^(?:\d+\.\s*)?(?:BÖLÜM|Bölüm|CHAPTER|Chapter)(?:\s+(?:\d+|[IVXLC]+))?\s*[.:]?$")
UNVAN = re.compile(r"^(?:Prof|Doç|Dr|Öğr|Arş|Gör|Uzm|Üyesi|Görevlisi|Psk|Dan|Lect|Assoc|Assist|Ph\.?D|Okt|Öğrt)\.?$",
                   re.I)
AD = re.compile(r"^(?:[A-ZÇĞİÖŞÜÂÎ](?:[a-zçğıöşüâîû'’-]+|\.)\.?\s*){1,3}(?:[A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜ'’-]+\s+){0,2}"
                r"[A-ZÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ'’-]+$")
DIPNOT_ISARETI = re.compile(r"[\s*†‡¹²³⁴⁵⁶⁷⁸⁹⁰\d,]+$")  # ad satırında: üst simge rakamlar da
ISARET = re.compile(r"[\s*†‡¹²³⁴⁵⁶⁷⁸⁹⁰]+$")  # başlıkta: rakamla biten başlık (COVID-19) korunur
KISIM = re.compile(r"^(?:kısım|part)\b")
EDITOR = re.compile(r"^\s*(Editör(?:ler)?|Ed\.|Yazar(?:lar)?|Hazırlayan(?:lar)?)\s*:?\s*(.+)$", re.I)


# ---------------------------------------------------------------- üst bilgi, alt bilgi, sayfa numarası
def ayni_satiri_birlestir(satirlar):
    """pymupdf bir satırı birkaç parça verebilir: aynı hizadaki yakın parçalar tek satır olur (sütunlar ayrı kalır)."""
    sonuc = []
    for s in satirlar:
        o = sonuc[-1] if sonuc else None
        if o and o["sayfa"] == s["sayfa"] and abs(o["y"] - s["y"]) < 1.5 and 0 <= s["x"] - o["x1"] < 2 * s["s"]:
            o["t"] = o["t"].rstrip() + " " + s["t"].lstrip() if s["x"] - o["x1"] > 1 else o["t"] + s["t"]
            o["x1"], o["s"] = s["x1"], max(o["s"], s["s"])
        else:
            sonuc.append(dict(s))
    return sonuc


def kenarda_mi(s):
    return s["y"] < KENAR * s["h"] or s["y"] > (1 - KENAR) * s["h"]


def kenar_anahtari(metin):
    return " ".join(re.sub(r"\d+", " ", tr_kucuk(metin)).split())


def sayfa_no_mu(metin):
    return bool(re.fullmatch(r"\s*[-–]?\s*(?:\d{1,4}|[ivxlcdm]{1,7})\s*[-–]?\s*", metin, re.I))


def kenar_kumesi(satirlar):
    """Üst ya da alt bantta en az üç sayfada yinelenen metinler (rakamlar yok sayılır): üst bilgi, alt bilgi."""
    sayfalar = {}
    for s in satirlar:
        if kenarda_mi(s) and not kaynakca_basligi_mi(s["t"]):
            sayfalar.setdefault(kenar_anahtari(s["t"]), set()).add(s["sayfa"])
    return {k for k, v in sayfalar.items() if k and len(v) >= 3}


def govde(satirlar, kume):
    """Üst bilgi, alt bilgi ve sayfa numarası atılmış satırlar."""
    return [s for s in satirlar if not (kenarda_mi(s) and not kaynakca_basligi_mi(s["t"])
                                        and (sayfa_no_mu(s["t"]) or kenar_anahtari(s["t"]) in kume))]


def basili_numara(etiket, sayfa_satirlari):
    """Basılı sayfa numarası: geçerli sayfa etiketi (rakam ya da Roma), yoksa alt (sonra üst) banttaki numara.
    Bulunamazsa None. (pymupdf 1.26 Typst PDF'lerinde etiketi 'ageLabel5' diye okur; o etiket geçersiz sayılır.)"""
    if etiket and re.fullmatch(r"\d+|[ivxlcdm]+", etiket, re.I):
        return etiket
    adaylar = sorted((s for s in sayfa_satirlari if kenarda_mi(s) and sayfa_no_mu(s["t"])), key=lambda s: -s["y"])
    return adaylar[0]["t"].strip(" -–") if adaylar else None


# ---------------------------------------------------------------- künye
def kunye_sayfasi_mi(metin):
    return "ISBN" in metin and bool(re.search(r"Sertifika|Copyright|©|Baskı|Basım|Yayıncı", metin, re.I))


def tarih_coz(metin):
    """'Ankara | Kasım 2026' → '2026-11'; yalnız yıl varsa '2026'; bulunamazsa ''."""
    e = AY_YIL.search(tr_kucuk(metin))
    if e:
        return f"{e.group(2)}-{AYLAR.index(e.group(1)) + 1:02d}"
    e = re.search(r"\b(19|20)\d{2}\b", metin)
    return e.group() if e else ""


def kunye_alanlari(metin):
    """Künye sayfasının metninden ISBN, E-ISBN, DOI, yayım tarihi ve yeri. Bulunamayan alan boş kalır."""
    duz = " ".join(metin.split())
    e_isbn = re.search(rf"(?:E-?ISBN|Elektronik ISBN|ISBN\s*\((?:e|PDF|elektronik)\))\s*[:：]?\s*{ISBN_DEGER}", duz,
                       re.I)
    isbn = re.search(rf"(?<![\w-])(?<!Elektronik )ISBN(?:-1[03])?(?!\s*\()\s*[:：]?\s*{ISBN_DEGER}", duz)
    doi = re.search(r"DOI\s*[:：]?\s*(?:https?://(?:dx\.)?doi\.org/)?(10\.\d{4,9}/\S+)", duz, re.I)
    baski = BASKI.search(metin)
    deger = baski.group(1).strip() if baski and "[DOLDUR" not in baski.group(1) else ""
    tarih = tarih_coz(deger) if deger else ""
    if not tarih:
        e = AY_YIL.search(tr_kucuk(duz))
        tarih = f"{e.group(2)}-{AYLAR.index(e.group(1)) + 1:02d}" if e else ""
    yer = next((p.strip() for p in re.split(r"[|,]", deger)
                if p.strip() and not re.search(r"\d", p) and tr_kucuk(p.strip()) not in AYLAR), "")
    return {"isbn": isbn.group(1).strip().replace(" ", "") if isbn else "",
            "e_isbn": e_isbn.group(1).strip().replace(" ", "") if e_isbn else "",
            "doi": doi.group(1).rstrip(".,;") if doi else "", "yayim_tarihi": tarih, "yayin_yeri": yer}


def donemde_mi(tarih, donem):
    """donem: '2026', '2026-01' ya da '2026-01..2026-03'. Tarih yalnız yılsa ve dönem aylıysa karar verilemez: None."""
    bas, _, son = donem.partition("..")
    son = son or bas
    if not tarih:
        return None
    if len(tarih) == 4 and (len(bas) > 4 or len(son) > 4):
        return None if bas[:4] <= tarih <= son[:4] else False
    return bas <= tarih[:len(bas)] and tarih[:len(son)] <= son


def kitap_basligi(satirlar, govde_punto):
    """İç kapaktan (ilk dolu sayfa) başlık, alt başlık ve editör/yazar satırı."""
    if not satirlar:
        return "", "", ""
    en_buyuk = max(s["s"] for s in satirlar)
    baslik = [s for s in satirlar if s["s"] >= en_buyuk - 0.6]
    sonraki = [s for s in satirlar if s["y"] > baslik[-1]["y"] and not EDITOR.match(s["t"])]
    alt = sonraki[0]["t"].strip() if sonraki and sonraki[0]["s"] >= 1.1 * govde_punto else ""
    editor = next((EDITOR.match(s["t"]).group(2).strip() for s in satirlar if EDITOR.match(s["t"])), "")
    if not editor:  # telif kitapta yazar çoğu zaman etiketsizdir: 'Dr. Ahmet METİN'
        editor = next((s["t"].strip() for s in sonraki if kisiler(s["t"]) and all(ad_mi(p, False)
                                                                                for p in kisiler(s["t"]))), "")
    return " ".join(s["t"].strip() for s in baslik), alt, editor


def kisiler(satir):
    """'Doç. Dr. Ayşe YILMAZ, Prof. Dr. Ali KAYA' → ['Ayşe YILMAZ', 'Ali KAYA'] (unvanlar atılır)."""
    parcalar = re.split(r",|;|\s+ve\s+|\s+&\s+", re.sub(r"[*†‡¹²³⁴⁵⁶⁷⁸⁹⁰]+", "", satir))
    return [a for a in (" ".join(w for w in p.split() if not UNVAN.match(w)) for p in parcalar) if a]


# ---------------------------------------------------------------- bölümler
def baslik_temizle(baslik):
    """Yer imi başlığından baştaki bölüm numarası ve 'BÖLÜM 3' etiketi atılır: '1 Çocuklarda …' → 'Çocuklarda …'."""
    b = re.sub(r"^\s*(?:(?:\d+\.\s*)?(?:BÖLÜM|Bölüm|CHAPTER|Chapter)\s+(?:\d+|[IVXLC]+)\s*[.:–-]?\s*|\d{1,2}\.?\s+)", "",
               baslik.strip())
    return ISARET.sub("", b).strip()


def duzey_araliklari(toc, duzey, sayfa_sayisi):
    """Yer imlerinde bir düzeyin girdileri: [(başlık, ilk, son)]. Aynı sayfada başlayan girdiler birleşir
    ('BÖLÜM 2' + 'Tarihsel Geçmiş:' + 'Rousseau'dan …'); daha üst düzey girdiler (kısım) yalnız sınırdır."""
    girdiler = []
    for d, baslik, sayfa in toc:
        if d > duzey or sayfa < 1:
            continue
        b = baslik.strip()
        if girdiler and girdiler[-1][0] == duzey == d and girdiler[-1][2] == sayfa:
            onceki = girdiler[-1][1]
            if ETIKET.match(onceki):
                girdiler[-1][1] = b
            elif not ETIKET.match(b):
                girdiler[-1][1] = onceki + (" " if onceki.endswith((":", "-", "–")) else ": ") + b
            continue
        girdiler.append([d, b, sayfa])
    sonuc = []
    for k, (d, baslik, sayfa) in enumerate(girdiler):
        if d != duzey:
            continue
        son = next((g[2] - 1 for g in girdiler[k + 1:] if g[2] > sayfa), sayfa_sayisi)
        sonuc.append((baslik, sayfa, max(son, sayfa)))
    return sonuc


def bolum_araliklari(toc, sayfa_sayisi, kaynakca_basliklari):
    """Yer imlerinden bölümler: [(başlık, ilk, son)]. kaynakca_basliklari: her kaynakça başlığının sayfası (bir
    sayfada iki başlık varsa iki kez). Bölüm düzeyi, girdilerinin çoğunda (≥ %60) kaynakça bulunan ve en az yarısında
    tam bir kaynakça bulunan en üst düzeydir: kısım düzeyinde her girdi birkaç kaynakça taşır, alt başlık düzeyinde
    çoğu girdi kaynakçasızdır. Hiçbir düzey uymazsa puanı en yüksek düzey (kaynakçalı girdi − fazladan kaynakça −
    kaynakçasız girdinin yarısı) seçilir; kaynakçalı girdi hiç yoksa boş liste döner."""
    adaylar = []
    for duzey in sorted({d for d, _, _ in toc if d <= 3}):
        araliklar = [a for a in duzey_araliklari(toc, duzey, sayfa_sayisi) if anahtar(a[0]) not in ON_SON]
        sayilar = [sum(1 for k in kaynakca_basliklari if i <= k <= s) for _, i, s in araliklar]
        if not sayilar:
            continue
        dolu = sum(1 for n in sayilar if n)
        if dolu >= 0.6 * len(sayilar) and sayilar.count(1) >= 0.5 * len(sayilar):
            return araliklar
        puan = dolu - sum(n - 1 for n in sayilar if n > 1) - 0.5 * sayilar.count(0)
        adaylar.append((puan, -duzey, araliklar))
    en_iyi = max(adaylar, key=lambda a: a[:2], default=None)
    return en_iyi[2] if en_iyi and en_iyi[0] > 0 else []


def yer_imi_baslari(toc, sayfa_sayisi, kunye_no):
    """Yer imlerinin 1. düzeyinden bölüm başları: künyeden sonra, ön/son sayfa ve kısım sayfası olmayan girdiler."""
    return [i for b, i, _ in duzey_araliklari(toc, 1, sayfa_sayisi)
            if i > kunye_no and anahtar(b) not in ON_SON and not KISIM.match(anahtar(b))]


def kitap_birimi(baslar, kaynakca_basliklari):
    """Telif kitapta kaynakça kitabın sonunda tektir: en az üç bölüm başı varken bütün kaynakça başlıkları son
    bölümün içindeyse kitap tek birim sayılır; ilk bölümün başladığı sayfa döner. Değilse None."""
    if len(baslar) >= 3 and kaynakca_basliklari and min(kaynakca_basliklari) >= baslar[-1]:
        return baslar[0]
    return None


def bolum_baslari_tahmini(ozetler, govde_punto, kunye_no):
    """Yer imi yoksa bölüm başları: ilk satırı gövdeden belirgin büyük (≥ 1,15 kat) olan sayfalar.
    ozetler: [(sayfa, ilk satırın metni, punto'su)]. Ön ve son sayfalar ile kaynakça sayfaları sayılmaz."""
    return [no for no, ilk, punto in ozetler
            if no > kunye_no and ilk and punto >= 1.15 * govde_punto
            and anahtar(ilk) not in ON_SON and not kaynakca_basligi_mi(ilk)]


def ad_mi(parca, sag_yasli):
    sozcukler = [s for s in parca.split() if not UNVAN.match(s)]
    ad = " ".join(sozcukler)
    if not AD.match(ad):
        return False
    son = sozcukler[-1]
    return sag_yasli or (len(son) >= 2 and son == son.replace("i", "İ").upper())


def bolum_basi(satirlar):
    """Bölümün ilk sayfası (üst bilgisiz satırlar) → (başlık, [yazarlar]). Başlık en büyük puntolu üst satırlardır
    ('BÖLÜM 1' etiketi atlanır); yazarlar başlığın hemen altındaki 'Ad SOYAD' satırlarıdır (dipnot işaretsiz)."""
    satirlar = [s for s in satirlar if not ETIKET.match(s["t"].strip())]
    if not satirlar:
        return "", []
    en_buyuk = max(s["s"] for s in satirlar[:8])
    sol = min(s["x"] for s in satirlar)
    i, baslik = 0, []
    while i < len(satirlar) and not baslik and i < 8:
        if satirlar[i]["s"] >= en_buyuk - 0.6:
            while i < len(satirlar) and satirlar[i]["s"] >= en_buyuk - 0.6 and len(baslik) < 4:
                baslik.append(satirlar[i]["t"].strip())
                i += 1
        else:
            i += 1
    yazarlar = []
    for s in satirlar[i:i + 6]:
        metin = DIPNOT_ISARETI.sub("", s["t"]).strip()
        parcalar = [p.strip() for p in re.split(r",|;|\s+ve\s+|\s+&\s+", re.sub(r"[*†‡¹²³⁴⁵⁶⁷⁸⁹⁰]+", "", metin))]
        parcalar = [p for p in parcalar if p]
        if not parcalar or not all(ad_mi(p, s["x"] > sol + 20) for p in parcalar):
            break
        yazarlar += [" ".join(w for w in p.split() if not UNVAN.match(w)) for p in parcalar]
    return ISARET.sub("", " ".join(baslik)).strip(), yazarlar
