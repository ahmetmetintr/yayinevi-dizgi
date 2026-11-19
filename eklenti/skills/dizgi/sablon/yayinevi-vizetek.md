# Yayınevi dizgi kuralları — Vizetek Yayıncılık

> Bu dosya Dizgi çalışma klasöründe durur. Dizgi, tashih ve kapak skill'leri onu her işte okur; buradaki değer
> skill'lerin varsayılanını geçersiz kılar. "Yayınevimizin kurallarını öğren" promptuyla gözden geçirilir.
> Durum: ÖN DOLDURULDU (19.11.2026) — kaynaklar: vizetek.com.tr, Vizetek 2026 Yazım Kılavuzu, 16×24 Örnek
> Kitap Yazım Şablonu, Vizetek'in dizdiği bir kitabın ölçümü. [TEYİT] yazan yerleri yayınevi onaylamalı.

## Yayınevi
- Ad: Vizetek Yayıncılık (Vizetek Yayıncılık Sanayi ve Ticaret Limited Şirketi), 2018'den beri, Ankara
- Yayıncı sertifika no: 41575
- Künye iletişim: Seyranbağları Mah. İncesu Cad. 10/2 Çankaya/ANKARA · Tel. (0312) 482 00 11 ·
  Web www.vizetek.com.tr · E-posta vizetekyayincilik@gmail.com
- Telif notu (künyede ortalı, küçük): "Copyright © Vizetek. Bu kitabın basım, yayım ve satış hakları Vizetek
  Yayıncılık Sanayi ve Ticaret Limited Şirketine aittir. Vizetek Yayıncılık'ın izni alınmadan kitabın tümü ya da
  bölümleri, kapak tasarımı, elektronik, mekanik, fotokopi, manyetik, kayıt ya da başka yöntemlerle
  çoğaltılamaz, basılamaz, dağıtılamaz. Bu kitap, basılı ve elektronik (e-kitap) formatlarında
  yayımlanmaktadır. Kitap içeriğinin tüm sorumluluğu yazar(lar)ına aittir."
- Logo: Dizgi klasörüne `logo.png` olarak konur (yayınevinden alınır).
- DOI: her kitaba bir DOI, bölümlere ayrı DOI yok (Crossref). Biçim: `10.54637/vizetek.<ISBN, tiresiz>`.
- Yayın alanları: eğitim bilimleri, sağlık bilimleri (diş hekimliği, hemşirelik, eczacılık, fizyoterapi),
  sosyal ve beşerî bilimler, fen ve mühendislik, spor, hukuk, ilahiyat, filoloji, güzel sanatlar, ziraat,
  mimarlık, veterinerlik; YDS-YÖKDİL ve çocuk kitapları. Ağırlık editörlü akademik kitaplarda (bölüm çağrısı).
- Yayın türü: basılı + e-kitap ya da yalnız e-kitap (PDF). Bölüm teslimi ile basım arası yaklaşık bir ay.

## Typst profili
- Telif kitap (tek ya da birkaç yazar): `vizetek-telif` — "BÖLÜM 1" etiketi, numaralı ara başlıklar (1.1.),
  kısım sayfaları, Tablo 2.1. numarası.
- Editörlü kitap (bölüm yazarları ayrı): `vizetek-editorlu` — bölüm başlığı tümü büyük harf, yazarlar sağa
  yaslı (`#bolum(...)`), unvan/kurum/ORCID dipnotta (*, **, ***), tablo ve dipnot numarası her bölümde 1'den.
- Ön sayfalar: 1 iç kapak (logo) · 2 künye · takdim/ön söz · içindekiler (ön sözden sonra, `#icindekiler-sayfasi()`).
  Sayfa numarası ön sözde 1'den başlar (`#ana-metin-baslat()` ön sözden hemen önce).

## Kitap ölçüleri (profilde hazır)
| Tür | Kesim | Kenar boşlukları | Not |
| --- | --- | --- | --- |
| Bütün kitaplar | 160 × 240 mm | üst 25, alt 25, sağ 20, sol 20 mm (tek ve çift sayfada aynı) | üst bilgi 5 mm yukarıda, sayfa no 8 mm aşağıda |

## Yazı (profilde hazır)
- Bölüm açılışı (telif): "BÖLÜM 1" 24 pt ve bölüm adı 20 pt, ortalı, üst kenar boşluğundan başlar; dizilen
  kitapta Fraunces (ücretsiz, OFL) kullanılmış, bilgisayarda yoksa Times New Roman. [TEYİT: her kitapta mı]
