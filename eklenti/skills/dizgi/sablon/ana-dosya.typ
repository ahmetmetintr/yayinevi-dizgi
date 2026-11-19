// Bu kitabın ana dosyası (dizgi skill'i). Derleme:
//   typst compile kitap.typ cikti/kitap.pdf
// Profil yayınevi kurallarından gelir (yayinevi.md → "Typst profili"). [DOLDUR] yazan yerleri doldurun.

#import "sablon/kitap.typ": kitap
#import "sablon/profiller.typ": klasik, vizetek-telif, vizetek-editorlu

#show: kitap.with(
  ..klasik, // [DOLDUR: profil — klasik, vizetek-telif ya da vizetek-editorlu]
  baslik: "[DOLDUR: Kitap adı]",
  alt-baslik: none,
  ucuncu-satir: none,
  yazar: "[DOLDUR: Yazar adı ya da Editör: Unvan Ad SOYAD]",
  yayinevi: "[DOLDUR: Yayınevi adı]",
  logo: none, // ör. "logo.png" (kitap klasöründe)
  kunye: (
    ("ISBN", "[DOLDUR]"),
    ("E-ISBN", "[DOLDUR]"),
    ("DOI", "[DOLDUR]"),
    "---",
    ("", [[DOLDUR: Telif notu]]),
    "---",
    ("Yayın Koordinatörü", "[DOLDUR]"),
    ("Kapak Tasarımı ve Mizanpaj", "[DOLDUR]"),
    ("Baskı", "[DOLDUR: Şehir | Ay Yıl]"),
    "---",
    ("Yayıncı Sertifika No", "[DOLDUR]"),
  ),
  // Kitaba özel farklar profilden sonra yazılır, ör.: e-kitap: true, bolum-sag-sayfada: false
)

// Metin dosyaları: telif kitapta tek dosya, editörlü kitapta bölüm başına bir dosya.
#include "metin/metin.typ"
