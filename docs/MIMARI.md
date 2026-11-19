# Mimari

Yayınevi dizgi kiti: Claude Code'a kurulan **dizgi eklentisi** (beş beceri: dizgi, tashih, kapak, doi, atif) ve onu
kopyala-yapıştır promptlarla anlatan **eğitim sayfası**. Depo aynı zamanda eklentinin pazar yeridir
(`.claude-plugin/marketplace.json`); kurulumda yalnız `eklenti/` klasörü kopyalanır.

## Harita

| Klasör | İçinde ne durur | Neye bağlanabilir |
| --- | --- | --- |
| `.claude-plugin/` | Pazar yeri tanımı: `yayinevi-dizgi` pazarı, `dizgi` eklentisi | `eklenti/` |
| `eklenti/.claude-plugin/` | Eklenti tanımı ve **sürüm** (`plugin.json`) | — |
| `eklenti/skills/dizgi/sablon/` | `kitap.typ` (ana şablon) → `on-sayfalar.typ`, `ogeler.typ` (bolum, kisim, kaynakca, kutu, tr-buyuk…); `profiller.typ` (klasik, vizetek-telif, vizetek-editorlu); `ana-dosya.typ`; kural dosyaları `yayinevi.md` (genel), `yayinevi-vizetek.md` | Yalnız kendi içinde |
| `eklenti/skills/dizgi/araclar/` | `tipografi.py`, `pdf_kontrol.py`, `kaynakca_denetle.py` (APA, DOI, atıf, Crossref), `bolum_denetle.py` (bölüm uzunluğu, ORCID), `e_kitap.py` (kapak + yer imi + PDF bilgisi) | Hiçbir şeye |
| `eklenti/skills/tashih/` | Düzeltme turları: `araclar/` (tashih_oku.py, tashih_uygula.py, tashih_rapor.py) | Hiçbir şeye |
| `eklenti/skills/kapak/` | Kapak: `sablon/kapak.typ` (ölçü), `araclar/kapak_kutulari.py` | Hiçbir şeye |
| `eklenti/skills/doi/` | Crossref DOI kaydı: `araclar/` (doi_hazirla.py, doi_xml.py, doi_sorgula.py, doi_ortak.py), `sablon/kayit-ornegi.json` | Kendi `doi_ortak.py`'sine; ağda yalnız api.crossref.org (okuma) |
| `eklenti/skills/atif/` | Atıf dizini: `araclar/` (atif_hazirla.py: PDF → dizin.json; atif_uret.py: denetim, bölüm PDF'leri, Excel; saf modüller atif_kaynakca.py, atif_yapi.py, atif_xlsx.py; atif_ortak.py), `sablon/dizin-ornegi.json` | Kendi `atif_ortak.py`'sine; ağa çıkmaz |
| `kurulum/` | Windows kurulum betiği (`windows.ps1`, `irm … \| iex` ile) ve çalışma klasörüne konan `CLAUDE.md` şablonu | GitHub'daki `main` dalı (ham dosya adresleri) |
| `egitim/` | Eğitim sayfası: `sayfa.html` iskelet, `promptlar/KOD-ad.md`, `uret.py` | `eklenti/.claude-plugin/plugin.json` (sürüm) |
| `testler/` | Birim testleri (tipografi, tashih, kaynakça, doi, atif), örnek kitaplar (klasik, Vizetek editörlü ve telif) ve örnek kapak | `eklenti/` |
| `scripts/denetle.sh` | Tek denetim komutu | hepsi |
| `cikti/` | Üretilen dosyalar (git dışında, elle düzenlenmez) | — |

Beceriler birbirini içe aktarmaz: her biri kendi `araclar/` klasörüyle tek başına çalışır. Ortak bilgi
kullanıcının çalışma klasöründedir: `Dizgi/yayinevi.md` (yayınevi kuralları) ve `Dizgi/CLAUDE.md`. Kurallar
eklentinin içinde tutulmaz; eklenti güncellenince kaybolurdu.

## Veri akışı

1. Word → `dizgi` (pandoc → metin.typ / bolum-NN.typ → tipografi.py → Typst (profil) → PDF → pdf_kontrol.py,
   kaynakca_denetle.py, bolum_denetle.py → e_kitap.py).
2. Hoca düzeltmesi → `tashih` (tashih_oku.py → liste.json → tashih_uygula.py → metin.typ → yeni PDF →
   tashih_rapor.py → işaretli PDF + rapor). Her tur `tashih/tur-NN/` klasöründe; önceki turlar
   `liste.sonuc.json` ile denetlenir.
3. Kitap → `kapak` (dört eskiz → seçilen yön → kapak.typ ile tam kapak → kapak_kutulari.py).
4. Son PDF → `doi` (doi_hazirla.py → `doi/kayit.json` (tek kaynak, elle düzeltilir) → doi_sorgula.py --doldur
   (kitap Crossref'te kayıtlıysa) → doi_xml.py: denetim + onay tablosu + `doi/crossref-<zaman>.xml` → yetkili kişi
   test.crossref.org'a, sonra doi.crossref.org'a yükler → doi_sorgula.py ile doğrulama). Araçlar Crossref'e
   yüklemez ve kimlik bilgisi kullanmaz.
5. Yayımlanmış kitapların PDF'leri → `atif` (atif_hazirla.py: künye, bölümler (yer imleri ya da tahmin), ilk
   sayfa, kaynakça satırları → kaynaklar → `atif-dizini/dizin.json` (bütün kitaplar, tek kaynak, elle düzeltilir) →
   atif_uret.py: denetim → `pdf/<kod>/<kod>-bolum-NN.pdf` (künye + ilk sayfa + kaynakça) ve `atif-dizini.xlsx`).
   Çekirdek modüller (atif_kaynakca.py, atif_yapi.py) PDF açmaz; satırları atif_hazirla.py verir.

## Yeni bir şey eklerken

| Eklenecek | Yeri | Örnek |
| --- | --- | --- |
| Yeni beceri | `eklenti/skills/<ad>/SKILL.md` (+ `araclar/`, `sablon/`) | `skills/kapak` |
| Yeni prompt | `egitim/promptlar/KOD-ad.md` + `sayfa.html`'de `{{KART:KOD|Başlık|Açıklama}}` ve dizin satırı | `D1-kapak-onerileri.md` |
| Tipografi kuralı | `tipografi.py` → `kurallar()` + `testler/test_tipografi.py` | "üç nokta" |
| Düzeltme biçimi | `tashih_oku.py` → `ayristir()` + `testler/test_tashih.py` | "Değiştir: «eski» → «yeni»" |
| Kaynakça biçimi (atıf dizini) | `atif_kaynakca.py` → `kaynaklara_ayir()` / `kaynak_alanlari()` + `testler/test_atif.py` | numaralı kaynakça |
| Atıf dizini sütunu | `atif_uret.py` → `tablo_sayfalari()` (başlık, satır ve genişlik aynı sırada) | "Bölüm DOI" |
| PDF denetimi | `pdf_kontrol.py` → `main()` içinde `yaz(...)` | tire merdiveni |
| Yeni yayınevi | `profiller.typ`'ye profil + `sablon/yayinevi-<ad>.md`; kurulumda `$DizgiProfil = '<ad>'` | `vizetek-editorlu` |
| Metin içi yardımcı | `ogeler.typ` (ayarı `kitap.typ`'den gelir) | `kutu`, `bolum` |
| Her değişiklikte | `eklenti/.claude-plugin/plugin.json` sürümünü artır (yoksa kullanıcıda güncelleme görünmez) | 1.0.0 → 1.0.1 |

## Ortak yardımcılar

| İş | Yer |
| --- | --- |
| Typst metnini yazı ve kod parçalarına ayırma | `tipografi.py` → `Tarayici` |
| Harf dizisi ve yapı doğrulaması | `tipografi.py` → `dogrula` |
| Tipografi ve biçim farkını yok sayan eşleştirme | `tashih_uygula.py` → `normallestir` |
| Kapak ölçüleri (sırt, taşma, panel konumları) | `kapak.typ` → `kapak-olcu` |
| Türkçe büyük harf (i → İ) | `ogeler.typ` → `tr-buyuk` |
| Türkçe alfabe sırası | `kaynakca_denetle.py` → `sira_anahtari` |
| Crossref XML'i (şema 5.3.1) ve kayıt denetimi | `doi_xml.py` → `xml_uret`, `denetle` |
| "Ad SOYAD" yazımını ad ve soyada ayırma, Türkçe baş harf | `doi_ortak.py` → `ad_ayir`, `bas_harf` |
| ORCID ve ISBN sağlama hanesi | `doi_ortak.py` (ORCID'in bir kopyası `bolum_denetle.py`'de: beceriler birbirini içe aktarmaz) |
| PDF satırlarından kaynakçayı tek tek kaynaklara ayırma (asılı girinti, numara, bölünen DOI) | `atif_kaynakca.py` → `kaynaklara_ayir`, `birlestir` |
| Künye alanları (ISBN, E-ISBN, DOI, baskı tarihi), basılı sayfa numarası, yer imlerinden bölüm düzeyi | `atif_yapi.py` → `kunye_alanlari`, `basili_numara`, `bolum_araliklari` |
| Ek paketsiz XLSX yazma | `atif_xlsx.py` → `xlsx_yaz` |
| Türkçe küçük harf ve başlık anahtarı | `atif_ortak.py` → `tr_kucuk`, `anahtar` (`tr_kucuk`'un kopyaları `doi_ortak.py` ve `kaynakca_denetle.py`'de: beceriler birbirini içe aktarmaz) |

## Bekçiler

`scripts/denetle.sh`: birim testleri, eklenti ve pazar yeri doğrulaması (`claude plugin validate`), sayfa
üretimi (her prompt sayfada tam bir kez), dosya boyutu (kaynak ≤ 400, test ≤ 600 satır).
