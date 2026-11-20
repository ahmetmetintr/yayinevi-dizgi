---
name: dizgi
description: Kitap iç sayfa dizgisi ve baskı öncesi hazırlık. Word (.docx) ya da metin dosyasından Typst ile baskıya hazır PDF, Türkçe tipografi düzeltmesi, yayınevi düzeni (özet, künye, başlık adları, tablo notları), dizgi kontrolü, tashih (düzeltme) işleme, künye ve içindekiler, matbaa hazırlığı, jenerik ve bölüm bölüm PDF teslimi, atıf bülteni dosyası. Kullanıcı "dizgi", "mizanpaj", "kitabı diz", "baskıya hazırla", "matbaaya gönder", "tashih", "düzeltmeleri işle", "künye", "içindekiler", "dul satır", "forma", "jenerik", "bölüm PDF'leri", "atıf bülteni" dediğinde ya da bir kitap dosyası verdiğinde kullan.
---

# Dizgi

## Altın kural: yazarın metnine dokunma

- Sözcük değiştirme, yazım düzeltme, kısaltma, "iyileştirme" yok. Yazım hatası ya da tutarsızlık görürsen
  düzeltme: kitabın `NOTLAR.md` dosyasındaki "Tashih önerileri" listesine yaz ve kullanıcıya göster. Bütün metnin
  imla taraması `imla` becerisinin işidir (rapor + sarı işaretli prova; metne yazmaz).
- Yayınevi düzeni de biçimdir: bölüm başındaki özet ve anahtar kelimelerin çıkarılması, künyede e-posta ve ORCID
  yazımı, Giriş/Sonuç/Kaynaklar başlık adları, tablo altı notlar. Elle değil `araclar/duzenle.py` ile yapılır;
  önce kuru çalıştırma raporu kullanıcıya gösterilir.
- Şekil ve tablo yazısı biçimdir, metin değil: etiket yayınevi biçimine getirilir. Vizetek: kalın "Tablo 1." /
  "Şekil 1." (noktalı; telifte "Tablo 2.1."), ardından boşluk ve düz başlık; tablo yazısı üstte ortalı ve
  girintisiz, şekil yazısı altta ortalı, 10 pt italik. Yazarın "Tablo 1", "Tablo 1:", "Şekil 3:Başlık" yazımları buna getirilir;
  Typst'in kendi numarası kapatılır (`#figure(numbering: none, …)`), yoksa "Şekil 1. Şekil 1:" çift basılır.
  Etiket sözcüğünü (Resim, Figür → Şekil) değiştirmek metin içi atıflara da dokunur: kullanıcıya sor.
- Noktalama ve boşluk düzeltmesini elle değil `araclar/tipografi.py` ile yap. Betik harf dizisi ya da Typst
  yapısı değişecekse dosyaya yazmaz.
- Yazarın dosyaları `kaynak/` klasöründe kalır ve hiç değiştirilmez.

## Yerler

Skill klasörü (yüklenirken "Base directory" satırında yazar). Skill klasöründe hiçbir dosyayı değiştirme:
eklenti güncellenince değişiklik silinir.
- `sablon/`: `kitap.typ` (şablon), `on-sayfalar.typ`, `ogeler.typ` (metinde kullanılan yardımcılar),
  `harita.typ` (kitabın bölüm haritası: jenerik, bölüm ve kaynakça sayfaları), `profiller.typ` (klasik,
  vizetek-telif, vizetek-editorlu), `ana-dosya.typ` (yeni kitabın ana dosyası), `yayinevi.md` (genel kural
  şablonu), `yayinevi-vizetek.md` (Vizetek kuralları, ön doldurulmuş).
