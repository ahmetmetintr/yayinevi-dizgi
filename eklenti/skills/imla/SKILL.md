---
name: imla
description: Türkçe imla (yazım) denetimi. Dizilecek ya da dizilmiş kitabın bütün metnini TDK Yazım Kılavuzu kurallarına göre tarar (bitişik/ayrı yazım, de/da/ki/mi, kesme işareti, kısaltma ve rakamdan sonra ek, yinelenen sözcük, terim yazımı, kitap içinde aynı terimin iki yazımı, tek geçen yazım hataları); hiçbir şeyi düzeltmez, editöre rapor ve düzeltilecek yerleri SARI işaretli prova PDF'i hazırlar. Kullanıcı "imla", "yazım", "yazım hatası", "imla kontrolü", "TDK", "sarı işaretle", "yazım yanlışları" dediğinde ya da dizgiden önce metin denetlenecekse kullan.
---

# İmla

Yayınevi dizgiden sonra imla düzeltmesi yapmaz (Vizetek); imla kararları **dizgiden önce editöre** gider. Bu beceri
bulur, sınıflar ve gösterir; **metni kendisi değiştirmez**. Onaylanan düzeltmeler `tashih` becerisiyle işlenir.

Önce çalışma klasöründeki `yayinevi.md`'yi oku (imla kılavuzu, istisnalar). Araç: `araclar/imla_denetle.py`;
kurallar veri olarak `kurallar/sik-yanlislar.tsv` (yanlış · doğru · kural) dosyasındadır, kodda değil.

## Kurallar (TDK Yazım Kılavuzu, özet)

- **Bitişik / ayrı:** birçok, birkaç, hiçbir, birtakım (bitişik) · bir şey, her şey, hiç kimse, her zaman, her gün,
  herhangi bir, pek çok, şu an, ya da, yanı sıra (ayrı).
- **Bağlaçlar:** "de/da" bağlacı ve "ki" bağlacı ayrı yazılır (şöyle ki, Türkiye'de de). "mi" soru eki ayrı yazılır
  (geldi mi?). "ve/veya/ile" sonraki sözcüğe yapışmaz ("ve McMahon").
- **Kesme işareti:** özel ada, kısaltmaya, rakama ve yüzde sayısına gelen ek kesmeyle ayrılır: 1990'lı, Tip 2'de,
  %20'si, MR'de, ABD'de. Ek kısaltmanın okunuşuna uyar (MR'de "emar", TDK'ye).
- **Büyük harf:** TÜMÜ BÜYÜK yazımda i → İ (HİRSCHSPRUNG); hastalık adları küçük harfle (diyabet), kişi adından
  gelen terimde ad büyük (Hirschsprung hastalığı).
- **Terim yazımı:** Türkçe tıp yazımında TDK biçimi (bağırsak, diyafram, nöroblastom, kateter, laparoskopi);
  Latince kalıplar olduğu gibi (diabetes mellitus). Bir kitapta aynı terim tek biçimde yazılır.
- **Alan içi kavram yazımı korunur** (Vizetek, 20.11.2026): alanında yerleşik yazım TDK'ninkinden farklıysa öneri
  yapılmaz (yazar "Hıristiyanlık" yazdıysa "Hristiyanlık" yapılmaz); böyle bir kavram `imla-istisnalar.txt`'ye yazılır.
  Büyük-küçük harf ve noktalama yanlışı ya da eksiği ise mutlaka düzeltilecekler listesine girer.
- **Rakamlar ve birimler:** tipografi işidir (`dizgi` → `tipografi.py`): "12–18", "5 mg" bölünmez boşluk.

## İş akışı

1. **Tara.** Kitap klasöründe:
   `py imla_denetle.py metin/*.typ --rapor cikti/imla-raporu.md --isaret metin/imla-isaretleri.typ --istisna imla-istisnalar.txt`
   Kaynakçalar taranmaz (özel adlar; `kaynakca_denetle.py` ayrı bakar). Yeni kitapta `imla-istisnalar.txt` boş açılır.
2. **Oku ve ayıkla.** Raporu kendin gözden geçir; bağlamı `metin/` dosyasında (satır numarasıyla) aç.
   - `kesin`: listedeki yanlış, kesmesiz ek, yinelenen bağlaç, yapışık bağlaç.
   - `olası`: bitişik soru eki; kitapta bir iki kez geçip sık geçen bir sözcükten tek harfle ayrılan sözcük
     ("anomamliler" ↔ "anomaliler", "streoid" ↔ "steroid"); aynı terimin iki yazımı ("adolesan" ↔ "adölesan").
     Öneri kitapta **daha sık geçen** biçimdir, TDK biçimi olmayabilir: terimde TDK ya da Türkçe tıp kılavuzu esas.
   - Editörün "doğru" dediği sözcükleri `imla-istisnalar.txt`'ye yaz (satır başına bir sözcük), yeniden tara.
3. **Sarı prova.** Kitabın ana dosyasında (bir kez):
   `#import "metin/imla-isaretleri.typ": imla-deseni` ve şablon ayarlarına
   `sari-desen: if sys.inputs.at("imla", default: "hayir") == "evet" { imla-deseni } else { none },`
   Sonra `typst compile --input imla=evet kitap.typ cikti/imla-prova.pdf`. Bulunan bütün yerler **sarı** zeminle
   işaretlenir; düzen baskı PDF'iyle aynıdır (sayfa numaraları tutar). Baskı derlemesinde işaret yoktur.
4. **Editöre gönder.** `imla-raporu.md` (bölüm bölüm tablo: satır, yazılan, öneri, kural, güven) + `imla-prova.pdf`.
   Raporun başına kısa özet yaz: kaç kesin, kaç olası, en sık kural, terim tutarlılığı kararları.
5. **Onaylananı işle.** Editörün onayladığı düzeltmeleri `tashih` becerisiyle bir tur olarak uygula; bu beceri
   metne yazmaz. Kitaba özgü yeni bir sık yanlış öğrenilirse `kurallar/sik-yanlislar.tsv`'ye değil kitabın
   `NOTLAR.md`'sine yaz; genel bir yanlışsa eklentiye öneri olarak bildir.

## Sınırlar

- Araç sözlük kullanmaz: listede olmayan ve kitapta tek tek geçmeyen yanlışları kaçırabilir; araya fazladan giren
  ünsüzü ("anomamliler", "beselenme") Türkçe çekimlerle karışmasın diye aramaz; "de/da" bağlacının bitişik
  yazıldığı yerleri (ör. "bende") anlam gerektirdiği için bulmaz. Raporla birlikte örnek sayfaları gözle de oku.
- 64 harften uzun harf dizileri (yapıştırılmış DNA dizisi, bozuk metin) sözcük sayılmaz, benzerlik denetimine girmez;
  o denetim sözcük uzunluğunun karesiyle büyüdüğü için böyle bir dizi taramayı dakikalarca kilitlerdi.
- Düzeltme önerisini metne kendin uygulama; kullanıcı açıkça "uygula" dese bile önce editör onayını sor
  (yayınevi kuralı). Yazarın üslubuna ve alan içi terim seçimine karışma; büyük-küçük harf ve noktalama yanlışını
  ya da eksiğini (Vizetek: mutlaka düzeltilir) raporda göster, editör onayıyla `tashih` turunda işle.
