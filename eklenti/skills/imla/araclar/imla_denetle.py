#!/usr/bin/env python3
"""İmla denetimi (imla skill'i): Typst metnindeki Türkçe yazım yanlışlarını bulur, hiçbirini DÜZELTMEZ.

Kullanım:
  py imla_denetle.py metin/bolum-01.typ metin/bolum-02.typ
  py imla_denetle.py metin/*.typ --rapor cikti/imla-raporu.md --isaret metin/imla-isaretleri.typ --istisna imla-istisnalar.txt
Bulgular:
  kesin  sık yanlışlar listesi (kurallar/sik-yanlislar.tsv), rakam ve kısaltmadan sonra kesmesiz ek, yinelenen bağlaç
  olası  bitişik yazılmış soru eki; kitapta bir iki kez geçip sık geçen bir sözcükten tek harfle ayrılan sözcük
         ("anomamliler" ↔ "anomaliler"); aynı terimin iki yazımı ("orşiopeksi" ↔ "orşidopeksi")
--isaret: sarı prova için Typst dosyası (`#let imla-deseni = "…"`); kitap.typ şablona `sari-desen` olarak verir.
--istisna: denetimden muaf sözcükler (satır başına bir sözcük; editörün "doğru" dediği terimler).
Kaynakçalar taranmaz: özel adlarla doludur ve kaynakça denetimi ayrı araçtır.
"""
import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

SURUM = "1.0"
KURALLAR = Path(__file__).resolve().parents[1] / "kurallar" / "sik-yanlislar.tsv"
HARF = "A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû"
ABECE = "abcçdefgğhıijklmnoöprsştuüvyzâîû"
SOZCUK = re.compile(rf"[{HARF}]+")
KAYNAKCA = re.compile(r"#kaynakca(?:\((?:[^()\[\]]|\[[^\]]*\])*\))?\[")
EK_RAKAM = ("da|de|ta|te|dan|den|tan|ten|lı|li|lu|lü|ya|ye|nın|nin|nun|nün|ncı|nci|ncu|ncü|lık|lik|luk|lük|"
            "lar|ler|dır|dir|dur|dür|tır|tir|tur|tür")
EK_KISALTMA = "da|de|ta|te|dan|den|tan|ten|ya|ye|yı|yi|yu|yü|nın|nin|nun|nün|ın|in|un|ün|la|le|lar|ler|dır|dir"
BAGLAC = "ve|veya|ile|bir|bu|da|de|için|olarak|gibi|daha|en|ya|ki|ancak|ise"
EK_FIIL = re.compile(r"(dır|dir|dur|dür|tır|tir|tur|tür)$")   # "bulgularıdır" ↔ "bulgulardır": ikisi de doğru


def tr_kucuk(s):
    return s.replace("I", "ı").replace("İ", "i").lower()   # uzunluk korunur: konumlar asıl metinle aynı kalır


def _bosalt(t, bas, son):
    return t[:bas] + re.sub(r"[^\n]", " ", t[bas:son]) + t[son:]


def duz_metin(t):
    """Typst kaynağını satır ve sütunları koruyarak yazıya indirger: kaynakça, kod, yol ve etiket boşluğa döner."""
    for m in reversed(list(KAYNAKCA.finditer(t))):
        d, j = 1, m.end()
        while j < len(t) and d:
            d += {"[": 1, "]": -1}.get(t[j], 0) if t[j - 1] != "\\" else 0
            j += 1
        t = _bosalt(t, m.start(), j)
    desenler = [r"(?m)^\s*(#import|#include|//).*$", r'(?<!\\)"(?:[^"\\\n]|\\.)*"', r"<[\w\-:.]+>|@[\w\-:.]+",
                r"\$[^$\n]*\$|`[^`\n]*`", r"#[A-Za-z][\w.-]*", r"\b[a-z][a-z-]*:\s",
                r"\b\d+(?:\.\d+)?(?:in|mm|cm|pt|em|fr|deg)\b", r"\\(?=[^'’])"]
    for d in desenler:
        t = re.sub(d, lambda e: re.sub(r"[^\n]", " ", e.group()), t)
    return t.replace("\\'", " '").replace("\\’", " ’")


