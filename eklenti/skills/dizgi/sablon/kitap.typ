// kitap.typ — Kitap iç sayfa şablonu (dizgi skill'i)
//
// Kullanım (kitabın ana dosyasında):
//   #import "sablon/kitap.typ": kitap, sahne-arasi
//   #show: kitap.with(baslik: "…", yazar: "…", yayinevi: "…")
//   #include "metin/metin.typ"
//
// Varsayılanlar 13,5 × 21 cm kitap içindir. Yayınevi kuralları farklıysa değerleri
// kitabın ana dosyasında parametreyle verin; bu dosyayı kitap kitap değiştirmeyin.

#assert(
  sys.version >= version(0, 13, 0),
  message: "Bu şablon Typst 0.13 ya da üstünü ister (typst --version).",
)

// --- Hangi sayfada ne basılır -------------------------------------------------------

// Ana metnin (ilk bölümün) başladığı fiziksel sayfa. Ön sayfalarda numara ve üst bilgi yok.
#let ana-metin-sayfasi() = {
  let iz = query(<dizgi-ana-metin>)
  if iz.len() == 0 { return 1 }
  let sonraki = query(selector(heading.where(level: 1)).after(iz.first().location()))
  if sonraki.len() > 0 { sonraki.first().location().page() } else { iz.first().location().page() }
}

// Bölüm açılış sayfası mı? (Üst bilgi basılmaz.)
#let bolum-acilisi-mi(p) = query(heading.where(level: 1)).any(b => b.location().page() == p)

// Bölümü sağ sayfaya almak için eklenmiş boş sayfa mı? (Numara da üst bilgi de basılmaz.)
// Her bölüm başlığı, sayfa sonundan önce <dizgi-bolum-oncesi> izi bırakır; iz ile başlık
// arasında iki sayfa fark varsa aradaki sayfa boştur.
#let bos-sayfa-mi(p) = query(<dizgi-bolum-oncesi>).any(iz => {
  let bp = iz.value.page()
  p == bp - 1 and bp - iz.location().page() == 2
})

#let ust-bilgi(cift-sayfa-metni) = context {
  let p = here().page()
  if p >= ana-metin-sayfasi() and not bolum-acilisi-mi(p) and not bos-sayfa-mi(p) {
    set text(size: 0.85em, style: "italic")
    if calc.even(p) {
      align(center, cift-sayfa-metni)
    } else {
      let onceki = query(selector(heading.where(level: 1)).before(here()))
      if onceki.len() > 0 { align(center, onceki.last().body) }
    }
  }
}

#let alt-bilgi() = context {
  let p = here().page()
  if p >= ana-metin-sayfasi() and not bos-sayfa-mi(p) {
    align(center, text(size: 0.85em, counter(page).display()))
  }
}

// --- Ön sayfalar: yarım başlık, iç kapak, künye, ithaf ------------------------------

#let on-sayfalar(baslik, alt-baslik, yazar, yayinevi, kunye, ithaf) = {
  set par(first-line-indent: 0pt, justify: false)
  // s. 1 — yarım başlık (sağ sayfa); s. 2 boş kalır
  v(28%)
  align(center, text(size: 1.35em, baslik))
  pagebreak(to: "odd")
  // s. 3 — iç kapak
  align(center, {
    v(12%)
    text(size: 1.1em, yazar)
    v(2.4em)
    text(size: 2em, weight: "bold", baslik)
    if alt-baslik != none {
      v(0.8em)
      text(size: 1.15em, style: "italic", alt-baslik)
    }
  })
  place(bottom + center, text(yayinevi))
  pagebreak()
  // s. 4 — künye (sol sayfa, sayfa dibinde)
  place(bottom + left, block(width: 100%, {
    set text(size: 0.78em)
    set par(leading: 0.5em, spacing: 0.6em)
    if type(kunye) == content {
      kunye
    } else {
      grid(
        columns: (auto, 1fr),
        column-gutter: 1em,
        row-gutter: 0.55em,
        ..kunye.map(((etiket, deger)) => (strong(etiket), deger)).flatten(),
      )
    }
  }))
  // s. 5 — ithaf (isteğe bağlı, sağ sayfa)
  if ithaf != none {
    pagebreak(to: "odd")
    place(horizon + center, text(style: "italic", ithaf))
  }
}

