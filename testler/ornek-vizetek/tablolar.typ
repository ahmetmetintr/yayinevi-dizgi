// Tablo yerleşimi testi: sığan tablo bölünmez, sığmayan önce 9 ve 8,5 pt'ye küçülür, yine sığmayan bölünür
// ve başlığı ilk satırlarıyla aynı sayfada kalır; tablo altı not, bağlantı rengi ve altı çizili adres.
#import "/eklenti/skills/dizgi/sablon/kitap.typ": kitap
#import "/eklenti/skills/dizgi/sablon/profiller.typ": vizetek-editorlu
#import "/eklenti/skills/dizgi/sablon/ogeler.typ": *
#show: kitap.with(..vizetek-editorlu, baslik: "Tablo Denemesi", yazar: "Editör: Ad SOYAD")
#icindekiler-sayfasi()
#ana-metin-baslat()
#bolum([Tablolar], yazarlar: (("Ad SOYAD", [Dr., Örnek Üniversitesi. ORCID: 0000-0002-1825-0097]),))
== Giriş
#for i in range(9) [Bu paragraf sayfayı doldurmak için yazıldı; tablonun sayfa sonuna denk gelmesi isteniyor. ]

#notlu-sekil(figure(numbering: none, caption: [#strong[Tablo 1.] Sayfaya sığan ama burada yer kalmayan tablo],
  table(columns: 2, table.header([Satır], [Değer]), ..range(14).map(i => ([Satır #i], [- Madde #i])).flatten())))[#emph[Not.] Değerler örnektir. Kaynak: #underline[https:/\/doi.org/10.0000/ornek] ve #link("https://ornek.org")[ornek.org].]

#figure(numbering: none, caption: [#strong[Tablo 2.] On punto sığmayan, dokuz puntoda sığan tablo],
  table(columns: 2, table.header([Satır], [Değer]), ..range(38).map(i => ([Satır #i], [Değer #i])).flatten()))

Ara paragraf. #for i in range(5) [Bu paragraf sayfayı doldurmak için yazıldı. ]

#figure(numbering: none, caption: [#strong[Tablo 3.] Hiçbir puntoda tek sayfaya sığmayan uzun tablo],
  table(columns: 2, table.header([Satır], [Değer]), ..range(90).map(i => ([Satır #i], [Değer #i])).flatten()))
Tablodan sonraki paragraf.
