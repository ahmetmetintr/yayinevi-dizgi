# Yayınevi dizgi kuralları

> Bu dosya Dizgi çalışma klasöründe durur. Dizgi, tashih ve kapak skill'leri onu her işte okur; buradaki değer
> skill'lerin varsayılanını geçersiz kılar. "Yayınevimizin kurallarını öğren" promptuyla doldurulur.
> Durum: VARSAYILAN (henüz yayınevine göre doldurulmadı)

## Yayınevi
- Ad: [DOLDUR]
- Yayıncı sertifika no: [DOLDUR]
- Adres ve iletişim (künye için): [DOLDUR]
- Çalışılan matbaa, adresi ve matbaa sertifika no: [DOLDUR]
- Telif notu: [DOLDUR]

## Typst profili
- Profil: klasik (13,5 × 21 genel kitap). Hazır yayınevi profilleri `sablon/profiller.typ` içinde.
- Kitap türü: telif / editörlü (editörlü kitapta bölüm başına `#bolum(...)` ve `#kaynakca[...]`)

## Kitap ölçüleri (Typst parametresi: milimetre)
| Tür | Kesim (genislik × yukseklik) | ic-bosluk | dis-bosluk | ust-bosluk | alt-bosluk |
| --- | --- | --- | --- | --- | --- |
| Roman ve genel | 135 × 210 | 20 | 15 | 20 | 22 |
| Akademik | 160 × 240 | 22 | 18 | 22 | 25 |

## Yazı
- Gövde yazı tipi (yazi-tipi): Libertinus Serif (Typst ile gelir, ücretsiz, Türkçe harfleri tam)
- Punto (punto): 10,5 pt · satır aralığı (satir-araligi): 0,65em · paragraf girintisi (girinti): 1,2em
- Başlık yazı tipi: gövdeyle aynı

## Noktalama
- Ara söz çizgisi: en ( – )   → tipografi.py --ara-cizgi en
- Konuşma çizgisi: uzun (—)   → tipografi.py --konusma-cizgisi em
- Tırnak: “ ” (iç tırnak ‘ ’)

## Sayfa düzeni
- Bölüm başı: sağ sayfa
- Sayfa numarası: alt orta; ön sayfalarda basılmaz
- Üst bilgi: sol sayfada kitap adı, sağ sayfada bölüm adı, italik
- Forma: 16 sayfa · Baskı: tek renk (siyah)
- Ön sayfalar: 1 yarım başlık · 2 boş · 3 iç kapak · 4 künye · (5 ithaf) · içindekiler

## Kapak
- Sırt yazısının yönü: yukarıdan aşağı (kitap yatırıldığında ön kapak üstte okunur)
- Sırtta sıra: yazar · kitap adı · yayınevi logosu
- Arka kapak: tanıtım metni, varsa takdim alıntıları, ISBN barkodu sağ altta (barkod yayınevinden)
- Taşma payı: 3 mm · Renk: CMYK
- Kapak yazı tipleri: [DOLDUR: lisansı olan ya da ücretsiz (OFL) yazı tipleri]

## Tashih
- Yazara giden düzeltme biçimi: PDF üzerinde yorum; her yorum tek başına okunur
  ("Değiştir: «eski» → «yeni»", "Ekle: …", "Sil: «…»", "Biçim: …")
- Yazar ya da hoca düzeltmesi tek ve kesin eşleşmezse uygulanmaz, sorulur

## DOI ve Crossref (doi skill'i)
- Crossref öneki: [DOLDUR: ör. 10.12345]
- Kitap DOI'si biçimi: [DOLDUR: ör. <önek>/<yayınevi>.<ISBN, tiresiz>]
- Bölüm DOI'si biçimi: [DOLDUR: ör. <kitap DOI>.ch1 ya da bölüm DOI'si yok]
- Bölüm DOI'sinin adresi: [DOLDUR: bölümün kendi sayfası ya da kitabın sayfası]
- Crossref'te yayınevi adı ve yayın yeri: [DOLDUR]
- Crossref bildirim e-postası (yükleme sonucu buraya gelir): [DOLDUR]

## Atıf dizini (atif skill'i)
- Dizine giren kitap PDF'i: [DOLDUR: yayımlanmış son PDF, e-kitap]
- Bölüm PDF'inin ve Excel'in yükleneceği yer: [DOLDUR]

## Notlar
-
