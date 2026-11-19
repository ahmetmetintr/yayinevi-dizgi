---
name: dizgi
description: Kitap iç sayfa dizgisi ve baskı öncesi hazırlık. Word (.docx) ya da metin dosyasından Typst ile baskıya hazır PDF, Türkçe tipografi düzeltmesi, dizgi kontrolü, tashih (düzeltme) işleme, künye ve içindekiler, matbaa hazırlığı. Kullanıcı "dizgi", "mizanpaj", "kitabı diz", "baskıya hazırla", "matbaaya gönder", "tashih", "düzeltmeleri işle", "künye", "içindekiler", "dul satır", "forma" dediğinde ya da bir kitap dosyası verdiğinde kullan.
---

# Dizgi

## Altın kural: yazarın metnine dokunma

- Sözcük değiştirme, yazım düzeltme, kısaltma, "iyileştirme" yok. Yazım hatası ya da tutarsızlık görürsen
  düzeltme: kitabın `NOTLAR.md` dosyasındaki "Tashih önerileri" listesine yaz ve kullanıcıya göster.
- Noktalama ve boşluk düzeltmesini elle değil `araclar/tipografi.py` ile yap. Betik harf dizisi ya da Typst
  yapısı değişecekse dosyaya yazmaz.
- Yazarın dosyaları `kaynak/` klasöründe kalır ve hiç değiştirilmez.

## Yerler

Skill klasörü (yüklenirken "Base directory" satırında yazar): `sablon/kitap.typ` şablon ·
`sablon/ana-dosya.typ` yeni kitabın ana dosyası · `sablon/yayinevi.md` kural şablonu · `araclar/tipografi.py` ·
`araclar/pdf_kontrol.py`. Skill klasöründe hiçbir dosyayı değiştirme: eklenti güncellenince değişiklik silinir.

Çalışma klasörü (genelde Belgeler/Dizgi; Claude Code burada açılır): `CLAUDE.md` · `yayinevi.md` · her kitaba bir
klasör. **Her işte önce çalışma klasöründeki `yayinevi.md`'yi oku; oradaki değer bu dosyadaki varsayılanı
geçersiz kılar.** Dosya yoksa `sablon/yayinevi.md`'yi oraya kopyala ve kullanıcıya kuralları doldurmayı öner.

Python'u Windows'ta `py`, macOS'ta `python3` ile çağır; araçlar bu skill'in `araclar/` klasöründedir. Kitap klasörünün düzeni:

```
Kitap-Adi/
  kaynak/           yazardan gelen dosyalar (salt okunur)
  metin/metin.typ   dizilecek metin
  gorseller/
  sablon/kitap.typ  şablonun bu kitaba kopyası (kitap kendi sürümünü taşır)
  kitap.typ         ana dosya (ana-dosya.typ'den)
  cikti/            PDF'ler (kitap-YYYY-AA-GG.pdf) ve onizleme/
  tashih/           düzeltme turları (tashih skill'i)
  kapak/            kapak eskizleri ve tam kapak (kapak skill'i)
  NOTLAR.md         kararlar · terim listesi · tashih önerileri · açık sorular · değişiklik kaydı
```

## İş akışı

1. **Proje aç.** Klasörleri kur; skill'deki `sablon/kitap.typ`'yi kitabın `sablon/` klasörüne, `ana-dosya.typ`'yi
   kitap klasörüne `kitap.typ` adıyla kopyala. Ölçü ve yazı tipini `yayinevi.md`'den al, künyeyi kullanıcıya sor; bilinmeyeni `[DOLDUR: …]` bırak.
2. **Word'ü al.** `pandoc "kaynak/<dosya>.docx" -t typst --wrap=none --extract-media=gorseller -o metin/metin.typ`
   Sonra denetle ve raporla: başlıklar (`=` bölüm, `==` ara başlık) ve düzeyleri; dipnot sayısı Word'dekiyle aynı
   mı; görsel ve tablo sayısı; stil verilmeden elle yapılmış başlıklar (tek satırlık kalın paragraflar); boş
   paragraflar ve elle sayfa sonları; `- ` ile başlayıp yanlışlıkla liste olmuş konuşma satırları. Sözcük
   sayısını `pandoc kaynak.docx -t plain` çıktısıyla karşılaştır; belirgin kayıp varsa dur. Yapı düzeltmesini
   (başlık düzeyi, boş satır) önce listele, onayla uygula; metne dokunma.
   Typst `unknown variable: horizontalrule` derse `#horizontalrule` yerine `#sahne-arasi` yaz ve metnin başına
   `#import "../sablon/kitap.typ": sahne-arasi` ekle.
3. **Tipografi.** `py tipografi.py metin/metin.typ` (kuru çalıştırma) → raporu göster → onayla `--uygula`.
   Çizgi tercihleri `yayinevi.md`'den: `--ara-cizgi en|em`, `--konusma-cizgisi em|en`.
4. **Diz.** `typst compile kitap.typ cikti/kitap-YYYY-AA-GG.pdf` — uyarıları oku ve çöz.
5. **Bak.** `typst compile kitap.typ "cikti/onizleme/s{p}.png" --ppi 50 --pages 1-16` (gerekirse başka sayfalar).
   Görüntüleri kendin incele: bölüm açılışları, boş sayfalar, üst bilgiler, künye, içindekiler.
