#!/usr/bin/env python3
"""Türkçe tipografi düzeltici (dizgi skill'i).

Typst metin dosyasında yalnız noktalama ve boşluğu düzeltir. Harf ve rakam dizisi ya da
Typst yapı karakterleri değişirse dosyaya hiçbir şey yazmaz. Kod bölgelerine dokunmaz:
#işlev(...) argümanları, `ham metin`, $matematik$, yorumlar, <etiket>, @atıf, bağlantılar.

Kullanım:
  py tipografi.py metin.typ             kuru çalıştırma: yalnız rapor
  py tipografi.py metin.typ --uygula    metin.yedek.typ bırakır, dosyayı düzeltir
Seçenekler:
  --ara-cizgi en|em          ara söz çizgisi: – (varsayılan) ya da —
  --konusma-cizgisi em|en    satır başı konuşma çizgisi: — (varsayılan) ya da –
"""
import argparse
import re
import sys
from pathlib import Path

SURUM = "1.0"
KOD_ANAHTAR = {"set", "show", "let", "import", "include", "if", "for", "while", "context", "return"}
OZEL = re.compile(r"[\\`$<@#\[\]]|//|/\*|https?://")
URL = re.compile(r"https?://[^\s\]\)>]+")
ETIKET = re.compile(r"<[\w\-:.]+>")
ATIF = re.compile(r"@[\w\-:.]+")
TANIMLAYICI = re.compile(r"[A-Za-z_][\w\-]*")
YAPI = "#[]$<>@*_="


# --- 1. Metni yazı (düzeltilebilir) ve kod (dokunulmaz) parçalarına ayır ------------------

class Tarayici:
    def __init__(self, metin):
        self.m, self.n, self.parcalar = metin, len(metin), []

    def ekle(self, tur, s):
        if not s:
            return
        if self.parcalar and self.parcalar[-1][0] == tur:
            self.parcalar[-1] = (tur, self.parcalar[-1][1] + s)
        else:
            self.parcalar.append((tur, s))

    def dizgi_sonu(self, i):  # i: açılış tırnağı; kapanıştan sonraki konumu döndürür
        j = i + 1
        while j < self.n and self.m[j] != '"':
            j += 2 if self.m[j] == "\\" else 1
        return min(j + 1, self.n)

    def dengeli(self, i, satir_sonunda_dur=False):
        """Parantez, köşeli ve süslü ayraçları dengeleyerek kod bölgesinin sonunu bulur."""
        derinlik, j = 0, i
        while j < self.n:
            c = self.m[j]
            if c == '"':
                j = self.dizgi_sonu(j)
                continue
            if c in "([{":
                derinlik += 1
            elif c in ")]}":
                derinlik -= 1
                if derinlik <= 0 and not satir_sonunda_dur:
                    return j + 1
            elif c == "\n" and satir_sonunda_dur and derinlik <= 0:
                return j
            j += 1
        return self.n

    def argumanlar(self, i):  # i: "(" — köşeli ayraç içindeki yazı düzeltilir
        derinlik, j = 0, i
        while j < self.n:
            c = self.m[j]
            if c == '"':
                k = self.dizgi_sonu(j)
                self.ekle("kod", self.m[j:k])
                j = k
                continue
            if c == "[":
                self.ekle("kod", "[")
                j = self.yazi(j + 1, "]")
                if j < self.n:
                    self.ekle("kod", "]")
                    j += 1
                continue
            self.ekle("kod", c)
            derinlik += c == "("
            derinlik -= c == ")"
            j += 1
            if derinlik == 0:
                return j
        return j

    def kod_ifadesi(self, i):  # i: "#"
        j = i + 1
        if j < self.n and self.m[j] in "{(":
            k = self.dengeli(j)
            self.ekle("kod", self.m[i:k])
            return k
        t = TANIMLAYICI.match(self.m, j)
        if not t:
            self.ekle("kod", "#")
            return j
        if t.group() in KOD_ANAHTAR:
            k = self.dengeli(t.end(), satir_sonunda_dur=True)
            self.ekle("kod", self.m[i:k])
            return k
        self.ekle("kod", self.m[i:t.end()])
        j = t.end()
        while j < self.n:
            alan = TANIMLAYICI.match(self.m, j + 1) if self.m[j] == "." else None
            if alan:
                self.ekle("kod", self.m[j:alan.end()])
                j = alan.end()
            elif self.m[j] == "(":
                j = self.argumanlar(j)
            elif self.m[j] == "[":
                self.ekle("kod", "[")
                j = self.yazi(j + 1, "]")
                if j < self.n:
                    self.ekle("kod", "]")
                    j += 1
            else:
                break
        return j

    def yazi(self, i, kapanis=None):
        while i < self.n:
            o = OZEL.search(self.m, i)
            k = o.start() if o else self.n
            self.ekle("yazi", self.m[i:k])
            if not o:
                return self.n
            i, s = k, o.group()
            if s == kapanis:
                return i
            if s == "\\":
                bitis = self.m.find("}", i) + 1 if self.m.startswith("\\u{", i) else i + 2
                self.ekle("kod", self.m[i:bitis])
                i = bitis
            elif s == "//":
                bitis = self.m.find("\n", i)
                i = self._kod(i, self.n if bitis < 0 else bitis)
            elif s == "/*":
                bitis = self.m.find("*/", i + 2)
                i = self._kod(i, self.n if bitis < 0 else bitis + 2)
            elif s.startswith("http"):
                i = self._kod(i, URL.match(self.m, i).end())
            elif s == "`":
                tik = len(self.m[i:]) - len(self.m[i:].lstrip("`"))
                bitis = self.m.find("`" * tik, i + tik)
                i = self._kod(i, self.n if bitis < 0 else bitis + tik)
            elif s == "$":
                j = i + 1
                while j < self.n and self.m[j] != "$":
                    j += 2 if self.m[j] == "\\" else 1
                i = self._kod(i, min(j + 1, self.n))
            elif s in "<@":
                e = (ETIKET if s == "<" else ATIF).match(self.m, i)
                i = self._kod(i, e.end()) if e else self._yazi_karakteri(i)
            elif s == "#":
                i = self.kod_ifadesi(i)
            elif s == "[":
                self.ekle("kod", "[")
                i = self.yazi(i + 1, "]")
                if i < self.n:
                    self.ekle("kod", "]")
                    i += 1
            else:  # eşleşmeyen "]"
                i = self._yazi_karakteri(i)
        return i

    def _kod(self, i, bitis):
        self.ekle("kod", self.m[i:bitis])
        return bitis

    def _yazi_karakteri(self, i):
        self.ekle("yazi", self.m[i])
        return i + 1


