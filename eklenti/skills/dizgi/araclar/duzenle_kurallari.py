"""Yayınevi düzeni kuralları (dizgi skill'i): saf işlevler, dosya açmaz; duzenle.py ve bolum_denetle.py kullanır.

Her kural (metin) → (yeni metin, değişiklikler, uyarılar) döndürür. Değişiklik: (satır, ne, önce, sonra).
Kurallar Typst yapısına dokunmaz: kod çağrılarının sonu tipografi.py'deki Tarayici ile bulunur.
  ozet    bölüm başındaki Özet/Abstract ve Anahtar Kelimeler/Keywords bloklarını çıkarır
  kunye   künyede (yazar dipnotları) e-postayı siler, ORCID yazımını "ORCID: 0000-0000-0000-0000" yapar
  baslik  tümü büyük GİRİŞ / SONUÇ / KAYNAKLAR → Giriş / Sonuç / Kaynaklar; kaynakça başlığı kitapta tek ad
  not     şekil ya da tablodan hemen sonraki "Not.", "Kaynak:" paragraflarını #notlu-sekil ile şekle bağlar
"""
import re

from kaynakca_denetle import tr_kucuk
from tipografi import Tarayici

BLOK_CAGRILARI = {"figure", "table", "bolum", "kaynakca", "block", "align", "kisim", "include", "import", "set",
                  "show", "let", "numarasiz", "icindekiler-sayfasi", "ana-metin-baslat", "sekil-notu",
                  "notlu-sekil", "kutu", "quote", "pagebreak", "v", "image", "metadata", "alt-grup", "tablo-puntosu"}
OZET_ADLARI = {"özet", "öz", "abstract", "summary"}
ANAHTAR = re.compile(r"(anahtar\s+(kelime|sözcük)ler|key\s?words)", re.I)
NOT_BASI = re.compile(r"(not|notlar|note|notes|kaynak|kaynaklar|kaynakça|source|sources|kısaltma|kısaltmalar|"
                      r"abbreviations?|açıklama|açıklamalar)\s*[.:]|(uyarlanmıştır|alıntılanmıştır)", re.I)
KAYNAKCA_ADLARI = {"kaynaklar", "kaynakça", "referanslar", "references", "yararlanılan kaynaklar", "kaynak listesi"}
STANDART_ADLAR = {"giriş": "Giriş", "sonuç": "Sonuç", "sonuçlar": "Sonuçlar", "kaynaklar": "Kaynaklar",
                  "kaynakça": "Kaynakça"}
NUMARA = r"(?:\\?\d+(?:\.\d+)*\.?\s+)?"
ORCID_NO = r"(\d{4}-\d{4}-\d{4}-\d{3}[\dXx])"
ORCID_ETIKET = r"\b[Oo][Rr][Cc][Iiİı][Dd]\b(?:\s*(?:[Ii][Dd]|[Nn][Oo]|[Nn]umaras[ıi]|[Nn]umber)\b)?\s*[:.]?\s*"
ORCID_ADRESLI = re.compile(rf"(?:{ORCID_ETIKET})?(?:#link\(\"https?://(?:www\.)?orcid\.org/{ORCID_NO}\"\)"
                           rf"(?:\[[^\]]*\])?|(?:https?:/\\?/)?(?:www\.)?orcid\.org/{ORCID_NO})")
ORCID_ETIKETLI = re.compile(ORCID_ETIKET + ORCID_NO)
EPOSTA_ADRES = r"(?:#link\(\"mailto:[^\"]+\"\)(?:\[[^\]]*\])?|(?:[\w.+\-]|\\_)+\\?@[\w\-]+(?:\.[\w\-]+)+)"
EPOSTA_ETIKET = r"(?:(?:e-?\s?posta|e-?\s?mail|email|mail|elektronik\s+posta|iletişim|yazışma\s+adresi)\s*(?:adresi)?\s*:?\s*)"
EPOSTA = re.compile(rf"[,;]?\s*(?:\(\s*{EPOSTA_ETIKET}?{EPOSTA_ADRES}\s*\)|{EPOSTA_ETIKET}?{EPOSTA_ADRES})", re.I)
KUNYE_IZI = re.compile(r"orc[iİı]d|(?:[\w.+\-]|\\_)+\\@[\w\-]+\.", re.I)


# --- Typst metnini bloklara ayırma ----------------------------------------------------------

def kod_sonu(metin, i):
    """metin[i] == '#': kod ifadesinin (çağrı, argümanlar, içerik blokları) bittiği konum."""
    return Tarayici(metin).kod_ifadesi(i)


def kacisli(metin, i):
    geri = 0
    while i - geri - 1 >= 0 and metin[i - geri - 1] == "\\":
        geri += 1
    return geri % 2 == 1


