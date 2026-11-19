#!/usr/bin/env python3
"""Düzeltmeleri okur (tashih skill'i): işaretli PDF, izli ya da yorumlu Word, düz liste.

Her işareti tek biçime çevirir: işlem (Değiştir / Sil / Ekle / Biçim / Not / Vurgu) · eski · yeni · bağlam ·
yer · yazar. Aynı yere konmuş çift işaretler (üstü çizili + ekleme imi) tek maddede birleşir.
El yazısı, çizim ve yorumsuz işaretlerin görüntüsü kaydedilir; onlara bakıp karar verilir.

Kullanım:
  py tashih_oku.py gelen/hoca.pdf gelen/hoca.docx --json tashih/tur-01/liste.json
Gerekli paket: pymupdf (PDF için)  ·  Word için ek paket gerekmez.
"""
import argparse
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
ISLEMLER = {"değiştir": "Değiştir", "sil": "Sil", "ekle": "Ekle", "biçim": "Biçim", "not": "Not"}
KOMUT = re.compile(r"^\s*(değiştir|sil|ekle|biçim|not)\s*:\s*", re.I)
ESKI_YENI = re.compile(r"[«\"“]\s*(.*?)\s*[»\"”]\s*(?:→|->|=>|yerine)\s*[«\"“]\s*(.*?)\s*[»\"”]", re.S)
TIRNAKLI = re.compile(r"[«\"“]\s*(.*?)\s*[»\"”]", re.S)
GORSEL_TURLER = {"Ink", "FreeText", "Stamp", "Square", "Circle", "Polygon", "PolyLine", "Line"}
METIN_TURLER = {"StrikeOut", "Highlight", "Underline", "Squiggly"}


def ayristir(yorum, tur="", isaretli=""):
    """Yorum metnini işlem, eski, yeni ve açıklamaya ayırır. Biçimsiz yorumda işaretin türüne bakar."""
    yorum = (yorum or "").strip()
    ilk, _, aciklama = yorum.partition("\n")
    k = KOMUT.match(ilk)
    islem = ISLEMLER.get(k.group(1).lower()) if k else None
    govde = ilk[k.end():] if k else ilk
    eski = yeni = ""
    ey = ESKI_YENI.search(govde)
    if ey:
        eski, yeni, islem = ey.group(1), ey.group(2), islem or "Değiştir"
    elif islem in ("Sil", "Ekle"):
        t = TIRNAKLI.search(govde)
        deger = t.group(1) if t else govde.strip()
        eski, yeni = (deger, "") if islem == "Sil" else ("", deger)
    if not islem:
        if tur == "StrikeOut" and not yorum:
            islem, eski = "Sil", isaretli
        elif tur == "Highlight" and not yorum:
            islem = "Vurgu"
        else:
            islem = "Not"
    if islem == "Sil" and not eski:
        eski = isaretli
    return {"islem": islem, "eski": eski, "yeni": yeni, "aciklama": aciklama.strip() if k or ey else yorum}


# --- PDF ------------------------------------------------------------------------------------

def _sozcukler(sayfa):
    return [s for s in sayfa.get_text("words", sort=True) if s[4].strip()]


def _birlestir_metin(sozcukler):
    metin = " ".join(sozcukler)
    return re.sub(r"(\w)- (\w)", r"\1\2", metin)  # satır sonu bölmesini kaldır


def pdf_baglam(sayfa, alan, sozcukler, genislik=6):
    import pymupdf
    kesisen = [i for i, s in enumerate(sozcukler) if pymupdf.Rect(s[:4]).intersects(alan)]
    if not kesisen:  # ekleme imi gibi dar işaretlerde en yakın sözcük
        merkez = (alan.tl + alan.br) / 2
        uzaklik = [abs(pymupdf.Rect(s[:4]).br - merkez) for s in sozcukler]
        kesisen = [min(range(len(sozcukler)), key=uzaklik.__getitem__)] if sozcukler else []
    if not kesisen:
        return "", ""
    i, j = kesisen[0], kesisen[-1]
    once = _birlestir_metin([s[4] for s in sozcukler[max(0, i - genislik):i]])
    sonra = _birlestir_metin([s[4] for s in sozcukler[j + 1:j + 1 + genislik]])
    return once, sonra


def pdf_isaretli(sayfa, isaret):
    import pymupdf
    kose = isaret.vertices or []
    parcalar = [sayfa.get_textbox(pymupdf.Quad(kose[i:i + 4]).rect).strip() for i in range(0, len(kose) - 3, 4)]
    metin = " ".join(p for p in parcalar if p) or sayfa.get_textbox(isaret.rect).strip()
    return _birlestir_metin(metin.split())


