// profiller.typ — Hazır yayınevi profilleri (dizgi skill'i)
//   #show: kitap.with(..vizetek-telif, baslik: "…", yazar: "…")
// Profil yalnız ayar taşır; kitaba özel bir farkı ana dosyada profilden sonra yazın (sonraki kazanır).

// Kitap şablonunun kendi varsayılanları: 13,5 × 21 cm genel kitap, Libertinus Serif.
#let klasik = (:)

// Vizetek Yayıncılık — kaynaklar: 2026 Yazım Kılavuzu, 16×24 örnek kitap şablonu ve Vizetek'in dizdiği
// bir kitabın ölçümü (Kasım 2026). Word'deki 11 pt / 1,15 satır aralığı = 14,5 pt satır adımı.
#let vizetek-ortak = (
  genislik: 160mm, yukseklik: 240mm, simetrik: true,
  dis-bosluk: 20mm, ust-bosluk: 25mm, alt-bosluk: 25mm,
  ust-bilgi-araligi: 5mm, alt-bilgi-araligi: 8mm,
  yazi-tipi: ("Times New Roman", "Libertinus Serif"),
  punto: 11pt, satir-carpani: 1.32, paragraf-araligi: 6pt,
  girinti: 5mm, ilk-paragraf-girintisi: true,
  ust-bilgi-bicimi: "kitap", ust-bilgi-yazi-tipi: ("Calibri", "Carlito", "Libertinus Serif"), ust-bilgi-punto: 9pt,
  sayfa-no-yazi-tipi: ("Lato", "Calibri", "Carlito", "Libertinus Serif"), sayfa-no-punto: 8pt,
  ust-bilgi-baslangici: "ilk-bolum", // üst bilgi 1. bölümün ilk sayfasından sonra (Vizetek, 20.11.2026)
  on-sayfa-duzeni: "vizetek", icindekiler: "elle", icindekiler-bolum-kalin: true,
  bolum-basi-boslugu: 22mm,
  // Tablo: 10 pt, sayfaya sığmazsa 9 ve 8,5 pt; başlığı girintisiz ve ortalı (Vizetek, 20.11.2026)
  tablo-punto: 10pt, tablo-kucuk-puntolar: (9pt, 8.5pt), tablo-baslik-zemini: luma(88%), tablo-yazisi-hizasi: center,
  sekil-yazisi: (punto: 10pt, stil: "italik"),
  dipnot-punto: 9pt, dipnot-satir-carpani: 1.15,
)

// Telif kitap (tek ya da birkaç yazarlı): "BÖLÜM 1" etiketi, numaralı ara başlıklar (1.1.), Tablo 2.1.
#let vizetek-telif = vizetek-ortak + (
  baslik-numarasi: true, bolum-etiketi: "BÖLÜM", sekil-numarasi: "bolum", bolum-basi-boslugu: 0mm,
  baslik-yazi-tipi: ("Fraunces", "Times New Roman", "Libertinus Serif"),
  bolum-basligi: (punto: 20pt, kalin: false, buyuk: false),
  basliklar: (
    "2": (girinti: 5mm),
    "3": (girinti: 5mm, italik: true),
    "4": (girinti: 5mm, kalin: false, italik: true),
  ),
)

// Editörlü kitap (bölüm yazarları ayrı): bölümler numaralı, başlığın üstünde "1. Bölüm" etiketi; bölüm
// başlığı tümü büyük harf; yazarlar sağa yaslı, unvan/kurum/ORCID dipnotta (#bolum); tablo ve dipnot
// numaraları her bölümde 1'den başlar. Ara başlıkların hepsi 3. düzey gibi: sola yaslı, girintisiz, üstte ve
// altta aynı boşluk; yazarın yazdığı gibi (tümü büyük harfe çevrilmez) (Vizetek, 20.11.2026).
#let vizetek-editorlu = vizetek-ortak + (
  baslik-numarasi: false, bolum-numarasi: true, bolum-etiketi: n => [#n. Bölüm], bolum-etiketi-punto: 12pt,
  sekil-numarasi: "bolum-basina", dipnot-bolumde-sifirla: true,
  bolum-basligi: (punto: 13pt, kalin: true, buyuk: true),
  basliklar: (
    "2": (hiza: left),
    "3": (hiza: left),
    "4": (hiza: left),
    "5": (hiza: left),
    "6": (hiza: left, kalin: false),
  ),
)
