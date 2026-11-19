---
name: tashih
description: Yazardan, hocalardan ya da editörden gelen düzeltmeleri (tashih, redaksiyon) hızla okuyup dizgiye uygulama ve yazara dönüşü hazırlama. İşaretli PDF (üstü çizili, ekleme imi, vurgu, yapışkan not, el yazısı), izli değişiklikli ya da yorumlu Word, e-posta ya da liste. Kullanıcı "düzeltmeler geldi", "hocanın notları", "tashih", "redaksiyon", "işaretli PDF", "yazar düzeltmesi", "ikinci tur", "düzeltmeleri işle" dediğinde kullan.
---

# Tashih

## İlkeler

- Düzeltmeyi araç uygular: `tashih_uygula.py` yalnız metinde tek ve kesin yere oturan maddeyi değiştirir,
  gerisini nedeniyle bırakır. Metne elle dokunman gerekirse en küçük farkla yap ve kayda geçir.
- Kitabın yazarından gelen düzeltme uygulanır. Başkasından (editör, hakem, takdim yazarı) gelen içerik
  değişikliğini uygulamadan önce kullanıcıya sor.
- Hızlı ama izli: her tur `tashih/tur-NN/` klasöründe durur; hocadan gelen dosyalar hiç değiştirilmez.
- Önce çalışma klasöründeki `yayinevi.md`'yi oku (düzeltme biçimi ve imza orada).

```
tashih/tur-01/
  gelen/             hocadan gelen dosyalar (salt okunur)
  gorsel/            el yazısı ve çizimlerin görüntüleri (araç kaydeder)
  liste.json         okunan maddeler
  liste.sonuc.json   uygulama sonucu (sonraki turların denetimi buna bakar)
  rapor.md           yazara dönüş
```

Araçlar bu skill'in `araclar/` klasöründe. Windows'ta `py`, macOS'ta `python3`. Gerekli paket: pymupdf.

## Akış

0. **Eski sürüm tuzağı.** Her turdan önce: `py tashih_uygula.py --onceki tashih metin/metin.typ`.
   Uyarı çıkarsa DUR ve kullanıcıya göster: metin eski bir sürümden türemiş, önceki turlar kaybolmuş olabilir.
   Hocanın işaretlediği PDF en son gönderilen PDF mi, bak; eskiyse sayfa numarasına değil metne güven.
1. **Oku.** `py tashih_oku.py tashih/tur-NN/gelen/* --json tashih/tur-NN/liste.json` ve tabloyu göster.
   - `[görsel]` olan maddelerin görüntüsüne bak; el yazısını oku ve maddeyi Değiştir ya da Sil biçimine çevir.
   - "Not" serbest yorumdur: anlamı açıksa Değiştir maddesine çevir (eski = metindeki birebir parça); açık
     değilse maddeye kısa bir `soru` yaz.
   - Ekle maddesinde eski = eklemenin hemen önündeki bir iki sözcük, yeni = aynı sözcükler + eklenen.
   - E-posta ya da mesajla gelen düzeltmeyi önce `gelen/` içine .txt olarak kaydet: satır başına bir madde.
   - Aynı ifade her yerde değişecekse (terim birliği) maddeye `"tum": true` ekle; yalnız hoca açıkça "her
     yerde" dediyse.
   - Birbirine aykırı maddeleri (aynı yer için iki farklı öneri) kullanıcıya göster.
2. **Uygula.** Kuru çalıştır: `py tashih_uygula.py tashih/tur-NN/liste.json metin/metin.typ` ve özeti ver:
   kaç madde uygulanacak, hangileri neden bekliyor. Kullanıcının tek onayıyla `--uygula` ekleyip uygula.
   - "elle (biçim içeriyor)": italik ya da kalın içindeki değişiklik; metin.typ'de elle yap.
   - "Biçim" maddeleri Typst'te ya da şablon parametresinde yapılır, metne dokunulmaz.
   - Elle uyguladığın maddenin `durum` alanını liste.sonuc.json'da "uygulandı (elle)" yap.
3. **Diz ve dön.** PDF'i dizgi skill'iyle yeniden üret. Sonra:
   `py tashih_rapor.py cikti/<yeni>.pdf tashih/tur-NN/liste.sonuc.json --isaretli cikti/<kitap>-tur-NN-isaretli.pdf --rapor tashih/tur-NN/rapor.md --imza "<yayınevi adı>"`
   Değişen sayfaları önizle: satır kayması yeni dul satır, taşan sayfa ya da içindekiler farkı yarattı mı.
4. **Kayıt.** `NOTLAR.md` değişiklik kaydına turun özetini yaz (tarih, uygulanan, bekleyen).

## Yazara dönüş

- Yayınevi editörünün sesiyle: kısa, nazik, resmî. "Sayın Hocam," diye başlayan 3–5 cümlelik e-posta taslağı:
  kaç düzeltme işlendi, kaç soru kaldı, ekler (işaretli PDF, rapor). Emoji, "yapay zekâ", araç adı geçmez.
- Soruları kapalı uçlu sor: "45. sayfadaki «…» ifadesi iki yerde geçiyor: 3. paragraftaki mi, 5.'deki mi?"
- Yayınevinin kendi düzeltmelerini yazara gönderirken PDF yorumu biçimi: ilk satır komut ("Değiştir:
  «eski» → «yeni»", "Ekle: «…»", "Sil: «…»", "Biçim: …"), sonraki satır kısa gerekçe. Her yorum tek başına
  okunur olmalı.