6. **Kontrol.** `py pdf_kontrol.py cikti/<pdf> --olcu 135x210 --tek-renk --yazi-tipi "<yazı tipi>"`
   (değerler `yayinevi.md`'den), sonra uyarı veren sayfaları önizleyip bak.
7. **Raporla.** Kısa tablo: sayfa sayısı, uyarılar, yapılanlar, kullanıcıdan beklenenler. `NOTLAR.md`'yi güncelle.

## Türkçe dizgi kuralları (varsayılan)

- Tırnak “ ”, iç tırnak ‘ ’, kesme işareti ’ (Ankara’da). Typst'te düz `"` ve `'` yaz; `lang: "tr"` doğru
  işarete çevirir.
- Birleşik sözcükte kısa çizgi (-); sayı aralığında en çizgi (1990–2000, s. 12–15); ara sözde boşluklu en
  çizgi ( – ); konuşma satırının başında uzun çizgi (— ).
- Üç nokta tek karakterdir (…) ve önceki sözcüğe bitişiktir. Noktalamadan önce boşluk yok, sonra bir boşluk.
- Yüzde işareti önde ve bitişik (%25); ondalık virgül (3,5), binlik nokta (1.000).
- Bölünmez boşluk (Typst'te `~`): unvan ile ad (Prof.~Dr.~Ad), sayı ile birim (5~kg), s.~12.
- Satır sonunda Türkçe hece bölmesi (`lang: "tr"` ile kendiliğinden). Art arda üçten çok tireli satır olmaz.
- Paragraf iki yana yaslı, ilk satır girintili; başlıktan sonraki ilk paragraf girintisiz; paragraf arası boşluk yok.
- Bölüm sağ (tek) sayfada açılır; bölüm açılışında üst bilgi, boş sayfada numara ve üst bilgi basılmaz.
- Dul satır (paragrafın son satırı yeni sayfanın başında) ve öksüz satır (ilk satırı sayfa dibinde) olmaz;
  ara başlık sayfa dibinde yalnız kalmaz. Şablon bunları önler, yine de önizlemede bak.

## Bilinen tuzaklar

- Typst'in `upper()` ve `lower()` işlevleri Türkçe i/İ ve ı/I'yı bozar ("İçindekiler" → "IÇINDEKILER").
  Büyük harf gerekiyorsa metni elle büyük harfle yaz.
- `#`, `$`, `@`, `*`, `_`, `<` ve ters tırnak Typst'te özeldir; metinde geçerse `\` ile kaçır (`\#`, `\$`).
- Yazı tipinde Türkçe harf yoksa Typst sessizce başka yazı tipine geçer; `pdf_kontrol.py --yazi-tipi` bunu
  yakalar. Yeni yazı tipini `typst fonts` ile bul, örnek sayfada ğüşıöç ĞÜŞİÖÇ âîû harflerini sına.
- Ticari yazı tipinin lisansı yayınevinindir: yazı tipi dosyasını kitap klasörüne kopyalama, dağıtma.
- Görseller basıldığı genişlikte en az 300 dpi olmalı; tek renk kitapta gri tonlamalı. Düşük çözünürlüklü
  görseli büyütme, kullanıcıya bildir.

## Tashih ve kapak

- Yazardan, hocalardan ya da editörden gelen düzeltmeler: `tashih` skill'i (işaretli PDF, izli Word, liste).
- Kapak önerisi ve tam kapak (ön + sırt + arka): `kapak` skill'i.

## Matbaa hazırlığı

- Sayfa sayısı forma katı olmalı (genelde 16). Eksik sayfayı kitabın sonuna boş sayfa olarak eklemeden önce sor.
- Künyede `[DOLDUR]` kalmamalı; ISBN ve sertifika numaralarını kullanıcı verir, uydurma.
- Yazı tipleri gömülü olmalı (Typst gömer). Matbaa PDF/X gibi bir standart isterse `typst compile --help`
  içindeki `--pdf-standard` seçeneklerine bak; istenen yoksa dönüşümü matbaaya sor.
- Kapak `kapak` skill'inin işidir; son sayfa sayısını oraya ver (sırt kalınlığı ona bağlı).
- Teslim dosyası adı: `KitapAdi_ic_135x210_YYYYAAGG.pdf`; yanına kısa teslim notu (ölçü, sayfa, renk, yazı tipleri).

## Üslup

Yazara, hocalara ve matbaaya giden her metin yayınevi editörünün sesiyle yazılır: kısa, nazik, resmî. Emoji,
abartılı övgü, "yapay zekâ" ya da araç adı geçmez.

## Ne zaman sorulur

- Ölçü, yazı tipi, punto gibi kararlar `yayinevi.md`'de yoksa.
- Metinde içerik değişikliği gerektiren her şey (yazım, eksik ya da yinelenen paragraf, bölüm sırası).
- Boş sayfa ekleme, künye bilgileri, kaynak dosyanın hangisi olduğu belirsizse.
