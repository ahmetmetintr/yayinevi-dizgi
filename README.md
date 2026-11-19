# Yayınevi Dizgi — Claude Code eklentisi

Türkçe kitap yayıncılığı için Claude Code eklentisi. Üç beceri getirir:

- **dizgi** — Word dosyasından Typst ile baskıya hazır PDF: kitap şablonu (iç kapak, künye, içindekiler,
  sağ sayfada açılan bölümler), Türkçe tipografi düzeltmesi (harf dizisi doğrulamalı), baskı öncesi PDF kontrolü.
- **tashih** — yazardan ya da hocalardan gelen düzeltmeleri okur (işaretli PDF, izli ya da yorumlu Word,
  liste), yalnız tek ve kesin yere oturanı uygular, yazara işaretli PDF ve rapor hazırlar; eski sürüm
  tuzağını her turda denetler.
- **kapak** — kitabın içinden çıkan dört kapak yönü ve sırt, taşma payı, CMYK ile baskıya hazır tam kapak.

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
