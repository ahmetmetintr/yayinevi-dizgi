#!/usr/bin/env python3
"""Düzeltme listesini metne uygular (tashih skill'i).

Yalnız Değiştir ve Sil maddeleri uygulanır; her madde metinde TEK ve KESİN bir yere oturmalıdır.
Tırnak, çizgi, boşluk ve bölünmez boşluk farkları eşleşmeye engel olmaz. Bulunamayan, birden çok yerde
geçen, Typst biçimi (italik, kalın, kod) içeren ya da başka maddeyle çakışan madde uygulanmaz; raporda
nedeni yazar. Bağlam (once/sonra) birden çok yer arasında seçim yapmaya yarar.

Kullanım:
  py tashih_uygula.py tashih/tur-02/liste.json metin/metin.typ             kuru çalıştırma
  py tashih_uygula.py tashih/tur-02/liste.json metin/metin.typ --uygula    yedek bırakır, uygular
  py tashih_uygula.py --onceki tashih metin/metin.typ                      önceki turlar yerinde mi
Uygulayınca liste.json'un yanına liste.sonuc.json yazılır (sonraki turların denetimi için).
"""
import argparse
import json
import re
import sys
from pathlib import Path

ESLE = {"~": " ", " ": " ", " ": " ", "’": "'", "‘": "'", "´": "'", "“": '"', "”": '"', "„": '"',
        "«": '"', "»": '"', "–": "-", "—": "-", "­": ""}
TYPST_BICIM = set("*_#[]`$<>@")
BICIM_ACILIS = re.compile(r"#(?:emph|strong|underline|smallcaps|sub|super)\[")
KACIR = set("#$@<*_`")


def normallestir(metin):
    """Karşılaştırma için sade metin ve her karakterin özgün konumu. Boşluk dizileri tek boşluk olur;
    Typst biçim işaretleri (_italik_, *kalın*, #emph[…]) atlanır ki PDF'te görünen metinle eşleşsin."""
    cikti, konum, onceki_bosluk = [], [], False
    i = 0
    while i < len(metin):
        c = metin[i]
        if c == "\\" and i + 1 < len(metin) and not metin[i + 1].isalnum():  # Typst kaçışı: \# → #
            i += 1
            c = metin[i]
        elif c in "_*]":
            i += 1
            continue
        elif c == "#" and BICIM_ACILIS.match(metin, i):
            i = BICIM_ACILIS.match(metin, i).end()
            continue
        c = ESLE.get(c, c)
        if c == "…":
            c = "..."
        if c.isspace():
            if not onceki_bosluk:
                cikti.append(" ")
                konum.append(i)
            onceki_bosluk = True
        else:
            for parca in c:
                cikti.append(parca)
                konum.append(i)
            onceki_bosluk = False
        i += 1
    return "".join(cikti), konum


def sade(metin):
    return normallestir(metin)[0].strip()


def yerleri_bul(norm, aranan):
    yerler, bas = [], norm.find(aranan)
    while bas >= 0:
        yerler.append(bas)
        bas = norm.find(aranan, bas + 1)
    return yerler


def harfler(metin):
    return "".join(c for c in metin.lower() if c.isalnum())


def baglamla_sec(norm, yerler, uzunluk, once, sonra):
    """Birden çok yer varsa önceki ve sonraki metinle (yalnız harf ve rakam) örtüşen yeri seç."""
    o, s = harfler(once)[-14:], harfler(sonra)[:14]

    def puan(bas):
        p = 0
        if o and harfler(norm[max(0, bas - 80):bas]).endswith(o):
            p += 1
        if s and harfler(norm[bas + uzunluk:bas + uzunluk + 80]).startswith(s):
            p += 1
        return p
    puanlar = [(puan(b), b) for b in yerler]
    en_iyi = max(p for p, _ in puanlar)
    secilen = [b for p, b in puanlar if p == en_iyi]
    return secilen if en_iyi > 0 else yerler


def kacir(metin):
    return "".join("\\" + c if c in KACIR else c for c in metin)


def planla(maddeler, metin):
    norm, konum = normallestir(metin)
    plan, alinan = [], []
    for m in maddeler:
        durum, aralik = "", None
        if m.get("karar") == "atla":
            durum = "atlandı (karar)"
        elif m.get("islem") not in ("Değiştir", "Sil"):
            durum = f"elle ({m.get('islem')})"
        elif not sade(m.get("eski", "")):
            durum = "elle (eski metin yok)"
        else:
            aranan = sade(m["eski"])
            yerler = yerleri_bul(norm, aranan)
            if len(yerler) > 1:
                yerler = baglamla_sec(norm, yerler, len(aranan), m.get("once", ""), m.get("sonra", ""))
            if not yerler:
                yeni = sade(m.get("yeni", ""))
                durum = "zaten uygulanmış olabilir" if len(yeni) >= 4 and norm.find(yeni) >= 0 else "bulunamadı"
            elif len(yerler) > 1 and not m.get("tum"):
                durum = f"birden çok yer ({len(yerler)})"
            else:
                araliklar = [(konum[b], konum[b + len(aranan) - 1] + 1) for b in yerler]
                if any(TYPST_BICIM & set(metin[a:z]) for a, z in araliklar):
                    durum = "elle (biçim içeriyor)"
                elif any(a < z2 and a2 < z for a, z in araliklar for a2, z2 in alinan):
                    durum = "çakışma"
                else:
                    durum, aralik = "uygulanacak", araliklar
                    alinan += araliklar
        plan.append((m, durum, aralik))
    return plan


