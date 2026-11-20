// Vizetek telif kitap profili testi (kısım, BÖLÜM etiketi, numaralı başlıklar, Tablo 2.1.).
#import "/eklenti/skills/dizgi/sablon/kitap.typ": kitap
#import "/eklenti/skills/dizgi/sablon/profiller.typ": vizetek-telif
#import "/eklenti/skills/dizgi/sablon/ogeler.typ": *
#show: kitap.with(..vizetek-telif, baslik: "Satırların Arasında", alt-baslik: "Dizgi Üzerine Denemeler",
  ucuncu-satir: "Uygulayıcılar İçin Bir El Kitabı", yazar: "Dr. Deneme YAZAR", yayinevi: "Örnek Yayıncılık",
  kunye: (("ISBN", "978-000-00-0000-0"),))
#numarasiz[Ön Söz]
Ön söz metni.
#icindekiler-sayfasi()
#ana-metin-baslat()
#kisim("I")[Giriş ve Temeller]
= Giriş: Dizgi Nedir
== İlk Kavramlar
#for i in range(14) [Dizgi, metni okunur kılan görünmez düzendir; kenar boşluklarından satır aralığına kadar her karar okurun yorulmadan ilerlemesine hizmet eder. ]
#kutu(baslik: [Uygulamaya Köprü 1.1])[Kutudaki metin, bölümde anlatılanı uygulamaya bağlar.]
= Tarihsel Geçmiş
== Kurşun Harften Dijitale
#figure(table(columns: 2, [Dönem], [Teknik], [1900], [Kurşun], [2000], [Dijital]), caption: [Dizgi tekniklerinin dönemleri])
