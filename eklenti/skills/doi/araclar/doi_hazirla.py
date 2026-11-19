#!/usr/bin/env python3
"""DOI kayıt dosyasını hazırlar (doi skill'i): doi/kayit.json.

Eklentiyle dizilen kitapta: künye ve editörler kitap.typ'den; bölüm başlığı, yazar, kurum ve ORCID
metin/*.typ içindeki #bolum(...) satırlarından; sayfa aralıkları son PDF'in yer imleri ve basılı sayfa
numaralarından. Eklentiyle dizilmemiş kitapta (kitap.typ yoksa) yalnız PDF'ten: bölüm başlıkları ve sayfalar;
kitap ve kişi bilgileri [DOLDUR] kalır. Bilinmeyeni uydurmaz. Var olan kayıt dosyasının üzerine yazmaz.

Kullanım:
  py doi_hazirla.py <kitap klasörü> --pdf cikti/<kitap>.pdf --adres https://… [--tarih 2026-11-19]
     [--bolum-eki .ch{no}] [--cikti doi/kayit.json] [--uzerine-yaz]
Gerekli paket: pymupdf
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from doi_ortak import ad_ayir, doldur_yerleri, kayit_yaz, tr_kucuk, unvan_mi  # noqa: E402

ORCID_BUL = re.compile(r"\b\d{4}-\d{4}-\d{4}-\d{3}[\dX]\b")
EPOSTA_BUL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
KURUM = re.compile(r"Üniversite|University|Enstitü|Hastane|Bakanlığı|Müdürlüğü|Okulu|Lisesi|Kurumu|Vakfı|Akademi",
                   re.I)
AYLAR = ["ocak", "şubat", "mart", "nisan", "mayıs", "haziran", "temmuz", "ağustos", "eylül", "ekim", "kasım", "aralık"]
ON_SON = {"ön söz", "önsöz", "takdim", "takdim yazıları", "içindekiler", "katkıda bulunanlar", "dizin",
          "editörden", "kaynakça", "kaynaklar", "sunuş", "teşekkür", "yazarlar hakkında"}


def doldur(ne):
    return f"[DOLDUR: {ne}]"


def anahtar(baslik):
    """Typst başlığını PDF yer imiyle karşılaştırmak için: biçim işaretleri ve büyük/küçük harf yok sayılır."""
    return re.sub(r"\s+", " ", tr_kucuk(re.sub(r"[\\_*#~\[\]]", " ", baslik))).strip()


# ---------------------------------------------------------------- kitap.typ
def kunye_oku(metin):
    """kitap.typ'den başlık, editör/yazar satırı, yayınevi, profil ve künye satırları."""
    def alan(ad):
        e = re.search(rf'\b{ad}:\s*"([^"]*)"', metin)
        return e.group(1) if e and "[DOLDUR" not in e.group(1) else None
    profil = re.search(r"kitap\.with\(\s*\.\.([\w-]+)", metin)
    satirlar = {k: v for k, v in re.findall(r'\(\s*"([^"]+)"\s*,\s*"([^"]*)"\s*\)', metin) if "[DOLDUR" not in v}
    return {"baslik": alan("baslik"), "alt_baslik": alan("alt-baslik"), "yazar": alan("yazar"),
            "yayinevi": alan("yayinevi"), "profil": profil.group(1) if profil else None, "kunye": satirlar}


def kisi_listesi(yazar_satiri, rol, uyarilar):
    """'Editör: Doç. Dr. Ad SOYAD, Prof. Dr. Ad2 SOYAD2' → kişiler (unvanlar atılır)."""
    govde = re.sub(r"^\s*(Editör(ler)?|Ed\.|Yazar(lar)?)\s*:\s*", "", yazar_satiri or "", flags=re.I)
    kisiler = []
    for parca in re.split(r",|;|&| ve ", govde):
        if not parca.strip() or unvan_mi(parca.strip()):
            continue
        ad, soyad, emin = ad_ayir(parca)
        if not emin:
            uyarilar.append(f"«{parca.strip()}»: ad ve soyad ayrımı kesin değil (Ad SOYAD yazımı bekleniyordu)")
        kisiler.append({"ad": ad, "soyad": soyad, "rol": rol, "orcid": "", "kurum": "", "birim": ""})
    return kisiler


def tarih_ve_yer(baski, tarih):
    """'Ankara | Kasım 2026' → ('2026-11', 'Ankara'); --tarih verildiyse o kullanılır."""
    yer, _, zaman = (baski or "").partition("|")
    if not tarih:
        e = re.search(r"(\w+)\s+(\d{4})", zaman)
        ay = AYLAR.index(tr_kucuk(e.group(1))) + 1 if e and tr_kucuk(e.group(1)) in AYLAR else None
        tarih = f"{e.group(2)}-{ay:02d}" if e and ay else (e.group(2) if e else None)
    return tarih or doldur("yayım tarihi YYYY-AA-GG"), yer.strip()