def yeni_metin(m):
    """Eşleşme eskinin baş ve sondaki boşluğunu dışarıda bırakır; yeniden de aynısı düşer (çift boşluk olmasın)."""
    eski, yeni = m.get("eski", ""), m.get("yeni", "")
    if eski[-1:].isspace():
        yeni = yeni.rstrip()
    if eski[:1].isspace():
        yeni = yeni.lstrip()
    return kacir(yeni)


def uygula(metin, plan):
    degisim = sorted(((a, z, yeni_metin(m)) for m, _, ar in plan if ar for a, z in ar), reverse=True)
    for a, z, yeni in degisim:
        metin = metin[:a] + yeni + metin[z:]
    return metin


def onceki_turlar(klasor, metin, haric=None):
    norm = normallestir(metin)[0]
    eksik = []
    for dosya in sorted(Path(klasor).rglob("*.sonuc.json")):
        if haric and dosya.resolve() == haric.resolve():
            continue
        for m in json.loads(dosya.read_text(encoding="utf-8")):
            yeni = sade(m.get("yeni", ""))
            if m.get("durum", "").startswith("uygulandı") and yeni and norm.find(yeni) < 0:
                eksik.append((dosya.parent.name, m))
    return eksik


def satir_no(metin, konum):
    return metin.count("\n", 0, konum) + 1


def main():
    for akis in (sys.stdout, sys.stderr):
        akis.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Düzeltme listesini metne uygula")
    p.add_argument("liste", nargs="?", help="tashih_oku.py çıktısı ya da elle hazırlanmış JSON")
    p.add_argument("metin", help="düzeltilecek dosya (metin/metin.typ)")
    p.add_argument("--uygula", action="store_true")
    p.add_argument("--onceki", help="önceki turların klasörü (tashih): uygulanmış düzeltmeler hâlâ yerinde mi")
    a = p.parse_args()
    yol = Path(a.metin)
    metin = yol.read_text(encoding="utf-8-sig")

    if a.onceki:
        eksik = onceki_turlar(a.onceki, metin, Path(a.liste).with_suffix(".sonuc.json") if a.liste else None)
        if eksik:
            print(f"⚠ Önceki turlarda uygulanmış {len(eksik)} düzeltme bu dosyada yok. Dosya eski bir sürümden türemiş olabilir:")
            for tur, m in eksik[:30]:
                print(f"   {tur} · {m.get('yer', '')} · «{m.get('eski', '')}» → «{m.get('yeni', '')}»")
        else:
            print("✓ Önceki turlardaki düzeltmelerin hepsi yerinde.")
        if not a.liste:
            return 1 if eksik else 0

    maddeler = json.loads(Path(a.liste).read_text(encoding="utf-8"))
    plan = planla(maddeler, metin)
    sayac = {}
    print("| No | Durum | Satır | Eski → Yeni |")
    print("| --- | --- | --- | --- |")
    for m, durum, aralik in plan:
        sayac[durum.split(" (")[0]] = sayac.get(durum.split(" (")[0], 0) + 1
        satir = ", ".join(str(satir_no(metin, x)) for x, _ in aralik) if aralik else ""
        ozet = f"«{m.get('eski', '')[:40]}» → «{m.get('yeni', '')[:40]}»" if m.get("eski") or m.get("yeni") \
            else " ".join((m.get("yorum") or "(görsele bak)").split())[:60]
        print(f"| {m.get('no', '')} | {durum} | {satir} | {ozet} |")
    print("\nÖzet: " + " · ".join(f"{k} {v}" for k, v in sayac.items()))

    if not a.uygula:
        print("Kuru çalıştırma: dosya değişmedi. Uygulamak için --uygula ekleyin.")
        return 0
    yeni_metin = uygula(metin, plan)
    yedek, n = yol.with_name(f"{yol.stem}.yedek{yol.suffix}"), 2
    while yedek.exists():
        yedek, n = yol.with_name(f"{yol.stem}.yedek-{n}{yol.suffix}"), n + 1
    yedek.write_text(metin, encoding="utf-8")
    yol.write_text(yeni_metin, encoding="utf-8")
    sonuc = [dict(m, durum="uygulandı" if aralik else durum) for m, durum, aralik in plan]
    Path(a.liste).with_suffix(".sonuc.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Uygulandı. Özgün dosya: {yedek.name} · sonuç: {Path(a.liste).with_suffix('.sonuc.json').name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