- Gövde: Times New Roman 11 pt, satır aralığı 1,15 (= 14,5 pt adım), paragraf öncesi 6 pt, ilk satır girintisi
  0,5 cm (başlıktan sonraki paragraf dahil), iki yana yaslı; heceleme isteğe bağlı (açık).
- Tablo: 10 pt; başlık satırı açık gri zeminli; tablo başlığı tablonun ÜSTÜNDE, sola yaslı, 10 pt
  ("Tablo 1." / telifte "Tablo 2.1."). Şekil başlığı şeklin ALTINDA, ortalı, 10 pt. [TEYİT: başlık italik mi
  kalın mı — dizilen kitapta italik, yazar şablonunda kalın]
- Dipnot: 9 pt. Kaynakça: 9 pt, asılı girinti 1,25 cm, APA 7; her kaynağın sonunda DOI zorunlu.
- Üst bilgi: iki satır ortalı — kitap adı TÜMÜ BÜYÜK (Calibri 9 pt) + alt başlık italik, altında kısa çizgi;
  bölüm açılışında ve boş sayfada basılmaz. Sayfa numarası alt orta (Lato 8 pt; yoksa Calibri).
- Başlık düzeyleri (editörlü, Yazım Kılavuzu): 1. düzey ortalı, kalın, TÜMÜ BÜYÜK · 2. düzey sola yaslı, kalın,
  Sözcükler Büyük Harfle · 3. düzey girintili, kalın, ilk sözcük büyük · 4. düzey girintili, kalın ·
  5. düzey girintili, düz. Hepsi 11 pt.

## Editörlü kitap kuralları (Yazım Kılavuzu 2026)
- Bölüm uzunluğu: kaynakça dahil ortalama 10–25 sayfa (`bolum_denetle.py --sayfa 10-25`).
- Bölüm başında: başlık, altında yazar(lar) unvanıyla; dipnotta üniversite, fakülte/bölüm, ORCID, e-posta.
- Görseller: özgün biçimde (JPG) ve yüksek çözünürlükte ayrıca gönderilir; dosya adı metindeki numarayla aynı.
- Ön söz: kitabı tanıtan, hazırlanış amacını anlatan kavramsal çerçeve (editörden).
- Bölüm sonunda isteğe bağlı "yazar hakkında" yazısı.
- Dil: TDK Yazım Kılavuzu.

## Noktalama
- Ara söz çizgisi: en ( – ) → tipografi.py --ara-cizgi en
- Konuşma çizgisi: uzun (—) → tipografi.py --konusma-cizgisi em
- Tırnak: “ ” (iç tırnak ‘ ’)

## Sayfa düzeni
- Bölüm başı: sağ sayfa [TEYİT: yalnız e-kitap baskılarında boş sayfa istenmiyorsa `bolum-sag-sayfada: false`]
- Forma: 16 sayfa · İç baskı: tek renk (siyah) · E-kitap: renkli olabilir, bağlantılar açık (`e-kitap: true`)

## Kapak
- Arka kapak tanıtım yazısı: 100–150 sözcük, editörden (yazar ya da editör yazar; uydurulmaz)
- Sırt yazısının yönü: [TEYİT] · Sırtta sıra: yazar/editör · kitap adı · logo
- Taşma payı: 3 mm · Renk: CMYK · ISBN barkodu arka kapakta (yayınevinden)
- Kapak tasarımı ve mizanpaj künyede ayrı satır: "Kapak Tasarımı ve Mizanpaj: Ad SOYAD"

## Tashih
- Yayınevi kuralı: kitap dizgiye girdikten sonra imla (yazım) düzeltmesi yapılmaz; yazar metni dizgiden önce
  denetlemelidir. Dizgiden sonra gelen düzeltmede imla maddeleri ayrılır ve editöre sorulur; içerik ve dizgi
  hataları işlenir. [TEYİT: araç düzeltmeyi hızlı işlediği için bu kural gevşetilecek mi]
- Yazara giden düzeltme biçimi: PDF üzerinde yorum; her yorum tek başına okunur
  ("Değiştir: «eski» → «yeni»", "Ekle: …", "Sil: «…»", "Biçim: …")
- Yorumlarda görünecek ad: Vizetek Yayıncılık

## Künye (Vizetek düzeni, sırayla)
ISBN · E-ISBN · DOI · telif notu · Yayın Tasarımcısı / Koordinatörü · Kapak Tasarımı ve Mizanpaj · Baskı
(Şehir | Ay Yıl) · e-kitapta: Materyal Türü: Elektronik Kitap (Çevrim içi / Web tabanlı), Elektronik Yayın
Formatı: PDF, Elektronik Yayın Tipi: Adobe Ebook Reader · logo · adres, telefon, web, e-posta · Yayıncı
Sertifika No: 41575

## Notlar
-
