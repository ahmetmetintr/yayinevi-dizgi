// Şablon testi için örnek kitap (eğitim kiti testleri). Derleme kökü: kitin kök klasörü.
#import "/eklenti/skills/dizgi/sablon/kitap.typ": kitap, sahne-arasi

#show: kitap.with(
  baslik: "Satırların Arasında",
  alt-baslik: "Dizgi Üzerine Denemeler",
  yazar: "Deneme Yazarı",
  yayinevi: "Örnek Yayınları",
  kunye: (
    ("Kitabın adı", "Satırların Arasında"),
    ("Yazar", "Deneme Yazarı"),
    ("ISBN", "978-000-00-0000-0"),
    ("Yayıncı sertifika no", "00000"),
    ("Birinci basım", "Kasım 2026"),
  ),
  ithaf: [Bütün mürettiplere],
)

#include "metin/metin.typ"