def pdf_oku(yol, gorsel_klasoru):
    import pymupdf
    belge = pymupdf.open(yol)
    maddeler = []
    for sayfa in belge:
        sozcukler = _sozcukler(sayfa)
        for isaret in sayfa.annots():
            tur = isaret.type[1]
            if tur in ("Popup", "Link", "Widget"):
                continue
            yorum = (isaret.info.get("content") or "").strip()
            isaretli = pdf_isaretli(sayfa, isaret) if tur in METIN_TURLER else ""
            once, sonra = pdf_baglam(sayfa, isaret.rect, sozcukler)
            madde = {"kaynak": Path(yol).name, "yer": f"s. {sayfa.number + 1}", "tur": tur,
                     "yazar": isaret.info.get("title", ""), "yorum": yorum, "isaretli": isaretli,
                     "once": once, "sonra": sonra, "alan": [round(x, 1) for x in isaret.rect]}
            madde.update(ayristir(yorum, tur, isaretli))
            if tur in GORSEL_TURLER or (not yorum and tur == "Caret"):
                gorsel_klasoru.mkdir(parents=True, exist_ok=True)
                kirp = (isaret.rect + (-60, -30, 60, 30)) & sayfa.rect
                ad = gorsel_klasoru / f"{Path(yol).stem}_s{sayfa.number + 1}_{len(maddeler) + 1}.png"
                sayfa.get_pixmap(clip=kirp, dpi=150).save(ad)
                madde["gorsel"] = str(ad)
            maddeler.append(madde)
    return ciftleri_birlestir(maddeler)


def ciftleri_birlestir(maddeler):
    """Aynı sayfada aynı yorumu taşıyan işaretleri (üstü çizili + ekleme imi) tek maddede toplar."""
    sonuc, gorulen = [], {}
    for m in maddeler:
        anahtar = (m["kaynak"], m["yer"], m["yorum"]) if m["yorum"] else None
        if anahtar and anahtar in gorulen:
            ilk = gorulen[anahtar]
            ilk["tur"] += "+" + m["tur"]
            ilk["isaretli"] = ilk["isaretli"] or m["isaretli"]
            continue
        if anahtar:
            gorulen[anahtar] = m
        sonuc.append(m)
    return sonuc


# --- Word -----------------------------------------------------------------------------------

def _parcalar(oge, durum, cikti):
    """Paragrafı belge sırasıyla gezer: (tür, metin) — tür: None, ins, del, ybas, yson."""
    etiket = oge.tag
    if etiket == W + "ins":
        durum = "ins"
    elif etiket == W + "del":
        durum = "del"
    if etiket == W + "t":
        cikti.append((durum, oge.text or ""))
    elif etiket == W + "delText":
        cikti.append(("del", oge.text or ""))
    elif etiket == W + "tab":
        cikti.append((durum, "\t"))
    elif etiket == W + "commentRangeStart":
        cikti.append(("ybas", oge.get(W + "id")))
    elif etiket == W + "commentRangeEnd":
        cikti.append(("yson", oge.get(W + "id")))
    for alt in oge:
        _parcalar(alt, durum, cikti)


def _capa(metin, sondan=True, sozcuk=2):
    parca = metin.split(" ")
    secilen = parca[-sozcuk - 1:] if sondan else parca[:sozcuk + 1]
    return " ".join(secilen)


def docx_oku(yol):
    with zipfile.ZipFile(yol) as z:
        govde = ET.fromstring(z.read("word/document.xml"))
        yorumlar = {}
        if "word/comments.xml" in z.namelist():
            for y in ET.fromstring(z.read("word/comments.xml")).iter(W + "comment"):
                metin = "\n".join("".join(t.text or "" for t in p.iter(W + "t")) for p in y.iter(W + "p"))
                yorumlar[y.get(W + "id")] = (y.get(W + "author", ""), metin.strip())
    maddeler, acik, onceki_paragraf = [], {}, ""
    for no, p in enumerate(govde.iter(W + "p"), 1):
        parcalar = []
        _parcalar(p, None, parcalar)
        normal, k = "", 0
        while k < len(parcalar):
            tur, metin = parcalar[k]
            if tur in ("ybas", "yson"):
                if tur == "ybas":
                    acik[metin] = ""
                elif metin in acik:
                    yazar, yorum = yorumlar.get(metin, ("", ""))
                    madde = {"kaynak": Path(yol).name, "yer": f"paragraf {no}", "tur": "Yorum", "yazar": yazar,
                             "yorum": yorum, "isaretli": acik.pop(metin).strip(), "once": "", "sonra": ""}
                    madde.update(ayristir(yorum, "Yorum", madde["isaretli"]))
                    maddeler.append(madde)
            elif tur in ("ins", "del"):
                silinen = eklenen = ""
                while k < len(parcalar) and parcalar[k][0] in ("ins", "del"):
                    if parcalar[k][0] == "del":
                        silinen += parcalar[k][1]
                    else:
                        eklenen += parcalar[k][1]
                    k += 1
                sonra = "".join(m for t, m in parcalar[k:] if t is None)
                maddeler.append(izli_madde(yol, no, normal, silinen, eklenen, sonra, onceki_paragraf))
                normal += eklenen
                for kimlik in acik:
                    acik[kimlik] += eklenen
                continue
            else:
                normal += metin
                for kimlik in acik:
                    acik[kimlik] += metin
            k += 1
        if normal.strip():
            onceki_paragraf = normal
    return maddeler


