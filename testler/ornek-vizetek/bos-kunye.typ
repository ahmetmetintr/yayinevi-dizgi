// Editörlü kitapta künyesi boş yazar: dipnot konmaz, yıldızlar dipnotu olanlar arasında sayılır.
#import "/eklenti/skills/dizgi/sablon/kitap.typ": kitap
#import "/eklenti/skills/dizgi/sablon/profiller.typ": vizetek-editorlu
#import "/eklenti/skills/dizgi/sablon/ogeler.typ": *
#show: kitap.with(..vizetek-editorlu, baslik: "Künye Denemesi", yazar: "Editör: Örnek EDİTÖR", yayinevi: "Örnek Yayıncılık")

#bolum([Künyesi Eksik Yazarlar], yazarlar: (
  ("Birinci YAZAR", [Örnek Üniversitesi. ORCID: 0000-0002-1825-0097]),
  ("İkinci YAZAR", ""),
  ("Üçüncü YAZAR", "Başka Üniversite"),
  ("Dördüncü YAZAR", none),
))
Bölüm metni.
