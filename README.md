# Yayınevi Dizgi — Claude Code eklentisi

Türkçe kitap yayıncılığı için Claude Code eklentisi. Beş beceri getirir:

- **dizgi** — Word dosyasından Typst ile baskıya hazır PDF: kitap şablonu (iç kapak, künye, içindekiler,
  sağ sayfada açılan bölümler), Türkçe tipografi düzeltmesi (harf dizisi doğrulamalı), baskı öncesi PDF kontrolü.
- **tashih** — yazardan ya da hocalardan gelen düzeltmeleri okur (işaretli PDF, izli ya da yorumlu Word,
  liste), yalnız tek ve kesin yere oturanı uygular, yazara işaretli PDF ve rapor hazırlar; eski sürüm
  tuzağını her turda denetler.
- **kapak** — kitabın içinden çıkan dört kapak yönü ve sırt, taşma payı, CMYK ile baskıya hazır tam kapak.
- **doi** — kitap ve bölüm DOI'lerinin Crossref kaydı: künye, bölüm, yazar, kurum, ORCID ve sayfa bilgisinden
  denetlenmiş Crossref XML'i ve onay tablosu; önce test, sonra asıl sisteme yükleme; kayıttan sonra doğrulama.
  Araçlar Crossref'e kendileri yüklemez ve şifre kullanmaz.
- **atif** — yayınevinin atıf dizini: yayımlanmış kitapların PDF'lerinden kaynakçadaki kaynakları tek tek
  çıkarır. Her bölüm için kitap künyesi, bölümün ilk sayfası ve bölümün kaynakçası tek PDF'te toplanır. Bütün
  kitapların kaynakları tek Excel dosyasına yazılır (`atif-dizini.xlsx`: kaynaklar, bölümler, kitaplar). Dönem
  süzgeci vardır (ör. yılın ilk üç ayı).

Hazır yayınevi profili: **Vizetek Yayıncılık** (2026 yazım kılavuzu ve dizgisi: 16×24, Times New Roman 11 pt /
1,15, editörlü ve telif kitap düzeni, APA 7 + DOI zorunlu kaynakça, 10–25 sayfalık bölüm, e-kitap).

## Kurulum (Windows, PowerShell)

Tek satır: Claude Code, Git, Typst, Pandoc, Python, eklentiler ve Belgeler\Dizgi çalışma klasörü.

```powershell
irm https://raw.githubusercontent.com/ahmetmetintr/yayinevi-dizgi/main/kurulum/windows.ps1 | iex
```

Yalnız eklenti (araçlar kuruluysa):

```powershell
claude plugin marketplace add ahmetmetintr/yayinevi-dizgi
claude plugin install dizgi@yayinevi-dizgi
```

Gerekenler: Typst 0.13+, Pandoc, Python 3 ve `py -m pip install --user pypdf pymupdf python-docx`. Lisans: MIT.
Adım adım eğitim ve kopyala-yapıştır promptlar: `egitim/` (sayfa `python3 egitim/uret.py` ile üretilir).

## Geliştirme

```bash
scripts/denetle.sh
```

Harita ve kurallar: `docs/MIMARI.md`. Her değişiklikte `eklenti/.claude-plugin/plugin.json` sürümünü artırın.
