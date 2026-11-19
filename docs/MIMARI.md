# Mimari

Yayınevi dizgi kiti: Claude Code'a kurulan **dizgi eklentisi** (dört beceri: dizgi, tashih, kapak, imla) ve onu
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
| `eklenti/skills/imla/` | İmla denetimi: `araclar/imla_denetle.py` (rapor + sarı prova deseni), kurallar veri olarak `kurallar/sik-yanlislar.tsv` | Hiçbir şeye (sarı prova `dizgi` şablonunun `sari-desen` ayarıyla) |
| `kurulum/` | Windows kurulum betiği (`windows.ps1`, `irm … \| iex` ile) ve çalışma klasörüne konan `CLAUDE.md` şablonu | GitHub'daki `main` dalı (ham dosya adresleri) |
| `egitim/` | Eğitim sayfası: `sayfa.html` iskelet, `promptlar/KOD-ad.md`, `uret.py` | `eklenti/.claude-plugin/plugin.json` (sürüm) |
| `testler/` | Birim testleri (tipografi, tashih, kaynakça), örnek kitaplar (klasik, Vizetek editörlü ve telif) ve örnek kapak | `eklenti/` |
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
4. metin/*.typ → `imla` (imla_denetle.py → imla-raporu.md + imla-isaretleri.typ → `--input imla=evet` ile sarı prova
   PDF) → editör kararı → onaylananlar `tashih` turu olarak işlenir. İmla aracı metne hiç yazmaz.

## Yeni bir şey eklerken

| Eklenecek | Yeri | Örnek |
| --- | --- | --- |
| Yeni beceri | `eklenti/skills/<ad>/SKILL.md` (+ `araclar/`, `sablon/`) | `skills/kapak` |
| Yeni prompt | `egitim/promptlar/KOD-ad.md` + `sayfa.html`'de `{{KART:KOD|Başlık|Açıklama}}` ve dizin satırı | `D1-kapak-onerileri.md` |
| Tipografi kuralı | `tipografi.py` → `kurallar()` + `testler/test_tipografi.py` | "üç nokta" |
| İmla: sık yanlış | `imla/kurallar/sik-yanlislar.tsv` satırı (yanlış · doğru · kural) | `barsak*` → `bağırsak*` |
| İmla: yeni kural türü | `imla_denetle.py` → `kural_bulgulari()` + `testler/test_imla.py` | kısaltmadan sonra kesmesiz ek |
| Düzeltme biçimi | `tashih_oku.py` → `ayristir()` + `testler/test_tashih.py` | "Değiştir: «eski» → «yeni»" |
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

## Bekçiler

`scripts/denetle.sh`: birim testleri, eklenti ve pazar yeri doğrulaması (`claude plugin validate`), sayfa
üretimi (her prompt sayfada tam bir kez), dosya boyutu (kaynak ≤ 400, test ≤ 600 satır).