// Roman ve öyküde sahne arası: #sahne-arasi
#let sahne-arasi = block(above: 1.3em, below: 1.3em, width: 100%, align(center)[\* #h(0.6em) \* #h(0.6em) \*])

// --- Ana şablon ------------------------------------------------------------------------

#let kitap(
  baslik: "Kitap Adı",
  alt-baslik: none,
  yazar: "Yazar Adı",
  yayinevi: "Yayınevi",
  kunye: (),
  ithaf: none,
  ust-bilgi-cift: auto, // sol (çift) sayfa üst bilgisi; auto = kitap adı
  genislik: 135mm,
  yukseklik: 210mm,
  ic-bosluk: 20mm, // cilt tarafı
  dis-bosluk: 15mm,
  ust-bosluk: 20mm,
  alt-bosluk: 22mm,
  yazi-tipi: "Libertinus Serif",
  punto: 10.5pt,
  satir-araligi: 0.65em,
  girinti: 1.2em,
  bolum-basi-boslugu: 28mm,
  icindekiler: true,
  govde,
) = {
  set document(title: baslik, author: yazar)
  set page(
    width: genislik,
    height: yukseklik,
    margin: (inside: ic-bosluk, outside: dis-bosluk, top: ust-bosluk, bottom: alt-bosluk),
    binding: left,
    numbering: "1",
    header: ust-bilgi(if ust-bilgi-cift == auto { baslik } else { ust-bilgi-cift }),
    footer: alt-bilgi(),
  )
  set text(font: yazi-tipi, size: punto, lang: "tr", region: "TR", hyphenate: true, fill: black)
  set par(
    justify: true,
    leading: satir-araligi,
    spacing: satir-araligi,
    first-line-indent: (amount: girinti, all: false),
  )

  // Bölüm başlığı: her zaman sağ (tek) sayfada açılır.
  show heading.where(level: 1): it => {
    [#metadata(it.location()) <dizgi-bolum-oncesi>]
    pagebreak(to: "odd", weak: true)
    v(bolum-basi-boslugu)
    block(width: 100%, below: 2.2em, {
      set par(justify: false, first-line-indent: 0pt)
      set align(center)
      text(size: 1.6em, weight: "bold", it.body)
    })
  }
  // Ara başlıklar sayfa dibinde yalnız kalmaz (sticky).
  show heading.where(level: 2): it => block(above: 1.8em, below: 1em, sticky: true, {
    set par(justify: false, first-line-indent: 0pt)
    text(size: 1.08em, weight: "bold", it.body)
  })
  show heading.where(level: 3): it => block(above: 1.4em, below: 0.8em, sticky: true, {
    set par(justify: false, first-line-indent: 0pt)
    text(weight: "bold", style: "italic", it.body)
  })

  set footnote.entry(separator: line(length: 25%, stroke: 0.4pt), clearance: 0.9em, gap: 0.4em, indent: 0pt)
  show footnote.entry: set text(size: 0.8em)
  show footnote.entry: set par(first-line-indent: 0pt, leading: 0.5em)

  show quote.where(block: true): it => block(above: 1.2em, below: 1.2em, pad(x: girinti, {
    set text(size: 0.92em)
    set par(first-line-indent: 0pt)
    it.body
    if it.attribution != none { block(above: 0.6em, width: 100%, align(right)[— #it.attribution]) }
  }))

  show figure: set block(above: 1.4em, below: 1.4em)
  show figure.caption: set text(size: 0.85em)
  set table(stroke: 0.4pt + black, inset: 4pt)
  show table: set text(size: 0.88em)
  show table: set par(justify: false, first-line-indent: 0pt)
  set list(indent: girinti)
  set enum(indent: girinti)
  show link: it => it.body // basılı kitapta bağlantı düz metindir

  set outline(indent: auto, depth: 2)
  show outline.entry.where(level: 1): set block(above: 0.9em)

  on-sayfalar(baslik, alt-baslik, yazar, yayinevi, kunye, ithaf)
  if icindekiler { outline(title: [İçindekiler]) }
  [#metadata("ana-metin") <dizgi-ana-metin>]
  govde
}
