Bu Windows bilgisayarı kitap dizgisi için hazırla. Teknik biri değilim; her adımda ne yaptığını tek cümleyle söyle.

1. Şu araçlar yüklü mü bak; yoksa winget ile resmî paketlerinden kur:
   - Git for Windows: `winget install --id Git.Git -e`
   - Typst (dizgi motoru): `winget install --id Typst.Typst -e`
   - Pandoc (Word dosyasını dönüştürür): `winget install --id JohnMacFarlane.Pandoc -e`
   - Python 3: `winget install --id Python.Python.3.13 -e`
2. Python paketlerini kur: `py -m pip install --user pypdf pymupdf python-docx`
3. Sürümleri doğrula: `typst --version`, `pandoc --version`, `py --version`. Yeni kurulan bir komut bulunamazsa söyle; Claude Code'u kapatıp açmam gerekir.
4. Belgeler klasörümde "Dizgi" adında bir çalışma klasörü aç (varsa dokunma) ve tam yolunu söyle. Belgeler OneDrive'a bağlıysa oradaki Belgeler'i kullan.
5. Dizgi klasörüne iki dosya koy (varsa dokunma):
   - `yayinevi.md`: dizgi skill'indeki `sablon/yayinevi.md` dosyasının kopyası.
   - `CLAUDE.md`, şu metinle:
     # Dizgi çalışma klasörü
     Bu klasörde yayınevimizin kitapları dizilir. Dizgi, tashih ve kapak işlerinde ilgili skill'i kullan.
     - Yayınevi kuralları: yayinevi.md (her işten önce oku).
     - Her kitap ayrı klasördedir; yazarın dosyaları kaynak/ içinde değişmeden kalır.
     - Yazarın sözcüklerine dokunma; yazım önerilerini kitabın NOTLAR.md dosyasına yaz.
     - Bu bilgisayar Windows; Python'u `py` ile çağır.
6. Sonunda bir tablo ver: araç · sürüm · durum (✓ / ✗). Kurulamayan bir şey varsa nedenini ve benim ne yapmam gerektiğini yaz.

Windows yönetici izni penceresi açılırsa bana söyle; onayı ben vereceğim.