# --- 2. Kurallar ---------------------------------------------------------------------------

def kurallar(ara, konusma):
    harf_once = r"(?:(?<=[^\W_])|(?<=%))"
    return [
        ("çift boşluk / sekme", r"(?<=\S)(?:[ \t]{2,}|\t)(?=\S)", " "),
        ("noktalamadan önce boşluk", r"(?<=[\w”’\"')])[ \t]+(?=[,;:!?…]|\.(?:\s|$))", ""),
        ("parantez içi boşluk", r"(?<=\()[ \t]+|[ \t]+(?=\))", ""),
        ("virgülden sonra boşluk yok", r"(?<=[,;])(?=[^\W\d_])", " "),
        ("üç nokta", r"(?<!\.)\.[ \t]?\.[ \t]?\.(?!\.)", "…"),
        ("kesme işareti", harf_once + r"[´‘′](?=[^\W\d_])", "’"),
        ("yanlış tırnak", r"«[ \t]*|[ \t]*»|[„‟″]", '"'),
        ("sayı aralığı çizgisi", r"(?<![\w\-–/])(?<!\d[.,])(\d{1,4})[ \t]?[-–][ \t]?(\d{1,4})(?![\w\-–/]|[.,]\d)", r"\1–\2"),
        ("ara söz çizgisi", r"(?<=\S)[ \t]+(?:-{1,3}|–|—)[ \t]+(?=\S)", f" {ara} "),
        ("yüzde işareti", r"%[ \t]+(?=\d)|(?<![\w%])(\d+(?:[.,]\d+)?)[ \t]?%(?![\w%])",
         lambda e: f"%{e.group(1)}" if e.group(1) else "%"),
        ("bölünmez boşluk: unvan", r"\b(Prof|Doç|Dr|Öğr|Gör|Arş|Uzm|Av|Op|Yrd|Sn)\.[ \t]*(?=[^\W\d_])", r"\1.~"),
        ("bölünmez boşluk: sayfa/no", r"\b(s|ss|bkz|c|no)\.[ \t]+(?=\d)", r"\1.~"),
        ("bölünmez boşluk: birim", r"(\d)[ \t]+(kg|g|mg|km|m|cm|mm|ml|lt|L|TL|°C|dk|sn|sa)(?![^\W_])", r"\1~\2"),
    ], [
        ("konuşma çizgisi", r"(?m)^([ \t]*)(?:\\-|–|—|-{2,3})[ \t]+(?=\S)", rf"\g<1>{konusma} "),
        ("kesme işareti", r"(?<=[^\W\d_])\\`(?=[^\W\d_])", "’"),
    ]


