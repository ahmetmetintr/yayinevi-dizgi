# Yayınevi dizgi kuralları — Vizetek Yayıncılık

> Bu dosya Dizgi çalışma klasöründe durur. Dizgi, tashih ve kapak skill'leri onu her işte okur; buradaki değer
> skill'lerin varsayılanını geçersiz kılar. "Yayınevimizin kurallarını öğren" promptuyla gözden geçirilir.
> Durum: ÖN DOLDURULDU (19.11.2026), Vizetek'in dizgi revizyon istekleriyle güncellendi (20.11.2026) — kaynaklar:
> vizetek.com.tr, Vizetek 2026 Yazım Kılavuzu, 16×24 Örnek Kitap Yazım Şablonu, Vizetek'in dizdiği bir kitabın
> ölçümü, "Dizgi İçin Revize Edilmesi Gereken Komutlar ve Öneriler" (Vizetek, 20.11.2026). [TEYİT] yazan yerleri
> yayınevi onaylamalı.

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
- DOI: kitaba ve editörlü kitapta her bölüme ayrı DOI (Crossref). Ayrıntı aşağıda, "DOI ve Crossref".
- Yayın alanları: eğitim bilimleri, sağlık bilimleri (diş hekimliği, hemşirelik, eczacılık, fizyoterapi),
  sosyal ve beşerî bilimler, fen ve mühendislik, spor, hukuk, ilahiyat, filoloji, güzel sanatlar, ziraat,
  mimarlık, veterinerlik; YDS-YÖKDİL ve çocuk kitapları. Ağırlık editörlü akademik kitaplarda (bölüm çağrısı).
- Yayın türü: basılı + e-kitap ya da yalnız e-kitap (PDF). Bölüm teslimi ile basım arası yaklaşık bir ay.

## Typst profili
- Telif kitap (tek ya da birkaç yazar): `vizetek-telif` — "BÖLÜM 1" etiketi, numaralı ara başlıklar (1.1.),
  kısım sayfaları, Tablo 2.1. numarası.
- Editörlü kitap (bölüm yazarları ayrı): `vizetek-editorlu` — her bölüm yeni (sağ) sayfada, başlığın üstünde
  "1. Bölüm" etiketi; bölüm başlığı tümü büyük harf, yazarlar sağa yaslı (`#bolum(...)`), künye (unvan, kurum,
  ORCID) her zaman dipnotta (*, **, ***), e-posta yazılmaz; tablo ve dipnot numarası her bölümde 1'den.
- Ön sayfalar: 1 iç kapak (logo) · 2 künye · takdim/ön söz · içindekiler (ön sözden sonra, `#icindekiler-sayfasi()`).
  Sayfa numarası içindekilerden sonra 1'den başlar (`#ana-metin-baslat()` içindekilerden hemen sonra); ön söz
  içindekilerde romen rakamıyla. Kitabın üst bilgisi 1. bölümün ilk sayfasından sonra başlar, kitap sonuna kadar
  sürer; ön söz ve içindekilerde basılmaz.
- Jenerik şablonu: [TEYİT: Vizetek'in jenerik (iç kapak ve künye) şablonu bekleniyor; gelene kadar şablondaki
  Vizetek künye düzeni kullanılır].

## Kitap ölçüleri (profilde hazır)
| Tür | Kesim | Kenar boşlukları | Not |
| --- | --- | --- | --- |
| Bütün kitaplar | 160 × 240 mm | üst 25, alt 25, sağ 20, sol 20 mm (tek ve çift sayfada aynı) | üst bilgi 5 mm yukarıda, sayfa no 8 mm aşağıda |

## Yazı (profilde hazır)
- Bölüm açılışı (telif): "BÖLÜM 1" 24 pt ve bölüm adı 20 pt, ortalı, üst kenar boşluğundan başlar; dizilen
  kitapta Fraunces (ücretsiz, OFL) kullanılmış, bilgisayarda yoksa Times New Roman. [TEYİT: her kitapta mı]
- Gövde: Times New Roman 11 pt, satır aralığı 1,15 (= 14,5 pt adım), paragraf öncesi 6 pt, ilk satır girintisi
  0,5 cm (başlıktan sonraki paragraf dahil), iki yana yaslı; heceleme isteğe bağlı (açık).
