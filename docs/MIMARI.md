# Mimari

Yayınevi dizgi kiti: Claude Code'a kurulan **dizgi eklentisi** (üç beceri: dizgi, tashih, kapak) ve onu
kopyala-yapıştır promptlarla anlatan **eğitim sayfası**. Depo aynı zamanda eklentinin pazar yeridir
(`.claude-plugin/marketplace.json`); kurulumda yalnız `eklenti/` klasörü kopyalanır.

## Harita

| Klasör | İçinde ne durur | Neye bağlanabilir |
| --- | --- | --- |
| `.claude-plugin/` | Pazar yeri tanımı: `yayinevi-dizgi` pazarı, `dizgi` eklentisi | `eklenti/` |
| `eklenti/.claude-plugin/` | Eklenti tanımı ve **sürüm** (`plugin.json`) | — |
| `eklenti/skills/dizgi/` | Kitap dizgisi: `SKILL.md`, `sablon/` (kitap.typ, ana-dosya.typ, yayinevi.md kural şablonu), `araclar/` (tipografi.py, pdf_kontrol.py) | Hiçbir şeye |
| `eklenti/skills/tashih/` | Düzeltme turları: `araclar/` (tashih_oku.py, tashih_uygula.py, tashih_rapor.py) | Hiçbir şeye |
| `eklenti/skills/kapak/` | Kapak: `sablon/kapak.typ` (ölçü), `araclar/kapak_kutulari.py` | Hiçbir şeye |
| `egitim/` | Eğitim sayfası: `sayfa.html` iskelet, `promptlar/KOD-ad.md`, `uret.py` | `eklenti/.claude-plugin/plugin.json` (sürüm) |
| `testler/` | Birim testleri, örnek kitap ve örnek kapak | `eklenti/` |
| `scripts/denetle.sh` | Tek denetim komutu | hepsi |
| `cikti/` | Üretilen dosyalar (git dışında, elle düzenlenmez) | — |

Beceriler birbirini içe aktarmaz: her biri kendi `araclar/` klasörüyle tek başına çalışır. Ortak bilgi
kullanıcının çalışma klasöründedir: `Dizgi/yayinevi.md` (yayınevi kuralları) ve `Dizgi/CLAUDE.md`. Kurallar
eklentinin içinde tutulmaz; eklenti güncellenince kaybolurdu.

## Veri akışı

1. Word → `dizgi` (pandoc → metin.typ → tipografi.py → Typst → PDF → pdf_kontrol.py).
2. Hoca düzeltmesi → `tashih` (tashih_oku.py → liste.json → tashih_uygula.py → metin.typ → yeni PDF →
   tashih_rapor.py → işaretli PDF + rapor). Her tur `tashih/tur-NN/` klasöründe; önceki turlar
   `liste.sonuc.json` ile denetlenir.
3. Kitap → `kapak` (dört eskiz → seçilen yön → kapak.typ ile tam kapak → kapak_kutulari.py).

## Yeni bir şey eklerken

| Eklenecek | Yeri | Örnek |
| --- | --- | --- |
| Yeni beceri | `eklenti/skills/<ad>/SKILL.md` (+ `araclar/`, `sablon/`) | `skills/kapak` |
| Yeni prompt | `egitim/promptlar/KOD-ad.md` + `sayfa.html`'de `{{KART:KOD|Başlık|Açıklama}}` ve dizin satırı | `D1-kapak-onerileri.md` |
| Tipografi kuralı | `tipografi.py` → `kurallar()` + `testler/test_tipografi.py` | "üç nokta" |
| Düzeltme biçimi | `tashih_oku.py` → `ayristir()` + `testler/test_tashih.py` | "Değiştir: «eski» → «yeni»" |
| PDF denetimi | `pdf_kontrol.py` → `main()` içinde `yaz(...)` | tire merdiveni |
| Her değişiklikte | `eklenti/.claude-plugin/plugin.json` sürümünü artır (yoksa kullanıcıda güncelleme görünmez) | 1.0.0 → 1.0.1 |

## Ortak yardımcılar

| İş | Yer |
| --- | --- |
| Typst metnini yazı ve kod parçalarına ayırma | `tipografi.py` → `Tarayici` |
| Harf dizisi ve yapı doğrulaması | `tipografi.py` → `dogrula` |
| Tipografi ve biçim farkını yok sayan eşleştirme | `tashih_uygula.py` → `normallestir` |
| Kapak ölçüleri (sırt, taşma, panel konumları) | `kapak.typ` → `kapak-olcu` |

## Bekçiler

`scripts/denetle.sh`: birim testleri, eklenti ve pazar yeri doğrulaması (`claude plugin validate`), sayfa
üretimi (her prompt sayfada tam bir kez), dosya boyutu (kaynak ≤ 400, test ≤ 600 satır).
