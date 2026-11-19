---
name: kapak
description: Kitap kapağı önerisi ve baskıya hazır tam kapak (ön + sırt + arka). Kitabın içinden çıkan, birbirinden farklı dört kapak yönü eskizler; seçilen yönü sırt kalınlığı, taşma payı ve CMYK renkle tam kapağa çevirir. Kapak hiçbir zaman yapay zekâ ya da hazır şablon ürünü gibi görünmez. Kullanıcı "kapak", "kapak önerisi", "kapak tasarımı", "sırt", "arka kapak", "arka kapak yazısı" dediğinde kullan.
---

# Kapak

Önce çalışma klasöründeki `yayinevi.md`'yi oku (sırt yönü, logo, barkod, yazı tipleri). Şablon:
`sablon/kapak.typ` (`kapak-olcu`, `tam-kapak`, `on-kapak-eskiz`). Kitap klasöründe `kapak/` altında çalış:
`kapak/eskiz/`, `kapak/yazi-tipleri/`, `kapak/tam-kapak.typ`, `kapak/KAPAK_BILGILERI.md`.

## Kesin kurallar: yapay zekâ ya da şablon ürünü gibi görünmesin

- Yapay zekâ ile üretilmiş görsel, stok fotoğraf, hazır ikon ya da süs kullanma. Görseller Typst'in kendi
  çizimleriyle (çizgi, daire, dikdörtgen, eğri, yazı) elle kurulur; fotoğraf yalnız yazar ya da yayınevi verirse.
- Klişe yok. Genel: ampul, beyin, yapboz, merdiven çıkan silüet, kapı aralığından ışık, yükselen ya da düşen
  eğri, el sıkışma, dünya, kum saati, sisli orman, yalnız ağaç, sırtı dönük kadın, parşömen, eski harita, devre
  kartı, parlayan ağ. Biçim: parlak geçişli renk, ışıma, cam ya da 3B etkisi, gölgeli yazı, her şeyin ortada
  durduğu krem zemin + ince serif düzeni.
- Bir fikir, tek vurgu: en çok iki yazı ailesi, en çok üç mürekkep. Renkler `cmyk(...)` ile tanımlanır.
- Windows'un gömülü yazı tiplerini (Arial, Calibri, Times New Roman, Segoe) kapakta kullanma. Yayınevinin
  lisanslı yazı tipini sor; yoksa Türkçe harfleri tam olan OFL lisanslı bir Google Fonts ailesini
  `kapak/yazi-tipleri/` klasörüne indir ve `typst compile --font-path kapak/yazi-tipleri` ile kullan.
- Başlığı anlam birimlerinden böl, genişlikten değil. Büyük harfi elle yaz (Typst `upper()` İ/I'yı bozar).
- Arka kapak metni ve alıntılar kitaptan ya da yazardan gelir, harfi harfine doğrulanır. Övgü ya da alıntı
  uydurma. Ad, unvan, takdim ve katkı ifadeleri ile sıraları yazarın kararıdır.

## Öneri: dört yön

1. **Kitabı oku**: başlık, alt başlık, içindekiler, önsöz, birkaç ana bölümün girişi. Kitaba özgü malzemeyi
   topla: tekrar eden bir nesne, yer, sayı, tablo, vaka, yazarın kendi benzetmesi. Kapak fikri buradan çıkar.
2. **Dört ayrı aileden birer yön** kur ve her biri için tek cümle yaz (fikir · neden bu kitap · hangi
   klişeye kaymamalı):
   - A. **Kitabın içinden**: bir nesne, tablo ya da sayı diziden çizilmiş işaret.
   - B. **Dönüşüm**: kitabın okura yaptığı değişikliğin soyut, klişesiz bir işareti.
   - C. **Yalnız yazı**: başlığın dizilişi fikrin kendisi olur.
   - D. **Dizi ve yayınevi kimliği**: yayınevinin rafında duracak sakin, klasik yön.
3. **Eskizle**: her yön `on-kapak-eskiz` ile ayrı sayfa; `typst compile kapak/eskiz.typ "kapak/eskiz/k{p}.png" --ppi 110`
   ve küçük boy sınaması için `--ppi 30` (yaklaşık 160 piksel; internet kitapçısı). Görüntülere kendin bak.
4. **Acımasızca ele**: Küçük boyda başlık okunuyor mu? Bu kapak başka bir kitabın da olabilir mi? Türün en çok
   satan on kapağından biri gibi mi duruyor? Klişe listesine düşüyor mu? Zayıf yönü yenisiyle değiştir.
5. **Sun**: dört eskizi yan yana göster, her birine tek cümle gerekçe, birini öner; kullanıcı seçsin.

## Tam kapak

- Sırt: `kapak-olcu(sayfa-sayisi: …, yaprak-kalinligi: …)` → sırt = sayfa ÷ 2 × yaprak kalınlığı. Yaprak
  kalınlığını matbaadan iste; matbaa sırtı mm olarak verdiyse `sirt:` ile o değeri yaz. Son sayfa sayısını
  dizgiden al.
- Taşma payı 3 mm (yayinevi.md farklı derse o). Zemin ve kenara taşan çizimler taşma alanına kadar uzanır;
  yazılar güvenli alanda kalır (kesimden en az 5 mm içeride, sırta 5 mm'den yakın değil).
- Sırt: yön `yayinevi.md`'den; sıra genelde yazar · başlık · logo. 8 mm'den ince sırta yalnız başlık yazılır.
- Arka kapak: tanıtım metni, varsa takdim alıntıları, ISBN barkodu ve logo için yer. Barkod ve logo
  yayınevinden gelir; gelene kadar kutuyla yerini ayır ve `[DOLDUR]` yaz. Tanıtım metnini editör ya da yazar
  verir (Vizetek: 100–150 sözcük, editörden); sözcük sayısını say ve sınırı aşıyorsa söyle; metni kendin
  yazman istenirse taslak olarak işaretle, kitaptaki ifadelere dayan.
- Editörlü kitapta ön kapakta "Editör: Unvan Ad SOYAD" yazar; bölüm yazarları kapağa yazılmaz.
- Provada `kilavuz: true`, baskı dosyasında `false`. Derle, sonra kutuları yaz:
  `py araclar/kapak_kutulari.py kapak/tam-kapak.pdf --genislik 135 --yukseklik 210 --sirt <mm> --tasma 3`
  (ölçü tutmazsa araç durur).

## Teslim

`kapak/` içinde: tam kapak PDF (gerçek yazı, gömülü yazı tipleri, kutular yazılmış), ön kapak ve tam kapak
PNG önizlemesi, Typst kaynağı, `KAPAK_BILGILERI.md` (açılım ölçüsü, sırt, taşma, renkler CMYK ve HEX, yazı
tipleri ve lisansları, bütün metinler). Matbaa yazıların eğriye çevrilmesini isterse bunu Typst yapamaz;
yayınevinin grafikerine ya da matbaaya bırak ve not düş. Kapak tasarımcısının adı künyede başkaysa onun
düzenleyebileceği biçimde teslim et.