def izli_madde(yol, no, once, silinen, eklenen, sonra, onceki_paragraf=""):
    """İzli değişikliği doğrudan uygulanabilir Değiştir maddesine çevirir (eklemede çevre sözcükler çapa olur)."""
    once_capa, sonra_capa = _capa(once), _capa(sonra, sondan=False)
    if silinen and eklenen:
        islem, eski, yeni = "Değiştir", silinen, eklenen
    elif silinen:
        islem, eski, yeni = "Sil", silinen, ""
    else:
        islem = "Ekle"
        eski, yeni = (once_capa, once_capa + eklenen) if once_capa.strip() else (sonra_capa, eklenen + sonra_capa)
    return {"kaynak": Path(yol).name, "yer": f"paragraf {no}", "tur": "İzli değişiklik", "yazar": "",
            "yorum": "", "isaretli": silinen, "once": once[-60:], "sonra": sonra[:60],
            "islem": islem if islem != "Ekle" else "Değiştir", "eski": eski, "yeni": yeni,
            "aciklama": ("yeni paragraf; şu paragraftan sonra: …" + onceki_paragraf[-60:]) if not (once + sonra).strip()
            else ("izli ekleme; çevre sözcüklerle" if islem == "Ekle" else "")}


# --- Düz liste ve çıktı ---------------------------------------------------------------------

def liste_oku(yol):
    maddeler = []
    for no, satir in enumerate(Path(yol).read_text(encoding="utf-8-sig").splitlines(), 1):
        if satir.strip():
            madde = {"kaynak": Path(yol).name, "yer": f"satır {no}", "tur": "Liste", "yazar": "", "yorum": satir.strip(),
                     "isaretli": "", "once": "", "sonra": ""}
            madde.update(ayristir(satir))
            maddeler.append(madde)
    return maddeler


def kisalt(metin, n=48):
    metin = " ".join(str(metin).split())
    return metin if len(metin) <= n else metin[:n - 1] + "…"


def tablo(maddeler):
    print("| No | Yer | İşlem | Eski → Yeni / Yorum | Yazar |")
    print("| --- | --- | --- | --- | --- |")
    for m in maddeler:
        if m["islem"] in ("Değiştir", "Sil", "Ekle"):
            ozet = f"«{kisalt(m['eski'], 30)}» → «{kisalt(m['yeni'], 30)}»"
        else:
            ozet = kisalt(m["yorum"] or m["isaretli"] or "(görsele bak)")
        if m.get("gorsel"):
            ozet += " [görsel]"
        print(f"| {m['no']} | {m['kaynak']} {m['yer']} | {m['islem']} | {ozet.replace('|', '/')} | {kisalt(m['yazar'], 20)} |")


def main():
    for akis in (sys.stdout, sys.stderr):
        akis.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Düzeltmeleri oku: PDF işaretleri, Word izli değişiklik ve yorumları, liste")
    p.add_argument("dosyalar", nargs="+")
    p.add_argument("--json", help="maddelerin yazılacağı JSON (ör. tashih/tur-01/liste.json)")
    a = p.parse_args()
    gorsel = Path(a.json).parent / "gorsel" if a.json else Path("tashih-gorsel")
    maddeler = []
    for d in a.dosyalar:
        uzanti = Path(d).suffix.lower()
        if uzanti == ".pdf":
            maddeler += pdf_oku(d, gorsel)
        elif uzanti == ".docx":
            maddeler += docx_oku(d)
        elif uzanti in (".txt", ".md"):
            maddeler += liste_oku(d)
        else:
            print(f"Atlandı (desteklenmiyor): {d} — .doc ise Word'de .docx olarak kaydedin", file=sys.stderr)
    for i, m in enumerate(maddeler, 1):
        m["no"] = i
    tablo(maddeler)
    sayac = {}
    for m in maddeler:
        sayac[m["islem"]] = sayac.get(m["islem"], 0) + 1
    print("\nToplam: " + ", ".join(f"{k} {v}" for k, v in sorted(sayac.items(), key=lambda x: -x[1])) + f" · {len(maddeler)} madde")
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(maddeler, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"Yazıldı: {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