def cagrilar(metin, ad):
    """#ad(…) ya da #ad[…] çağrılarının (başlangıç, bitiş) aralıkları."""
    for e in re.finditer(rf"#{re.escape(ad)}(?=[(\[])", metin):
        if not kacisli(metin, e.start()):
            yield e.start(), kod_sonu(metin, e.start())


def satir_no(metin, i):
    return metin.count("\n", 0, i) + 1


def paragraf_sonu(metin, i):
    """Paragrafın bittiği konum: boş satır (kod ifadeleri ve kaçışlar atlanarak) ya da metin sonu."""
    j, n = i, len(metin)
    while j < n:
        c = metin[j]
        if c == "\\":
            j += 2
            continue
        if c == "#" and re.match(r"#[A-Za-z_(\[{]", metin[j:j + 2]):
            j = max(kod_sonu(metin, j), j + 1)
            continue
        if c == "\n" and re.match(r"\n[ \t]*(\n|$)", metin[j:]):
            return j
        j += 1
    return n


def bloklar(metin, bas=0, son=None):
    """[(başlangıç, bitiş, tür)]; tür: "baslik", "kod" (satırı kaplayan blok çağrısı) ya da "paragraf"."""
    son, sonuc, i = len(metin) if son is None else son, [], bas
    while i < son:
        bosluk = re.match(r"[ \t]*\n", metin[i:son])
        if bosluk:
            i += bosluk.end()
            continue
        if re.match(r"[ \t]*$", metin[i:son]):
            break
        satir_sonu = metin.find("\n", i)
        satir_sonu = son if satir_sonu < 0 or satir_sonu > son else satir_sonu
        satir = metin[i:satir_sonu].lstrip()
        girinti = len(metin[i:satir_sonu]) - len(satir)
        cagri = re.match(r"#([A-Za-z][\w\-]*)", satir)
        if re.match(r"=+\s", satir):
            sonuc.append((i, satir_sonu, "baslik"))
            i = satir_sonu
        elif cagri and cagri.group(1) in BLOK_CAGRILARI:
            k = max(kod_sonu(metin, i + girinti), satir_sonu if cagri.group(1) in {"import", "include", "set", "show", "let"} else 0)
            sonuc.append((i, min(k, son), "kod"))
            i = k
        else:
            k = min(paragraf_sonu(metin, i), son)
            sonuc.append((i, k, "paragraf"))
            i = k
    return sonuc


def duz_yazi(parca):
    """Başlık ya da paragrafın baştaki biçim kodları atılmış düz hâli (karşılaştırma için)."""
    s = re.sub(r"^=+\s*", "", parca.strip())
    s = re.sub(r"#(strong|emph|underline|text)(\([^)]*\))?\[", "", s)
    return re.sub(r"[\]*_\\]", "", s).strip()


def ad_anahtari(parca):
    """Başlık adını karşılaştırma anahtarına çevirir: numara ve noktalama atılır, Türkçe küçük harf."""
    return tr_kucuk(re.sub(r"^\d+(\.\d+)*\.?\s*", "", duz_yazi(parca))).strip(" .:")


def uygula(metin, duzeltmeler):
    """duzeltmeler: [(bas, son, yeni)] → yeni metin (çakışmayan aralıklar, sondan başa)."""
    for bas, son, yeni in sorted(duzeltmeler, key=lambda d: d[0], reverse=True):
        metin = metin[:bas] + yeni + metin[son:]
    return metin


def kisa(s, n=70):
    s = " ".join(s.split())
    return s if len(s) <= n else s[:n - 1] + "…"


def parca(metin, blok):
    return metin[blok[0]:blok[1]]


# --- ozet: bölüm başındaki özet ve anahtar kelimeler ----------------------------------------

def anahtar_mi(s):
    return bool(ANAHTAR.match(duz_yazi(s)))


def yalniz_etiket_mi(s):
    return bool(re.fullmatch(ANAHTAR.pattern + r"\s*[:.]?", duz_yazi(s), re.I))


def ozet_uzunlugu(metin, bl):
    """Bölüm başındaki özet bloklarının sayısı: 0 özet yok, None düzensiz (elle bakılır)."""
    k = 0
    while k < len(bl) and bl[k][2] != "kod" and ad_anahtari(parca(metin, bl[k])) in OZET_ADLARI:
        j = k + 1
        while j < len(bl) and bl[j][2] == "paragraf" and not anahtar_mi(parca(metin, bl[j])):
            j += 1
        anahtar_var = j < len(bl) and anahtar_mi(parca(metin, bl[j]))
        if j - k > 7 or (j == k + 1 and not anahtar_var):
            return None  # özet etiketinden hemen sonra başlık ya da çok uzun blok: yapı belirsiz
        while j < len(bl) and anahtar_mi(parca(metin, bl[j])):
            yalniz = yalniz_etiket_mi(parca(metin, bl[j]))
            j += 1
            if yalniz and j < len(bl) and bl[j][2] == "paragraf" and not anahtar_mi(parca(metin, bl[j])):
                j += 1
        k = j
    return k


