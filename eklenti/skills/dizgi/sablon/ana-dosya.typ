// Bu kitabın ana dosyası (dizgi skill'i). Derleme:
//   typst compile kitap.typ cikti/kitap.pdf
// Ölçü, yazı tipi ve künye bilgileri yayınevi kurallarından gelir; [DOLDUR] yazan yerleri doldurun.

#import "sablon/kitap.typ": kitap, sahne-arasi

#show: kitap.with(
  baslik: "[DOLDUR: Kitap adı]",
  alt-baslik: none,
  yazar: "[DOLDUR: Yazar adı]",
  yayinevi: "[DOLDUR: Yayınevi adı]",
  kunye: (
    ("Kitabın adı", "[DOLDUR]"),
    ("Yazar", "[DOLDUR]"),
    ("Editör", "[DOLDUR]"),
    ("Dizgi", "[DOLDUR]"),
    ("Kapak tasarımı", "[DOLDUR]"),
    ("ISBN", "[DOLDUR]"),
    ("Yayıncı sertifika no", "[DOLDUR]"),
    ("Baskı ve cilt", "[DOLDUR: Matbaa adı, adresi, matbaa sertifika no]"),
    ("Birinci basım", "[DOLDUR: Ay Yıl]"),
    ("", "[DOLDUR: Telif notu]"),
  ),
  // Yayınevi kuralları farklıysa burada değiştirin:
  // genislik: 135mm, yukseklik: 210mm, ic-bosluk: 20mm, dis-bosluk: 15mm,
  // ust-bosluk: 20mm, alt-bosluk: 22mm, yazi-tipi: "Libertinus Serif", punto: 10.5pt,
)

#include "metin/metin.typ"
