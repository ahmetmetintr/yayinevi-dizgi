// Vizetek editörlü kitap profili testi.
#import "/eklenti/skills/dizgi/sablon/kitap.typ": kitap
#import "/eklenti/skills/dizgi/sablon/profiller.typ": vizetek-editorlu
#show: kitap.with(..vizetek-editorlu,
  baslik: "Eğitimde Güncel Yaklaşımlar", alt-baslik: "Kuram ve Uygulama", yazar: "Editör: Doç. Dr. Örnek EDİTÖR",
  yayinevi: "Örnek Yayıncılık",
  kunye: (
    ("ISBN", "978-000-00-0000-0"), ("E-ISBN", "978-000-00-0000-1"), ("DOI", "10.00000/ornek.9780000000001"),
    "---",
    ("", [Copyright © Örnek Yayıncılık. Bu kitabın basım, yayım ve satış hakları yayınevine aittir.]),
    "---",
    ("Yayın Koordinatörü", "Ad SOYAD"), ("Kapak Tasarımı ve Mizanpaj", "Ad SOYAD"), ("Baskı", "Ankara | Kasım 2026"),
    ("Materyal Türü", "Elektronik Kitap (Çevrim içi / Web tabanlı)"), ("Elektronik Yayın Formatı", "PDF"),
    "---",
    ("Web", "www.ornek.com.tr"), ("Yayıncı Sertifika No", "00000"),
  ),
)
#include "metin-editorlu.typ"