def uygula_kural(metin, ad, desen, yerine, sayac, ornekler, satir0=1):
    def degistir(e):
        yeni = yerine(e) if callable(yerine) else e.expand(yerine)
        if yeni != e.group():
            sayac[ad] = sayac.get(ad, 0) + 1
            if len(ornekler.setdefault(ad, [])) < 3:
                satir = satir0 + metin.count("\n", 0, e.start())
                once = metin[max(0, e.start() - 18):e.end() + 18].replace("\n", " ")
                ornekler[ad].append((satir, once, yeni))
        return yeni
    return re.sub(desen, degistir, metin)


def duzelt(metin, ara="–", konusma="—"):
    parca_kurallari, satir_kurallari = kurallar(ara, konusma)
    sayac, ornekler = {}, {}
    on = metin
    for ad, desen, yerine in satir_kurallari:  # yalnız kod satırı olmayan satırlarda
        on = "".join(
            satir if satir.lstrip().startswith(("#", "//"))
            else uygula_kural(satir, ad, desen, yerine, sayac, ornekler, no)
            for no, satir in enumerate(on.splitlines(keepends=True), 1)
        )
    t = Tarayici(on)
    t.yazi(0)
    cikti, satir = [], 1
    for tur, s in t.parcalar:
        if tur == "yazi":
            for ad, desen, yerine in parca_kurallari:
                s = uygula_kural(s, ad, desen, yerine, sayac, ornekler, satir)
        satir += s.count("\n")
        cikti.append(s)
    return "".join(cikti), sayac, ornekler


def dogrula(once, sonra):
    harf = lambda s: [c for c in s if c.isalnum()]
    yapi = lambda s: {c: s.count(c) for c in YAPI}
    return harf(once) == harf(sonra), yapi(once) == yapi(sonra)


# --- 3. Komut satırı -----------------------------------------------------------------------

def main():
    for akis in (sys.stdout, sys.stderr):  # Windows konsolunda Türkçe ve ✓ için
        akis.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Türkçe tipografi düzeltici (Typst metin dosyaları)")
    p.add_argument("dosya", nargs="?")
    p.add_argument("--uygula", action="store_true", help="düzeltmeyi dosyaya yaz (yedek bırakır)")
    p.add_argument("--ara-cizgi", choices=["en", "em"], default="en")
    p.add_argument("--konusma-cizgisi", choices=["em", "en"], default="em")
    p.add_argument("--surum", action="store_true")
    a = p.parse_args()
    if a.surum:
        print(f"tipografi.py {SURUM}")
        return 0
    if not a.dosya:
        p.error("dosya gerekli")
    yol = Path(a.dosya)
    ham = yol.read_bytes()
    bom = ham.startswith(b"\xef\xbb\xbf")
    once = ham.decode("utf-8-sig")
    cizgi = {"en": "–", "em": "—"}
    sonra, sayac, ornekler = duzelt(once, cizgi[a.ara_cizgi], cizgi[a.konusma_cizgisi])
    harf_ayni, yapi_ayni = dogrula(once, sonra)

    print(f"Tipografi raporu: {yol.name}")
    for ad, adet in sorted(sayac.items(), key=lambda x: -x[1]):
        print(f"  {ad:<28} {adet:>5}")
    print(f"  {'TOPLAM':<28} {sum(sayac.values()):>5}")
    print(f"Harf ve rakam dizisi: {'AYNI ✓' if harf_ayni else 'DEĞİŞTİ ✗'}"
          f"   Typst yapı karakterleri: {'AYNI ✓' if yapi_ayni else 'DEĞİŞTİ ✗'}")
    print("Örnekler (satır: önce → yeni parça):")
    for ad, liste in ornekler.items():
        for satir, once_parca, yeni in liste:
            print(f"  [{ad}] {satir}: …{once_parca}… → {yeni!r}")
    if not (harf_ayni and yapi_ayni):
        print("DURDU: metnin harfleri ya da yapısı değişecekti; dosyaya yazılmadı.", file=sys.stderr)
        return 2
    if a.uygula and sayac:
        yedek, n = yol.with_name(f"{yol.stem}.yedek{yol.suffix}"), 2
        while yedek.exists():
            yedek, n = yol.with_name(f"{yol.stem}.yedek-{n}{yol.suffix}"), n + 1
        yedek.write_bytes(ham)
        yol.write_bytes((b"\xef\xbb\xbf" if bom else b"") + sonra.encode("utf-8"))
        print(f"Uygulandı. Özgün dosya: {yedek.name}")
    elif sayac:
        print("Kuru çalıştırma: dosya değişmedi. Uygulamak için --uygula ekleyin.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