- `araclar/`: `tipografi.py`, `duzenle.py` (yayınevi düzeni; kuralları `duzenle_kurallari.py`), `tablo_kur.py`
  (boşlukla dizilmiş tablo → tablo taslağı), `pdf_kontrol.py`, `kaynakca_denetle.py`, `bolum_denetle.py`,
  `bolum_pdfleri.py` (jenerik, bölüm PDF'leri, atıf bülteni), `e_kitap.py`.

Çalışma klasörü (genelde Belgeler/Dizgi; Claude Code burada açılır): `CLAUDE.md` · `yayinevi.md` · her kitaba bir
klasör. **Her işte önce çalışma klasöründeki `yayinevi.md`'yi oku; oradaki değer bu dosyadaki varsayılanı
geçersiz kılar.** Dosya yoksa `sablon/yayinevi.md`'yi oraya kopyala ve kullanıcıya kuralları doldurmayı öner.

Python'u Windows'ta `py`, macOS'ta `python3` ile çağır; araçlar bu skill'in `araclar/` klasöründedir. Kitap klasörünün düzeni:

```
Kitap-Adi/
  kaynak/           yazardan gelen dosyalar (salt okunur)
  metin/metin.typ   dizilecek metin (editörlü kitapta bölümleri sırayla #include eder: bolum-01.typ …)
  gorseller/
  sablon/*.typ      şablon dosyalarının bu kitaba kopyası (kitap kendi sürümünü taşır)
  kitap.typ         ana dosya (ana-dosya.typ'den)
  cikti/            PDF'ler (kitap-YYYY-AA-GG.pdf) ve onizleme/
  tashih/           düzeltme turları (tashih skill'i)
  kapak/            kapak eskizleri ve tam kapak (kapak skill'i)
  NOTLAR.md         kararlar · terim listesi · tashih önerileri · açık sorular · değişiklik kaydı
```

## İş akışı

1. **Proje aç.** Klasörleri kur; skill'deki `sablon/` içindeki bütün `.typ` dosyalarını kitabın `sablon/`
   klasörüne, `ana-dosya.typ`'yi kitap klasörüne `kitap.typ` adıyla kopyala. Profili `yayinevi.md`'den seç
   (`..vizetek-telif` gibi); kitap türünü (telif / editörlü) kullanıcıya sor. Künyeyi `yayinevi.md`'deki
   sırayla doldur; bilinmeyeni `[DOLDUR: …]` bırak. Logo varsa Dizgi klasöründen kitap klasörüne kopyala.
2. **Word'ü al.** `pandoc "kaynak/<dosya>.docx" -t typst --wrap=none --extract-media=gorseller -o metin/metin.typ`
   Eski `.doc` dosyası önce LibreOffice ile çevrilir (macOS textutil tablo ve dipnot yapısını bozar):
   `soffice --headless --convert-to docx --outdir metin/donusum "kaynak/<dosya>.doc"`.
   Sonra denetle ve raporla: başlıklar (`=` bölüm, `==` ara başlık) ve düzeyleri; dipnot sayısı Word'dekiyle aynı
   mı; görsel ve tablo sayısı; stil verilmeden elle yapılmış başlıklar (tek satırlık kalın paragraflar); boş
   paragraflar ve elle sayfa sonları; `- ` ile başlayıp yanlışlıkla liste olmuş konuşma satırları; "Tablo N."
   yazısı olup tablosu olmayan yerler (tablo Word'de boşluk ya da sekmeyle dizilmiş: tablo nesnesi yoktur,
   dönüştürücü çizecek tablo bulamaz; `py tablo_kur.py metin/donusum/<dosya>.docx --tablo N` taslak verir, harfleri
   denetler; taslak Word'e bakılarak kullanıcıyla düzeltilip düz metnin yerine konur). Sözcük
   sayısını `pandoc kaynak.docx -t plain` çıktısıyla karşılaştır; belirgin kayıp varsa dur. Yapı düzeltmesini
   (başlık düzeyi, boş satır) önce listele, onayla uygula; metne dokunma.
   Typst `unknown variable: horizontalrule` derse `#horizontalrule` yerine `#sahne-arasi` yaz. Her metin
   dosyasının başına `#import "../sablon/ogeler.typ": *` ekle.
   **Editörlü kitap:** `kaynak/` içinde bölüm başına bir Word olur. Her birini `metin/bolum-NN.typ`'ye çevir
   (sırayı editöre sor). Her bölümün başındaki başlık ve yazar satırlarını `#bolum([Başlık], aciklama: […],
   yazarlar: (("Ad SOYAD", [Unvan, Kurum, Bölüm. ORCID: 0000-0000-0000-0000]), …))` biçimine (künye her zaman
   dipnottadır, e-posta yazılmaz; yazar künyeyi adının altına metin içinde yazdıysa oradan alınır), sonundaki kaynak listesini
   `#kaynakca[ … ]` bloğuna al (her kaynak ayrı paragraf). Kaynakça bölüm sonunda **yeni sayfadan** başlar
   (`#kaynakca` bunu kendisi yapar; metin biter bitmez kaynakçaya geçilmez). Bir bölümde birkaç yazı ve
   kaynakça varsa her biri `#kaynakca(baslik: [Kaynaklar], duzey: 3)[…]` olur. Yazar bilgisi Word'de dipnottaysa oradan al; eksik
   bilgiyi uydurma, `[DOLDUR]` bırak. `metin/metin.typ` ön sözü ve bölümleri sırayla `#include` eder.
   **Ön sayfalar (Vizetek profilleri):** ön söz başlığı `#numarasiz[Ön Söz]`, içindekiler ön sözden sonra
   `#icindekiler-sayfasi()`, hemen ardından `#ana-metin-baslat()`: sayfa numarası içindekilerden sonra 1'den başlar
   (ön söz içindekilerde romen rakamıyla), kitabın üst bilgisi 1. bölümün ilk sayfasından sonra başlar. Kısım
   varsa `#kisim("1")[Ad]` ("KISIM 1"; bölümler "1. Bölüm" etiketli olduğundan grup için "BÖLÜM" kullanma).
   **Yayınevi düzeni (editörlü kitap):** `py duzenle.py "metin/bolum-*.typ"` (kuru çalıştırma) → raporu göster →
   onayla `--uygula`. Bölüm başındaki özet ve anahtar kelimeler çıkar; künyede e-posta silinir, ORCID
   `ORCID: 0000-…` olur; tümü büyük GİRİŞ / SONUÇ / KAYNAKLAR baş harfi büyük olur; kaynakça başlığı kitapta en
   çok kullanılan ada (Kaynaklar ya da Kaynakça) getirilir; şekil ve tablodan sonraki "Not.", "Kaynak:"
   paragrafları `#notlu-sekil(figure(…))[…]` ile şekle bağlanır. "Elle bakılacaklar" listesini (düzensiz özet,
   metin içinde kalmış künye, boşlukla dizilmiş tablo, tümü büyük ara başlık) kullanıcıya sor; kendiliğinden düzeltme.
3. **Tipografi.** `py tipografi.py metin/metin.typ` (kuru çalıştırma) → raporu göster → onayla `--uygula`.
   Çizgi tercihleri `yayinevi.md`'den: `--ara-cizgi en|em`, `--konusma-cizgisi em|en`.
4. **Diz.** `typst compile kitap.typ cikti/kitap-YYYY-AA-GG.pdf` — uyarıları oku ve çöz.
5. **Bak.** `typst compile kitap.typ "cikti/onizleme/s{p}.png" --ppi 50 --pages 1-16` (gerekirse başka sayfalar).
   Görüntüleri kendin incele: bölüm açılışları, boş sayfalar, üst bilgiler, künye, içindekiler.
6. **Kontrol.** `py pdf_kontrol.py cikti/<pdf> --olcu 160x240 --tek-renk --yazi-tipi "<yazı tipi>"`
   (değerler `yayinevi.md`'den), sonra uyarı veren sayfaları önizleyip bak. Akademik kitapta ayrıca:
   `py kaynakca_denetle.py metin/*.typ` (internet varsa `--crossref`: DOI gerçekten var mı, yıl ve ilk yazar
   tutuyor mu) ve editörlü kitapta `py bolum_denetle.py cikti/<pdf> metin/*.typ --sayfa 10-25` (bölüm
   uzunluğu, yazar bilgisi, ORCID sağlaması). Bulunan kaynakça ve yazar sorunlarını düzeltme: editöre liste ver.
7. **Raporla.** Kısa tablo: sayfa sayısı, uyarılar, yapılanlar, kullanıcıdan beklenenler. `NOTLAR.md`'yi güncelle.

## Tablolar ve şekiller (şablonda hazır)

- Tablo bir sayfaya sığıyorsa bölünmez; başlığıyla birlikte sonraki sayfaya geçer. Sığmıyorsa profildeki küçük
  puntolar denenir (Vizetek: 10 → 9 → 8,5 pt); yine sığmayan tablo bölünür, başlığı ilk satırlarıyla aynı
  sayfada kalır, başlık satırı her sayfada yinelenir. Bir tabloya elle punto: `#tablo-puntosu(9pt)[#figure(…)]`.
- Tablo içi metin girintisizdir (paragraf ve madde imi). Tablo ve şekil altı not ve kaynak 9 pt, girintisiz, iki
  yana yaslı: `#notlu-sekil(figure(…))[#emph[Not.] …]` (not şekille birlikte kalır) ya da tek başına `#sekil-notu[…]`.
- Bağlantılar (metin, kaynakça, dipnot) siyah ve altı çizgisizdir; Word'den altı çizili gelen adres de düz basılır.

## Teslim PDF'leri: jenerik, bölümler, atıf bülteni

Son PDF'ten sonra (kitap klasöründe): `py bolum_pdfleri.py kitap.typ cikti/<son>.pdf` → `cikti/teslim/`:
`<Kitap>, Jenerik.pdf` (iç kapak, künye, ön söz, içindekiler; boş sayfalar atılır), `bolumler/<Yazar>, <Bölüm
Adı>.pdf` (her bölüm; Vizetek'in dosya adı örneği) ve `<Kitap>, Atıf bülteni.pdf` (jenerik + her bölümün ilk
sayfası ve kaynakçası, yer imli). Sayfalar tahmin edilmez: şablon her derlemede `<dizgi-harita>` bırakır, araç onu
Typst'ten (`typst eval`, eskisinde `typst query`) okur; PDF'in sayfa sayısı haritayla tutmazsa durur (eski PDF). Derlemede `--input` verildiyse
araca da aynısı verilir. Kaynakçası `#kaynakca` ile yazılmamış bölüm bültene yalnız ilk sayfasıyla girer: uyarıyı
kullanıcıya söyle.

## E-kitap

İç PDF'i `e-kitap: true` ile derle (bağlantılar tıklanır kalır; renk serbest, `--tek-renk` kullanma). Sonra:
`py e_kitap.py cikti/<iç>.pdf --tam-kapak kapak/tam-kapak.pdf --genislik 160 --yukseklik 240 --tasma 3 --baslik "…" --yazar "…" --cikti cikti/<kitap>-e-kitap.pdf`
Künyede E-ISBN, DOI ve e-kitap satırları (Materyal Türü, Elektronik Yayın Formatı) dolu olmalı.

## Türkçe dizgi kuralları (varsayılan)

- Tırnak “ ”, iç tırnak ‘ ’, kesme işareti ’ (Ankara’da). Typst'te düz `"` ve `'` yaz; `lang: "tr"` doğru
  işarete çevirir.
- Birleşik sözcükte kısa çizgi (-); sayı aralığında en çizgi (1990–2000, s. 12–15); ara sözde boşluklu en
  çizgi ( – ); konuşma satırının başında uzun çizgi (— ).
- Üç nokta tek karakterdir (…) ve önceki sözcüğe bitişiktir. Noktalamadan önce boşluk yok, sonra bir boşluk.
- Yüzde işareti önde ve bitişik (%25); ondalık virgül (3,5), binlik nokta (1.000).
- Bölünmez boşluk (Typst'te `~`): unvan ile ad (Prof.~Dr.~Ad), sayı ile birim (5~kg), s.~12.
- Satır sonunda Türkçe hece bölmesi (`lang: "tr"` ile kendiliğinden). Art arda üçten çok tireli satır olmaz.
- Paragraf iki yana yaslı, ilk satır girintili; başlıktan sonraki ilk paragraf girintisiz; paragraf arası boşluk yok
  (profil farklı diyebilir: Vizetek'te her paragraf girintili, aralarında 6 pt).
- Bölüm sağ (tek) sayfada açılır; bölüm açılışında üst bilgi, boş sayfada numara ve üst bilgi basılmaz.
- Dul satır (paragrafın son satırı yeni sayfanın başında) ve öksüz satır (ilk satırı sayfa dibinde) olmaz;
  ara başlık sayfa dibinde yalnız kalmaz. Şablon bunları önler, yine de önizlemede bak.

## Bilinen tuzaklar

- Typst'in `upper()` ve `lower()` işlevleri Türkçe i/İ ve ı/I'yı bozar ("İçindekiler" → "IÇINDEKILER").
  Büyük harf için `ogeler.typ`'deki `tr-buyuk(...)` kullanılır (şablon başlıklarda kendisi kullanır).
- `#`, `$`, `@`, `*`, `_`, `<` ve ters tırnak Typst'te özeldir; metinde geçerse `\` ile kaçır (`\#`, `\$`).
- Yazı tipinde Türkçe harf yoksa Typst sessizce başka yazı tipine geçer; `pdf_kontrol.py --yazi-tipi` bunu
  yakalar. Yeni yazı tipini `typst fonts` ile bul, örnek sayfada ğüşıöç ĞÜŞİÖÇ âîû harflerini sına.
- Ticari yazı tipinin lisansı yayınevinindir: yazı tipi dosyasını kitap klasörüne kopyalama, dağıtma.
- Görseller basıldığı genişlikte en az 300 dpi olmalı; tek renk kitapta gri tonlamalı. Düşük çözünürlüklü
  görseli büyütme, kullanıcıya bildir.

## Tashih, kapak ve DOI

- Yazardan, hocalardan ya da editörden gelen düzeltmeler: `tashih` skill'i (işaretli PDF, izli Word, liste).
- Kapak önerisi ve tam kapak (ön + sırt + arka): `kapak` skill'i.
- Kitap ve bölüm DOI'lerinin Crossref kaydı (son PDF'ten): `doi` skill'i.
- Yayımlanmış kitapların atıf dizini (künye + bölümün ilk sayfası + kaynakça, kaynak tablosu): `atif` skill'i.
  Bu kitle dizilen kitabın atıf bülteni dosyası dizgi bitince `bolum_pdfleri.py` ile hazırlanır (yukarıda).

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