- Tablo: içi 10 pt; çok büyük ve dağınık duran tablo 9 ya da 8,5 pt (şablon sığmayan tabloda kendisi dener;
  elle `#tablo-puntosu(9pt)[…]`); tablo içi metin girintisiz; başlık satırı açık gri zeminli. Tablo başlığı
  tablonun ÜSTÜNDE, girintisiz ve ortalı, 10 pt ("Tablo 1." / telifte "Tablo 2.1."). Şekil başlığı şeklin
  ALTINDA, ortalı, 10 pt. [TEYİT: başlık italik mi kalın mı — dizilen kitapta italik, yazar şablonunda kalın]
- Tek sayfaya sığan tablo bölünmez; tablo ve şekil başlığı tablodan/şekilden ayrı sayfada kalmaz.
- Tablo ve şekil altı not ve kaynak: 9 pt, girintisiz, iki yana yaslı (`#notlu-sekil`).
- Bağlantı adresleri (metin, kaynakça, dipnot): siyah, altı çizgisiz.
- Dipnot: 9 pt. Kaynakça: 9 pt, asılı girinti 1,25 cm, APA 7; her kaynağın sonunda DOI zorunlu.
- Üst bilgi: iki satır ortalı — kitap adı TÜMÜ BÜYÜK (Calibri 9 pt) + alt başlık italik, altında kısa çizgi;
  bölüm açılışında ve boş sayfada basılmaz. Sayfa numarası alt orta (Lato 8 pt; yoksa Calibri).
- Bölüm alt başlıkları (editörlü): hepsi 3. düzey gibi sola yaslı, girintisiz, kalın, üstte ve altta aynı
  boşluk (Vizetek, 20.11.2026; Yazım Kılavuzu'ndaki ortalı/girintili düzeylerin yerine). Hepsi 11 pt.
  [TEYİT: "üstten ve alttan 0,5" — şablon 3. düzeyin boşluğunu (üstte ≈ 0,58 cm, altta ≈ 0,31 cm) bütün
  düzeylere uyguladı; 0,5 cm ya da 0,5 satır kesin isteniyorsa bildirilir]
- Başlık adları kitapta tektir: kaynakça başlığı hep aynı (Kaynaklar ya da Kaynakça, kitapta çoğunlukta olan);
  tümü büyük GİRİŞ / SONUÇ / KAYNAKLAR baş harfi büyük yazılır (`duzenle.py`).

## Editörlü kitap kuralları (Yazım Kılavuzu 2026)
- Bölüm uzunluğu: kaynakça dahil ortalama 10–25 sayfa (`bolum_denetle.py --sayfa 10-25`).
- Bölüm başında: başlık, altında yazar(lar) unvanıyla; dipnotta üniversite, fakülte/bölüm, ORCID, e-posta.
- Görseller: özgün biçimde (JPG) ve yüksek çözünürlükte ayrıca gönderilir; dosya adı metindeki numarayla aynı.
- Ön söz: kitabı tanıtan, hazırlanış amacını anlatan kavramsal çerçeve (editörden).
- Bölüm sonunda isteğe bağlı "yazar hakkında" yazısı.
- Bölüm başındaki özet ve anahtar kelimeler dizgiye girmez (`duzenle.py` çıkarır).
- Künyede ORCID şöyle yazılır: `ORCID: 0009-0009-5384-6169` ("Orcid id", "Orcid no", orcid.org adresi değil).
- Kaynakça her bölümde yeni sayfadan başlar.
- Dil: TDK Yazım Kılavuzu.

## Noktalama
- Ara söz çizgisi: en ( – ) → tipografi.py --ara-cizgi en
- Konuşma çizgisi: uzun (—) → tipografi.py --konusma-cizgisi em
- Tırnak: “ ” (iç tırnak ‘ ’)

## Sayfa düzeni
- Bölüm başı: sağ sayfa [TEYİT: yalnız e-kitap baskılarında boş sayfa istenmiyorsa `bolum-sag-sayfada: false`]
- Forma: 16 sayfa · İç baskı: tek renk (siyah) · E-kitap: renkli olabilir, bağlantılar açık (`e-kitap: true`)

## Teslim (dizgi sonunda)
- Kitabın jeneriği ve her bölüm ayrı PDF; bölüm dosyasının adı "Yazar İsmi, Bölüm Adı" (`bolum_pdfleri.py`).
- Atıf bülteni için tek dosya: kitap jeneriği + her bölümün ilk sayfası ve kaynakçası (aynı araç).

## Kapak
- Arka kapak tanıtım yazısı: 100–150 sözcük, editörden (yazar ya da editör yazar; uydurulmaz)
- Sırt yazısının yönü: [TEYİT] · Sırtta sıra: yazar/editör · kitap adı · logo
- Taşma payı: 3 mm · Renk: CMYK · ISBN barkodu arka kapakta (yayınevinden)
- Kapak tasarımı ve mizanpaj künyede ayrı satır: "Kapak Tasarımı ve Mizanpaj: Ad SOYAD"

## Tashih
- Yayınevi kuralı: kitap dizgiye girdikten sonra imla (yazım) düzeltmesi yapılmaz; yazar metni dizgiden önce
  denetlemelidir. Dizgiden sonra gelen düzeltmede imla maddeleri ayrılır ve editöre sorulur; içerik ve dizgi
  hataları işlenir. [TEYİT: araç düzeltmeyi hızlı işlediği için bu kural gevşetilecek mi]
- İmla (TDK): alan içi kavram yazımına dokunulmaz (ör. "Hıristiyanlık" yazılmışsa öyle kalır); büyük-küçük harf ve
  noktalama yanlışı ya da eksiği mutlaka düzeltilir (Vizetek, 20.11.2026). [TEYİT: dizgiden sonra imla
  düzeltmesi yapılmaz kuralıyla birlikte: imla taraması dizgiden önce yapılıp yazara/editöre mi gider]
- Yazara giden düzeltme biçimi: PDF üzerinde yorum; her yorum tek başına okunur
  ("Değiştir: «eski» → «yeni»", "Ekle: …", "Sil: «…»", "Biçim: …")
- Yorumlarda görünecek ad: Vizetek Yayıncılık

## DOI ve Crossref (doi skill'i)
- Crossref üyeliği: Vizetek Publishing Company, üye no 33161, önek `10.54637`.
- Kitap DOI'si: `10.54637/vizetek.<ISBN, tiresiz>` (ör. 10.54637/vizetek.9786253825409).
- Bölüm DOI'si (editörlü kitap; Kasım 2026'da başladı): `<kitap DOI>.ch1`, `.ch2` … → `--bolum-eki .ch{no}`.
- Bölüm DOI'sinin adresi: bölümün sitede kendi sayfası yok; şimdilik kitabın vizetek.com.tr sayfası. Bölüm sayfaları
  açılınca adresler doldurulup kitap yeniden yüklenir.