def ozet_cikar(metin):
    duzeltmeler, degisiklikler, uyarilar = [], [], []
    bolumler = list(cagrilar(metin, "bolum"))
    for n, (_, bas) in enumerate(bolumler):
        son = bolumler[n + 1][0] if n + 1 < len(bolumler) else len(metin)
        bl = bloklar(metin, bas, son)[:14]
        k = ozet_uzunlugu(metin, bl)
        if k is None:
            uyarilar.append((satir_no(metin, bl[0][0]), "özet düzensiz, elle bakılmalı: etiketten hemen sonra başlık ya da çok uzun blok"))
        elif k:
            bitis = bl[k][0] if k < len(bl) else bl[k - 1][1]
            duzeltmeler.append((bl[0][0], bitis, ""))
            ilk = kisa(parca(metin, bl[0]), 30)
            degisiklikler.append((satir_no(metin, bl[0][0]), "özet", f"{ilk} … {k} blok", "(çıkarıldı)"))
        elif any(anahtar_mi(parca(metin, b)) for b in bl[:5]):
            uyarilar.append((satir_no(metin, bl[0][0]), "özet düzensiz, elle bakılmalı: anahtar kelimeler var, özet etiketi yok"))
    return uygula(metin, duzeltmeler), degisiklikler, uyarilar


# --- kunye: e-posta ve ORCID -----------------------------------------------------------------

def kunye_bolgeleri(metin):
    """Künyenin durduğu yerler: #bolum(…) çağrıları ve ORCID ya da e-posta taşıyan dipnotlar."""
    bolgeler = list(cagrilar(metin, "bolum"))
    for bas, son in cagrilar(metin, "footnote"):
        if KUNYE_IZI.search(metin[bas:son]) and not any(b <= bas < s for b, s in bolgeler):
            bolgeler.append((bas, son))
    return sorted(bolgeler)


def kunye_disarida(metin):
    """Künye bilgisi (ORCID, e-posta) dipnot ya da #bolum dışında: [(satır, parça)]."""
    bolgeler = kunye_bolgeleri(metin)
    return [(satir_no(metin, e.start()), kisa(metin[max(0, e.start() - 30):e.end() + 30], 60))
            for e in KUNYE_IZI.finditer(metin) if not any(b <= e.start() < s for b, s in bolgeler)
            and not metin.startswith("//", metin.rfind("\n", 0, e.start()) + 1)]


def kunye_duzelt(metin):
    duzeltmeler, degisiklikler = [], []
    for bas, son in kunye_bolgeleri(metin):
        eski, satir = metin[bas:son], satir_no(metin, bas)

        def orcid(e):
            yeni = f"ORCID: {next(g for g in e.groups() if g).upper()}"
            if e.group(0) != yeni:
                degisiklikler.append((satir, "ORCID", kisa(e.group(0), 60), yeni))
            return yeni

        def eposta(e):
            degisiklikler.append((satir, "e-posta", kisa(e.group(0).strip(" ,;"), 60), "(silindi)"))
            return ""

        yeni = ORCID_ETIKETLI.sub(orcid, ORCID_ADRESLI.sub(orcid, eski))
        silinmeden = yeni
        yeni = EPOSTA.sub(eposta, yeni)
        if yeni != silinmeden:  # silinen adresin bıraktığı "[, " ve ".." artığı
            yeni = re.sub(r"(?<!\.)\.\.(?!\.)", ".", re.sub(r"\[\s*[,;]\s*", "[", yeni))
        if yeni != eski:
            duzeltmeler.append((bas, son, yeni))
    return uygula(metin, duzeltmeler), degisiklikler, []


# --- baslik: Giriş / Sonuç / Kaynaklar ve kaynakça adı ---------------------------------------

def tr_buyuk(s):
    return s.replace("i", "İ").replace("ı", "I").upper()


def kaynakca_basliklari(metin):
    """[(bas, son, metin)]: #kaynakca(baslik: [X]) ve kaynakça adındaki başlık satırlarının ad kısmı."""
    sonuc = []
    for e in re.finditer(r"#kaynakca\(\s*baslik:\s*\[", metin):
        son = metin.find("]", e.end())
        sonuc.append((e.end(), son, metin[e.end():son]))
    for e in re.finditer(r"(?m)^=+[ \t]+(.+?)[ \t]*$", metin):
        if ad_anahtari(e.group(1)) in KAYNAKCA_ADLARI:
            sonuc.append((e.start(1), e.end(1), e.group(1)))
    return sonuc