# ---------------------------------------------------------------- metin/*.typ
def bolum_cagrilari(metin):
    """#bolum(...) çağrıları (dengeli parantezle): [(başlık, [(ad, bilgi)])]."""
    sonuc, i = [], metin.find("#bolum(")
    while i >= 0:
        j, derin = i + len("#bolum("), 1
        while j < len(metin) and derin:
            derin += {"(": 1, ")": -1}.get(metin[j], 0)
            j += 1
        govde = metin[i + len("#bolum("):j - 1]
        baslik = re.match(r"\s*\[([^\]]*)\]", govde)
        yazarlar = re.findall(r'\(\s*"([^"]+)"\s*,\s*\[([^\]]*)\]\s*\)', govde)
        sonuc.append((baslik.group(1) if baslik else "", yazarlar))
        i = metin.find("#bolum(", j)
    return sonuc


def yazar_bilgisi(ad, bilgi, uyarilar):
    """('Ayşe YILMAZ', 'Prof. Dr., Örnek Üniversitesi, Eğitim Fakültesi. ORCID: …, e-posta') → kişi."""
    bilgi = bilgi.replace("\\", "")
    orcid = ORCID_BUL.search(bilgi)
    kalan = EPOSTA_BUL.sub("", re.sub(r"ORCID\s*:?\s*\S*", "", ORCID_BUL.sub("", bilgi), flags=re.I))
    parcalar = [p.strip(" .;") for p in kalan.split(",")]
    parcalar = [p for p in parcalar if p and not unvan_mi(p)]
    kurum = next((p for p in parcalar if KURUM.search(p)), parcalar[0] if parcalar else "")
    birim = ", ".join(p for p in parcalar if p != kurum)
    a, soyad, emin = ad_ayir(ad)
    if not emin:
        uyarilar.append(f"«{ad}»: ad ve soyad ayrımı kesin değil (Ad SOYAD yazımı bekleniyordu)")
    return {"ad": a, "soyad": soyad, "rol": "yazar", "orcid": orcid.group() if orcid else "",
            "kurum": kurum, "birim": birim}


# ---------------------------------------------------------------- PDF
def pdf_bolumleri(pdf):
    """PDF'in birinci düzey yer imleri: [{baslik, ilk, son, etiketli}]. Sayfa no basılı numaradır (sayfa etiketi);
    bölümün son sayfası bir sonraki birinci düzey başlıktan önceki ilk dolu sayfadır (boş sayfa sayılmaz)."""
    import pymupdf
    belge = pymupdf.open(pdf)
    girdiler = [(baslik, sayfa - 1) for duzey, baslik, sayfa in belge.get_toc() if duzey == 1]
    dolu = [bool(belge[i].get_text().strip()) for i in range(len(belge))]

    def etiket(i):
        return belge[i].get_label() or str(i + 1)

    sonuc = []
    for k, (baslik, bas) in enumerate(girdiler):
        son = (girdiler[k + 1][1] if k + 1 < len(girdiler) else len(belge)) - 1
        while son > bas and not dolu[son]:
            son -= 1
        sonuc.append({"baslik": baslik.strip(), "ilk": etiket(bas), "son": etiket(son),
                      "etiketli": bool(belge[bas].get_label())})
    return sonuc


def bolumleri_esle(pdf_girdileri, typ_bolumleri, uyarilar):
    """PDF'teki sırayla bölümler; typ_bolumleri None ise (yalnız PDF) ön/son sayfalar dışındaki başlıklar."""
    bolumler = []
    for g in pdf_girdileri:
        if typ_bolumleri is None:
            if anahtar(g["baslik"]) not in ON_SON:
                bolumler.append((g, None))
            continue
        eslesen = [t for t in typ_bolumleri if anahtar(t[0]) == anahtar(g["baslik"])]
        if eslesen:
            bolumler.append((g, eslesen[0]))
        elif anahtar(g["baslik"]) not in ON_SON:
            uyarilar.append(f"PDF'teki «{g['baslik']}» metinde #bolum olarak bulunamadı; bölüm sayılmadı")
    for t in typ_bolumleri or []:
        if not any(e[1] is t for e in bolumler):
            uyarilar.append(f"metindeki «{t[0]}» bölümü PDF yer imlerinde yok (PDF eski mi?)")
    if any(not g["etiketli"] for g, _ in bolumler):
        uyarilar.append("PDF'te sayfa etiketi yok: sayfa numaraları fiziksel sayfa; basılı numarayla karşılaştırın")
    return bolumler