- Kayıt yolu: XML yüklemesi; önce test.crossref.org, sonuç temizse doi.crossref.org. Yüklemeyi hesabı olan kişi yapar.
- Crossref'te yayınevi adı: Vizetek Yayıncılık · yayın yeri: Ankara · dil: tr
- Crossref bildirim e-postası (yükleme sonucu buraya gelir): [TEYİT]
- Bölüm DOI'si bölümün ilk sayfasına basılıyor mu, basılıyorsa nereye: [TEYİT]

## Atıf dizini (atif skill'i)
- Dizin yayınevinin kendisinindir: `Dizgi/atif-dizini/` klasöründe `dizin.json` (tek kaynak), `atif-dizini.xlsx`
  (kaynaklar, bölümler, kitaplar) ve `pdf/` (her bölüm için künye + bölümün ilk sayfası + bölümün kaynakçası).
- Dizine giren kitap PDF'i: yayımlanmış son PDF (e-kitap). Taslak PDF girmez.
- Dönem: kitabın künyesindeki "Baskı: Ankara | Ay Yıl" satırı. Dizin hangi aralıklarla güncellenir: [TEYİT]
- Bölüm PDF'inin ve Excel'in yükleneceği yer (site, paylaşılan klasör): [TEYİT]

## Künye (Vizetek düzeni, sırayla)
ISBN · E-ISBN · DOI · telif notu · Yayın Tasarımcısı / Koordinatörü · Kapak Tasarımı ve Mizanpaj · Baskı
(Şehir | Ay Yıl) · e-kitapta: Materyal Türü: Elektronik Kitap (Çevrim içi / Web tabanlı), Elektronik Yayın
Formatı: PDF, Elektronik Yayın Tipi: Adobe Ebook Reader · logo · adres, telefon, web, e-posta · Yayıncı
Sertifika No: 41575

## Notlar
-