def sozluk(yol=KURALLAR):
    """[(derlenmiş desen, doğru, kural, kök mü)]"""
    out = []
    for satir in yol.read_text(encoding="utf-8").splitlines():
        if not satir.strip() or satir.startswith("#"):
            continue
        yanlis, dogru, kural = (satir.split("\t") + ["", ""])[:3]
        kok = yanlis.endswith("*")
        govde = r"\s+".join(map(re.escape, yanlis.rstrip("*").split()))
        out.append((re.compile(rf"(?<![{HARF}]){govde}" + (rf"[{HARF}]*" if kok else rf"(?![{HARF}])")),
                    dogru.rstrip("*"), kural, yanlis.rstrip("*")))
    return out


def _harf_duzeni(asil, oneri):
    if asil.isupper():
        return oneri.replace("i", "İ").replace("ı", "I").upper()
    return oneri[:1].upper() + oneri[1:] if asil[:1].isupper() else oneri


def kural_bulgulari(t, kurallar):
    """Satır içi kurallar: [(konum, eşleşen, öneri, kural, güven)]"""
    k = tr_kucuk(t)
    out = []
    for desen, dogru, kural, yanlis in kurallar:
        for m in desen.finditer(k):
            asil = t[m.start():m.end()]
            out.append((m.start(), asil, _harf_duzeni(asil, dogru + m.group()[len(yanlis):]), kural, "kesin"))
    for m in re.finditer(rf"(?<![\w.,%])(\d+)({EK_RAKAM})(?![{HARF}])", t):
        out.append((m.start(), m.group(), f"{m.group(1)}'{m.group(2)}", "rakamdan sonraki ek kesmeyle ayrılır", "kesin"))
    for m in re.finditer(rf"%(\d+(?:[.,]\d+)?)([{HARF}]+)", t):
        out.append((m.start(), m.group(), f"%{m.group(1)}'{m.group(2)}", "yüzde sayısından sonraki ek kesmeyle ayrılır", "kesin"))
    for m in re.finditer(rf"(?<![{HARF}])([A-ZÇĞİÖŞÜ]{{2,6}})({EK_KISALTMA})(?![{HARF}])", t):
        out.append((m.start(), m.group(), f"{m.group(1)}'{m.group(2)}", "kısaltmadan sonraki ek kesmeyle ayrılır", "kesin"))
    for m in re.finditer(rf"(?<![{HARF}'’])({BAGLAC})\s+\1(?![{HARF}])", k):   # "Türkiye'de de" doğrudur
        out.append((m.start(), t[m.start():m.end()], m.group(1), "aynı sözcük iki kez yazılmış", "kesin"))
    for m in re.finditer(rf"(?<![{HARF}])[{HARF}]*[a-zçğıöşü]İ[{HARF}]*", t):        # "hİpertrofik pİlor"
        out.append((m.start(), m.group(), m.group()[:1] + tr_kucuk(m.group()[1:]), "sözcük içinde büyük İ", "kesin"))
    for m in re.finditer(rf"(?<![{HARF}'’])(ve|veya|ile)([A-ZÇĞİÖŞÜ][{HARF}]+)", t):   # "veMcMahon"
        out.append((m.start(), m.group(), f"{m.group(1)} {m.group(2)}", "bağlaç sonraki sözcüğe yapışmış", "kesin"))
    for m in re.finditer(rf"(?<![{HARF}])([{HARF}]{{3,}})(mı|mi|mu|mü)(?:dır|dir|sın|sin|yız|yiz)?\?", t):
        out.append((m.start(), m.group()[:-1], f"{m.group(1)} {m.group()[len(m.group(1)):-1]}", "soru eki ayrı yazılır", "olası"))
    return out


