// Gruplu editörlü kitap testi: "BÖLÜM n" grupları, alt grup, numaralı bölümler, gruplu içindekiler.
#import "/eklenti/skills/dizgi/sablon/kitap.typ": kitap
#import "/eklenti/skills/dizgi/sablon/profiller.typ": vizetek-editorlu
#import "/eklenti/skills/dizgi/sablon/ogeler.typ": *
#show: kitap.with(..vizetek-editorlu, bolum-numarasi: true, baslik: "Klinik Deneme", yazar: "Editör: Ad SOYAD")
#ana-metin-baslat()
#numarasiz[Ön Söz]
Ön söz.
#icindekiler-sayfasi()
#kisim("1", etiket: "BÖLÜM")[Temel İlkeler ve Fizyoloji]
#bolum([Çocuklarda Fizyolojik Farklılıklar], yazarlar: (("Ad SOYAD", [Op. Dr., Örnek Hastanesi. ORCID: 0000-0002-1825-0097]),))
== 1. Giriş
Metin.
== 1.1. Alt başlık
Metin.
#bolum([Perioperatif Bakım], yazarlar: (("Ali SEVGİLİ", [Uzm. Dr., Örnek Hastanesi.]),))
Metin.
#kisim("2", etiket: "BÖLÜM")[Gastrointestinal Sistem Cerrahisi]
#alt-grup[Üst Gastrointestinal Sistem]
#bolum([Yabancı Cisimler], yazarlar: (("Atilla CAN", [Dr. Öğr. Üyesi.]),))
Metin.
#alt-grup[Alt Gastrointestinal Sistem ve Karın Duvarı]
#bolum([Meckel Divertikülü], yazarlar: (("Emine BİLALOĞLU", [Dr. Öğr. Üyesi.]),))
Metin.
