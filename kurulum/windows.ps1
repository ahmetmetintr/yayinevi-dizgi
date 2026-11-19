# Yayınevi Dizgi — Windows kurulumu (tek satır)
#
# PowerShell'de çalıştırın:
#   irm https://raw.githubusercontent.com/ahmetmetintr/yayinevi-dizgi/main/kurulum/windows.ps1 | iex
# Yayınevi kuralları Vizetek profiliyle gelir. Başka yayınevi için önce: $DizgiProfil = 'genel'
#
# Kurar: Claude Code, Git, Typst, Pandoc, Python 3 ve Python paketleri (pypdf, pymupdf, python-docx);
# belge eklentisi (document-skills) ve dizgi eklentisi (dizgi, tashih, kapak); Belgeler\Dizgi çalışma klasörü
# (CLAUDE.md ve yayinevi.md ile). Yüklü olanı yeniden kurmaz, var olan dosyanın üzerine yazmaz; iki kez
# çalıştırmak zararsızdır. winget paketlerini, paket ve kaynak sözleşmelerini kabul ederek kurar.

$DizgiDepo = 'https://raw.githubusercontent.com/ahmetmetintr/yayinevi-dizgi/main'
if (-not (Get-Variable -Name DizgiProfil -ValueOnly -ErrorAction SilentlyContinue)) { $DizgiProfil = 'vizetek' }
$DizgiSonuc = New-Object System.Collections.Generic.List[object]

function DizgiBaslik($metin) { Write-Host "`n== $metin" -ForegroundColor Cyan }
function DizgiKayit($ad, $durum) { $DizgiSonuc.Add([pscustomobject]@{ Adim = $ad; Durum = $durum }) }
function DizgiKomutVar($ad) { [bool](Get-Command $ad -ErrorAction SilentlyContinue) }
function DizgiYoluYenile {
  $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
    [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + (Join-Path $HOME '.local\bin')
}

function DizgiWinget($kimlik, $komut, $ad) {
  if (DizgiKomutVar $komut) { DizgiKayit $ad 'zaten vardı'; return }
  DizgiBaslik "$ad kuruluyor"
  winget install --id $kimlik -e --silent --accept-package-agreements --accept-source-agreements
  DizgiYoluYenile
  if (DizgiKomutVar $komut) { DizgiKayit $ad 'kuruldu' } else { DizgiKayit $ad 'KURULAMADI' }
}

function DizgiIndir($kaynak, $hedef, $ad) {
  if (Test-Path $hedef) { DizgiKayit $ad 'zaten vardı (dokunulmadı)'; return }
  try {
    Invoke-WebRequest -UseBasicParsing -Uri $kaynak -OutFile $hedef -ErrorAction Stop
    DizgiKayit $ad 'yazıldı'
  } catch { DizgiKayit $ad "İNDİRİLEMEDİ: $($_.Exception.Message)" }
}

function DizgiKur {
  DizgiYoluYenile
  if (-not (DizgiKomutVar 'winget')) {
    Write-Host "winget bulunamadı. Microsoft Store'dan 'Uygulama Yükleyicisi'ni (App Installer) kurup güncelleyin, sonra yeniden çalıştırın." -ForegroundColor Red
    return
  }

  # 1. Claude Code (resmî kurucu ayrı bir PowerShell'de çalışır; kendini güncel tutar)
  if (DizgiKomutVar 'claude') { DizgiKayit 'Claude Code' 'zaten vardı' }
  else {
    DizgiBaslik 'Claude Code kuruluyor'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -Command 'irm https://claude.ai/install.ps1 | iex'
    DizgiYoluYenile
    if (DizgiKomutVar 'claude') { DizgiKayit 'Claude Code' 'kuruldu' } else { DizgiKayit 'Claude Code' 'KURULAMADI' }
  }

  # 2. Araçlar
  DizgiWinget 'Git.Git' 'git' 'Git'
  DizgiWinget 'Typst.Typst' 'typst' 'Typst'
  DizgiWinget 'JohnMacFarlane.Pandoc' 'pandoc' 'Pandoc'
  DizgiWinget 'Python.Python.3.13' 'py' 'Python 3'

  # 3. Python paketleri
  if (DizgiKomutVar 'py') {
    DizgiBaslik 'Python paketleri kuruluyor'
    & py -m pip install --user --quiet --disable-pip-version-check pypdf pymupdf python-docx
    if ($LASTEXITCODE -eq 0) { DizgiKayit 'Python paketleri' 'kuruldu' } else { DizgiKayit 'Python paketleri' 'KURULAMADI' }
  } else { DizgiKayit 'Python paketleri' 'atlandı (Python yok)' }

  # 4. Eklentiler
  if (DizgiKomutVar 'claude') {
    DizgiBaslik 'Eklentiler kuruluyor'
    & claude plugin marketplace add anthropics/skills
    & claude plugin install document-skills@anthropic-agent-skills
    & claude plugin marketplace add ahmetmetintr/yayinevi-dizgi
    & claude plugin install dizgi@yayinevi-dizgi
    $liste = (& claude plugin list) -join "`n"
    foreach ($e in @('document-skills@anthropic-agent-skills', 'dizgi@yayinevi-dizgi')) {
      if ($liste -match [regex]::Escape($e)) { DizgiKayit "Eklenti $e" 'kurulu' } else { DizgiKayit "Eklenti $e" 'KURULAMADI' }
    }
  } else { DizgiKayit 'Eklentiler' 'atlandı (Claude Code yok)' }

  # 5. Dizgi çalışma klasörü (Belgeler OneDrive'daysa orası)
  $dizgi = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'Dizgi'
  New-Item -ItemType Directory -Force -Path $dizgi | Out-Null
  DizgiIndir "$DizgiDepo/kurulum/dizgi-klasoru-CLAUDE.md" (Join-Path $dizgi 'CLAUDE.md') 'Dizgi\CLAUDE.md'
  $kural = if ($DizgiProfil -eq 'genel') { 'yayinevi.md' } else { "yayinevi-$DizgiProfil.md" }
  DizgiIndir "$DizgiDepo/eklenti/skills/dizgi/sablon/$kural" (Join-Path $dizgi 'yayinevi.md') "Dizgi\yayinevi.md ($DizgiProfil)"

  Write-Host "`n== Sonuç" -ForegroundColor Cyan
  $DizgiSonuc | Format-Table -AutoSize | Out-String | Write-Host
  if ($DizgiSonuc | Where-Object { $_.Durum -match 'KURULAMADI|İNDİRİLEMEDİ' }) {
    Write-Host 'Bazı adımlar tamamlanmadı. PowerShell''i kapatıp açın ve bu satırı yeniden çalıştırın; sorun sürerse eğitim sayfasındaki elle kurulumu kullanın.' -ForegroundColor Yellow
  }
  Write-Host "Çalışma klasörü: $dizgi"
  Write-Host 'Sonraki adım: bu pencereyi kapatın, yeni bir PowerShell açın ve şunu yazın:' -ForegroundColor Green
  Write-Host "  cd `"$dizgi`"; claude" -ForegroundColor Green
  Write-Host 'İlk açılışta tarayıcıda Claude hesabınızla giriş yapın.'
}

DizgiKur