# Gerçekçi yazım hataları: Türkçe harf karışması, s/z, a/e, a/o; i/y eklenip düşmesi; harf ikilemesi; yer değiştirme.
# İlk harf hiç değişmez (a-semptomatik, s-eptik gibi önekler ve ayrı sözcükler yakalanmasın).
KARISAN = {frozenset(c) for c in ("oö", "uü", "iı", "cç", "sş", "gğ", "sz", "ae", "ao")}
UNLU = set("aeıioöuüâîû")


def _bir_harf_komsulari(s, son=3):
    """s'nin kökünde (ilk ve son `son` harf dışında) tek düzeltmeyle elde edilen biçimler → (biçim, serbest mi).
    serbest: herhangi bir fazla harf ("anomamliler"). Kullanılmaz: kitapta denendi, Türkçe çekimlerle karışıyor
    ("olamadığı" ↔ "olmadığı", "dışlatmaz" ↔ "dışlamaz"); ünlü yığılması ("periaoperatif") ise olağan sayılır."""
    n = len(s)
    for i in range(1, max(1, n - son)):
        olagan = s[i] in "iıyh" or s[i] == s[i - 1] or (s[i] in UNLU and (s[i - 1] in UNLU or s[i + 1:i + 2] in UNLU))
        yield s[:i] + s[i + 1:], not olagan                          # fazla harf
        if i + 1 < n:
            yield s[:i] + s[i + 1] + s[i] + s[i + 2:], False           # yer değiştirme
        for c in ABECE:
            if frozenset((c, s[i])) in KARISAN:
                yield s[:i] + c + s[i + 1:], False                    # karışan harf
            if c in "iy" or c == s[i - 1] or c == s[i]:
                yield s[:i] + c + s[i:], False                        # eksik harf


def benzerlik_bulgulari(sayim, istisna, buyuk=Counter(), en_kisa=7, seyrek=2, sik=5):
    """Seyrek sözcük sık bir sözcükten tek harfle ayrılıyorsa olası yazım hatası; ikisi de sıksa tutarsız yazım.
    Hep büyük harfle başlayan ad, aynı biçimdeki adla karşılaştırılmaz (Thompson ↔ Thomson). → {sözcük: (öneri, kural)}"""
    out = {}
    ad_mi = lambda w: buyuk[w] == sayim[w]
    for s, n in sayim.items():
        if len(s) < en_kisa or s in istisna:
            continue
        adaylar = {a for a, serbest in _bir_harf_komsulari(s) if a != s and sayim.get(a, 0) >= max(sik, n + 1)
                   and not (ad_mi(s) and ad_mi(a)) and not (EK_FIIL.search(s) and EK_FIIL.search(a))
                   and not serbest}
        if not adaylar:
            continue
        en_sik = max(adaylar, key=sayim.get)
        if n <= seyrek:
            out[s] = (en_sik, f"olası yazım hatası (kitapta {n} kez; «{en_sik}» {sayim[en_sik]} kez)")
        elif n >= 3:
            out[s] = (en_sik, f"aynı terimin iki yazımı («{s}» {n} kez, «{en_sik}» {sayim[en_sik]} kez)")
    return out