def kaynakca_cogunlugu(metinler):
    """Kitapta en çok kullanılan kaynakça adı (Kaynaklar ya da Kaynakça); eşitlikte Kaynaklar."""
    sayac = {"kaynaklar": 0, "kaynakça": 0}
    for metin in metinler:
        sayac["kaynaklar"] += len(re.findall(r"#kaynakca\[", metin))
        for _, _, ad in kaynakca_basliklari(metin):
            anahtar = ad_anahtari(ad)
            if anahtar in sayac:
                sayac[anahtar] += 1
    return "Kaynakça" if sayac["kaynakça"] > sayac["kaynaklar"] else "Kaynaklar"


def baslik_duzelt(metin, kaynakca_adi="Kaynaklar"):
    duzeltmeler, degisiklikler, uyarilar = [], [], []
    kaynakca_yerleri = set()
    for bas, son, ad in kaynakca_basliklari(metin):
        kaynakca_yerleri.add(bas)
        if ad.strip() != kaynakca_adi:
            duzeltmeler.append((bas, son, kaynakca_adi))
            degisiklikler.append((satir_no(metin, bas), "kaynakça adı", kisa(ad, 40), kaynakca_adi))
    for e in re.finditer(r"(?m)^(=+)[ \t]+(" + NUMARA + r")(.+?)[ \t]*$", metin):
        if e.start(2) in kaynakca_yerleri:
            continue
        ad, duz = e.group(3), duz_yazi(e.group(3))
        anahtar = ad_anahtari(ad)
        if not re.search(r"[a-zçğıöşüA-ZÇĞİÖŞÜ]", duz) or duz != tr_buyuk(duz):
            continue
        if anahtar in STANDART_ADLAR:
            duzeltmeler.append((e.start(3), e.end(3), STANDART_ADLAR[anahtar]))
            degisiklikler.append((satir_no(metin, e.start()), "başlık", kisa(ad, 40), STANDART_ADLAR[anahtar]))
        elif len(e.group(1)) >= 2:
            uyarilar.append((satir_no(metin, e.start()), f"tümü büyük harf ara başlık: {kisa(duz, 50)}"))
    return uygula(metin, duzeltmeler), degisiklikler, uyarilar


# --- not: şekil ve tablo altı notları ---------------------------------------------------------

def not_bagla(metin):
    duzeltmeler, degisiklikler, uyarilar = [], [], []
    bl = bloklar(metin)
    for k, blok in enumerate(bl):
        girinti = len(parca(metin, blok)) - len(parca(metin, blok).lstrip())
        bas = blok[0] + girinti
        if blok[2] != "kod" or not metin.startswith("#figure(", bas):
            continue
        notlar = []
        for sonraki in bl[k + 1:]:
            if sonraki[2] != "paragraf" or not NOT_BASI.match(duz_yazi(parca(metin, sonraki))):
                break
            notlar.append(sonraki)
        if notlar:
            notu = metin[notlar[0][0]:notlar[-1][1]].strip()
            yeni = f"#notlu-sekil({metin[bas + 1:blok[1]]})[{notu}]"
            duzeltmeler.append((bas, notlar[-1][1], yeni))
            degisiklikler.append((satir_no(metin, notlar[0][0]), "not", kisa(notu, 50), "#notlu-sekil"))
    return uygula(metin, duzeltmeler), degisiklikler, uyarilar


# --- yalnız rapor: boşlukla dizilmiş tablo ----------------------------------------------------

def sahte_tablolar(metin):
    """"Tablo N." yazısı olan ama ardından tablo gelmeyen paragraflar: [(satır, parça)]. Kaynakta tablo
    boşluk ya da sekmeyle dizilmiştir (ör. eski .doc); tablo_kur.py ile gerçek tabloya çevrilir."""
    bl, sonuc = bloklar(metin), []
    for k, blok in enumerate(bl):
        yazi = duz_yazi(parca(metin, blok))
        if blok[2] != "paragraf" or not re.match(r"Tablo\s+\d+(\.\d+)*\s*[.:]", yazi):
            continue
        sonraki = parca(metin, bl[k + 1]).lstrip() if k + 1 < len(bl) else ""
        if not re.match(r"#(figure|table|align|tablo-puntosu|notlu-sekil)\b", sonraki):
            sonuc.append((satir_no(metin, blok[0]), kisa(yazi, 60)))
    return sonuc


KURALLAR = {"ozet": ozet_cikar, "kunye": kunye_duzelt, "baslik": baslik_duzelt, "not": not_bagla}