# ---------------------------------------------------------------- kayıt
def kayit_kur(klasor, pdf, adres, tarih, bolum_eki, uyarilar):
    kitap_typ = Path(klasor) / "kitap.typ"
    k = kunye_oku(kitap_typ.read_text(encoding="utf-8-sig")) if kitap_typ.exists() else {"kunye": {}}
    typ_bolumleri = None
    if kitap_typ.exists():
        typ_bolumleri = [c for m in sorted((Path(klasor) / "metin").glob("*.typ"))
                         for c in bolum_cagrilari(m.read_text(encoding="utf-8-sig"))]
    tur = "editorlu" if typ_bolumleri and any(y for _, y in typ_bolumleri) else (
        "telif" if kitap_typ.exists() else doldur("editorlu ya da telif"))
    kunye = k["kunye"]
    yayim, yer = tarih_ve_yer(kunye.get("Baskı"), tarih)
    doi = kunye.get("DOI") or doldur("kitap DOI'si")
    kisiler = kisi_listesi(k.get("yazar"), "editor" if tur == "editorlu" else "yazar", uyarilar)
    kitap = {"tur": tur, "baslik": k.get("baslik") or doldur("kitap adı"), "alt_baslik": k.get("alt_baslik") or "",
             "doi": doi, "adres": adres or doldur("kitabın sitedeki sayfası, https://…"),
             "isbn_basili": kunye.get("ISBN", ""), "isbn_elektronik": kunye.get("E-ISBN", ""),
             "yayim_tarihi": yayim, "basili": bool(kunye.get("ISBN")), "baski_no": 1, "ozet": "",
             "yayinevi": k.get("yayinevi") or doldur("yayınevi"), "yayin_yeri": yer, "dil": "tr",
             "kisiler": kisiler or [{"ad": "", "soyad": doldur("editör ya da yazar"), "rol": "editor",
                                     "orcid": "", "kurum": "", "birim": ""}]}
    bolumler = []
    for no, (g, t) in enumerate(bolumleri_esle(pdf_bolumleri(pdf), typ_bolumleri, uyarilar), 1):
        if t is not None:
            yazarlar = [yazar_bilgisi(ad, bilgi, uyarilar) for ad, bilgi in t[1]]
        else:
            yazarlar = [{"ad": "", "soyad": doldur("bölüm açılış sayfasından yazar"), "rol": "yazar",
                         "orcid": "", "kurum": "", "birim": ""}] if tur != "telif" else []
        bolumler.append({"no": no, "baslik": g["baslik"],
                         "doi": doi + bolum_eki.format(no=no) if "[DOLDUR" not in doi else doldur("bölüm DOI'si"),
                         "ilk_sayfa": g["ilk"], "son_sayfa": g["son"], "adres": "", "kisiler": yazarlar})
    yatiran = {"ad": kitap["yayinevi"], "eposta": doldur("Crossref bildirim e-postası (yayinevi.md)")}
    return {"yatiran": yatiran, "kitap": kitap, "bolumler": bolumler}


def main():
    for akis in (sys.stdout, sys.stderr):
        akis.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="DOI kayıt dosyasını hazırlar (doi/kayit.json)")
    p.add_argument("klasor", help="kitap klasörü (kitap.typ ve metin/ burada; yoksa yalnız PDF kullanılır)")
    p.add_argument("--pdf", required=True, help="kitabın son PDF'i (yer imleri ve sayfa numaraları buradan)")
    p.add_argument("--adres", help="kitabın sitedeki sayfası (bölüm DOI'leri de şimdilik buraya gider)")
    p.add_argument("--tarih", help="yayım tarihi YYYY-AA-GG (yoksa künyedeki Baskı satırından ay ve yıl)")
    p.add_argument("--bolum-eki", default=".ch{no}", help="bölüm DOI'si = kitap DOI'si + bu ek (varsayılan .ch{no})")
    p.add_argument("--cikti", help="varsayılan: <kitap klasörü>/doi/kayit.json")
    p.add_argument("--uzerine-yaz", action="store_true", help="var olan kayıt dosyasının üzerine yaz")
    a = p.parse_args()
    cikti = Path(a.cikti or Path(a.klasor) / "doi" / "kayit.json")
    if cikti.exists() and not a.uzerine_yaz:
        print(f"{cikti} zaten var; elle düzeltilmiş olabilir. Üzerine yazmak için --uzerine-yaz.")
        return 1
    uyarilar = []
    kayit = kayit_kur(a.klasor, a.pdf, a.adres, a.tarih, a.bolum_eki, uyarilar)
    kayit_yaz(cikti, kayit)
    print(f"Yazıldı: {cikti} · {len(kayit['bolumler'])} bölüm · tür {kayit['kitap']['tur']}")
    for b in kayit["bolumler"]:
        print(f"  {b['no']:>2}. {b['doi']} · s. {b['ilk_sayfa']}–{b['son_sayfa']} · {b['baslik'][:60]}")
    for u in uyarilar:
        print(f"⚠ {u}")
    eksik = doldur_yerleri(kayit)
    if eksik:
        print("Doldurulacak yerler:", ", ".join(eksik))
    print("Sonra: py doi_xml.py " + str(cikti))
    return 0


if __name__ == "__main__":
    sys.exit(main())
