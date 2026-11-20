#!/usr/bin/env python3
"""Yayınevi düzeni (dizgi skill'i): editörlü kitabın metin dosyalarına Vizetek'in dizgi isteklerini uygular.

Yazarın cümlelerine dokunmaz. Kurallar (duzenle_kurallari.py):
  ozet    bölüm başındaki Özet/Abstract ve Anahtar Kelimeler/Keywords bloklarını çıkarır
  kunye   yazar künyesinde e-postayı siler, ORCID'i "ORCID: 0000-0000-0000-0000" yazar
  baslik  tümü büyük GİRİŞ / SONUÇ / KAYNAKLAR → Giriş / Sonuç / Kaynaklar; kaynakça başlığı kitapta tek ad
  not     şekil ya da tablodan hemen sonraki "Not.", "Kaynak:" paragraflarını #notlu-sekil ile şekle bağlar
Elle bakılacakları da listeler: düzensiz özet, metin içinde kalmış künye, boşlukla dizilmiş tablo, tümü büyük
harf ara başlık.

Kullanım:
  py duzenle.py metin/bolum-*.typ                kuru çalıştırma: yalnız rapor
  py duzenle.py metin/bolum-*.typ --uygula       dosyaları düzeltir, her birinin özgününü .yedek.typ bırakır
Seçenekler:
  --kural ozet,kunye,baslik,not    yalnız bu kurallar (varsayılan: hepsi)
  --kaynakca-basligi Kaynaklar     kaynakça başlığı (varsayılan: kitapta en çok kullanılan; eşitlikte Kaynaklar)
"""
import argparse
import glob
import sys
from collections import Counter, defaultdict
from pathlib import Path

from duzenle_kurallari import KURALLAR, kaynakca_cogunlugu, kunye_disarida, sahte_tablolar

ORNEK = 4  # her değişiklik ve uyarı türünden rapora giren örnek sayısı


def dosyalari_bul(desenler):
    yollar = []
    for d in desenler:
        yollar += sorted(glob.glob(d)) if any(c in d for c in "*?[") else [d]
    return [Path(y) for y in dict.fromkeys(yollar) if ".yedek" not in Path(y).name]


def yedekle(yol, ham):
    yedek, n = yol.with_name(f"{yol.stem}.yedek{yol.suffix}"), 2
    while yedek.exists():
        yedek, n = yol.with_name(f"{yol.stem}.yedek-{n}{yol.suffix}"), n + 1
    yedek.write_bytes(ham)
    return yedek


def duzenle(metin, kurallar, kaynakca_adi):
    """Seçilen kuralları sırayla uygular → (yeni metin, değişiklikler, uyarılar)."""
    degisiklikler, uyarilar = [], []
    for ad in kurallar:
        ek = (kaynakca_adi,) if ad == "baslik" else ()
        metin, deg, uyar = KURALLAR[ad](metin, *ek)
        degisiklikler += deg
        uyarilar += uyar
    disarida = {s: p for s, p in kunye_disarida(metin)}  # aynı satırdaki ORCID ve e-posta tek uyarı
    uyarilar += [(s, f"künye metin içinde, dipnota (#bolum yazarlarına) taşınmalı: {p}") for s, p in disarida.items()]
    uyarilar += [(s, f"tablo yazısı var, tablosu yok (boşlukla dizilmiş; tablo_kur.py): {p}")
                 for s, p in sahte_tablolar(metin)]
    return metin, degisiklikler, uyarilar


def raporla(sonuclar):
    """sonuclar: [(dosya adı, değişiklikler, uyarılar)] → tür başına sayı ve örnekler."""
    sayac, ornekler = Counter(), defaultdict(list)
    for ad, degisiklikler, _ in sonuclar:
        for satir, tur, once, sonra in degisiklikler:
            sayac[tur] += 1
            ornekler[tur].append(f"{ad}:{satir}  {once} → {sonra}")
    print("Değişiklikler:")
    for tur, adet in sayac.most_common():
        print(f"  {tur:<14} {adet:>4}")
        for o in ornekler[tur][:ORNEK]:
            print(f"      {o}")
    print(f"  {'TOPLAM':<14} {sum(sayac.values()):>4}")
    turler = defaultdict(list)
    for ad, _, uyarilar in sonuclar:
        for satir, ne in uyarilar:
            turler[ne.split(":")[0]].append(f"{ad}:{satir}  {ne}")
    if turler:
        print("Elle bakılacaklar:")
    for tur, liste in turler.items():
        print(f"  {tur} ({len(liste)})")
        for o in liste[:ORNEK if "büyük harf" in tur else len(liste)]:
            print(f"      {o}")


def main():
    for akis in (sys.stdout, sys.stderr):
        akis.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Yayınevi düzeni: özet, künye, başlık adları, tablo notları")
    p.add_argument("dosyalar", nargs="+", help="metin dosyaları (ör. metin/bolum-*.typ)")
    p.add_argument("--kural", default=",".join(KURALLAR), help="virgülle: " + ", ".join(KURALLAR))
    p.add_argument("--kaynakca-basligi", help="kaynakça başlığı (varsayılan: kitapta en çok kullanılan)")
    p.add_argument("--uygula", action="store_true", help="dosyalara yaz (yedek bırakır)")
    a = p.parse_args()
    kurallar = [k.strip() for k in a.kural.split(",") if k.strip()]
    bilinmeyen = [k for k in kurallar if k not in KURALLAR]
    if bilinmeyen:
        p.error(f"bilinmeyen kural: {', '.join(bilinmeyen)}")
    yollar = dosyalari_bul(a.dosyalar)
    eksik = [str(y) for y in yollar if not y.is_file()]
    if eksik or not yollar:
        p.error(f"dosya bulunamadı: {', '.join(eksik) or ' '.join(a.dosyalar)}")
    hamlar = {y: y.read_bytes() for y in yollar}
    metinler = {y: h.decode("utf-8-sig") for y, h in hamlar.items()}
    kaynakca_adi = a.kaynakca_basligi or kaynakca_cogunlugu(metinler.values())
    print(f"Yayınevi düzeni: {len(yollar)} dosya · kurallar: {', '.join(kurallar)} · kaynakça başlığı: {kaynakca_adi}")

    sonuclar, yazilacak = [], {}
    for yol, metin in metinler.items():
        yeni, degisiklikler, uyarilar = duzenle(metin, kurallar, kaynakca_adi)
        sonuclar.append((yol.name, degisiklikler, uyarilar))
        if yeni != metin:
            yazilacak[yol] = yeni
    raporla(sonuclar)
    if not yazilacak:
        print("Değişecek bir şey yok.")
    elif a.uygula:
        for yol, yeni in yazilacak.items():
            bom = b"\xef\xbb\xbf" if hamlar[yol].startswith(b"\xef\xbb\xbf") else b""
            yedekle(yol, hamlar[yol])
            yol.write_bytes(bom + yeni.encode("utf-8"))
        print(f"Uygulandı: {len(yazilacak)} dosya (özgünleri .yedek.typ). Şimdi kitabı derleyip bakın.")
    else:
        print(f"Kuru çalıştırma: {len(yazilacak)} dosya değişecek. Uygulamak için --uygula ekleyin.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