def denetle(dosyalar, istisna=frozenset(), kurallar=None):
    """[(dosya, satır, eşleşen, öneri, kural, güven)]"""
    kurallar = sozluk() if kurallar is None else kurallar
    metinler = {d: duz_metin(Path(d).read_text(encoding="utf-8")) for d in dosyalar}
    sozcukler = [w for t in metinler.values() for w in SOZCUK.findall(t) if not (w.isupper() and len(w) > 1)]
    sayim = Counter(tr_kucuk(w) for w in sozcukler)              # TÜMÜ BÜYÜK sözcük (I/İ belirsiz) sayılmaz
    buyuk = Counter(tr_kucuk(w) for w in sozcukler if w[:1].isupper())
    benzer = benzerlik_bulgulari(sayim, istisna, buyuk)
    out = []
    for d, t in metinler.items():
        satir_basi = [0] + [m.end() for m in re.finditer("\n", t)]
        satir = lambda konum: next(i for i in range(len(satir_basi) - 1, -1, -1) if satir_basi[i] <= konum) + 1
        for konum, esles, oneri, kural, guven in kural_bulgulari(t, kurallar):
            if tr_kucuk(esles) not in istisna:
                out.append((d, satir(konum), esles, oneri, kural, guven))
        for m in SOZCUK.finditer(t):
            if tr_kucuk(m.group()) in benzer and not m.group().isupper():
                oneri, kural = benzer[tr_kucuk(m.group())]
                out.append((d, satir(m.start()), m.group(), _harf_duzeni(m.group(), oneri), kural, "olası"))
    return sorted(set(out), key=lambda b: (b[0], b[1]))


def rapor(bulgular):
    say = Counter(b[5] for b in bulgular)
    satirlar = [f"# İmla denetimi (imla_denetle.py {SURUM})", "",
                f"Kesin: {say['kesin']} · olası: {say['olası']}. Metin değiştirilmedi; karar editörün ve yazarındır.", ""]
    for kural, n in Counter(b[4].split(" (")[0] for b in bulgular).most_common():
        satirlar.append(f"- {kural}: {n}")
    gruplar = defaultdict(list)
    for b in bulgular:
        gruplar[b[0]].append(b)
    for d, liste in gruplar.items():
        satirlar += ["", f"## {Path(d).name} ({len(liste)})", "", "| Satır | Yazılan | Öneri | Kural | Güven |",
                     "| --- | --- | --- | --- | --- |"]
        satirlar += [f"| {s} | {e} | {o} | {k} | {g} |" for _, s, e, o, k, g in liste]
    return "\n".join(satirlar) + "\n"


def isaret_dosyasi(bulgular):
    """Sarı prova deseni: bulunan yazımlar (uzundan kısaya), Typst dizgesi olarak kaçışlı."""
    parcalar = sorted({re.escape(b[2]) for b in bulgular}, key=len, reverse=True)
    desen = "(?:" + "|".join(parcalar) + ")" if parcalar else ""
    typst = desen.replace("\\", "\\\\").replace('"', '\\"')
    deger = f'"{typst}"' if desen else "none"
    return ("// imla_denetle.py üretir, elle düzenlenmez. Sarı prova: typst compile --input imla=evet kitap.typ …\n"
            f"#let imla-deseni = {deger}\n")


def main():
    for akis in (sys.stdout, sys.stderr):
        akis.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Türkçe imla denetimi (Typst metin dosyaları); düzeltmez, raporlar")
    p.add_argument("dosyalar", nargs="*")
    p.add_argument("--rapor", help="Markdown rapor dosyası")
    p.add_argument("--isaret", help="sarı prova için Typst desen dosyası")
    p.add_argument("--istisna", help="muaf sözcükler dosyası (satır başına bir sözcük)")
    p.add_argument("--surum", action="store_true")
    a = p.parse_args()
    if a.surum:
        print(f"imla_denetle.py {SURUM}")
        return 0
    if not a.dosyalar:
        p.error("en az bir dosya gerekli")
    istisna = frozenset()
    if a.istisna and Path(a.istisna).exists():
        istisna = frozenset(tr_kucuk(s.strip()) for s in Path(a.istisna).read_text(encoding="utf-8").splitlines()
                            if s.strip() and not s.startswith("#"))
    bulgular = denetle(a.dosyalar, istisna)
    metin = rapor(bulgular)
    if a.rapor:
        Path(a.rapor).write_text(metin, encoding="utf-8")
    if a.isaret:
        Path(a.isaret).write_text(isaret_dosyasi(bulgular), encoding="utf-8")
    print(metin if not a.rapor else metin.split("\n## ")[0] + f"\nRapor: {a.rapor}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
