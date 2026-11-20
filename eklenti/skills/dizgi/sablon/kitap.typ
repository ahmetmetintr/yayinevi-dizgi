// kitap.typ — Kitap iç sayfa şablonu (dizgi skill'i)
//
// Kullanım (kitabın ana dosyasında):
//   #import "sablon/kitap.typ": kitap
//   #import "sablon/profiller.typ": vizetek-telif     // ya da klasik, vizetek-editorlu
//   #show: kitap.with(..vizetek-telif, baslik: "…", yazar: "…")
//   #include "metin/metin.typ"                       // metinde: #import "../sablon/ogeler.typ": *
// Ölçüler profilden gelir; kitaba özel farkı ana dosyada parametreyle verin, bu dosyayı değiştirmeyin.

#import "on-sayfalar.typ": on-sayfalar
#import "ogeler.typ": tr-buyuk, bolum-notu, ana-metin-sayfasi, sayfa-etiketi, duz-metin, tablo-elle
#import "harita.typ": kitap-haritasi

#assert(sys.version >= version(0, 13, 0), message: "Bu şablon Typst 0.13 ya da üstünü ister (typst --version).")

// --- Hangi sayfada ne basılır -------------------------------------------------------------

// Ana metindeki ilk bölümün açılış sayfası (numaralı bölüm varsa ilk numaralı bölüm). Vizetek: kitabın üst
// bilgisi bu sayfadan SONRA başlar; ön söz ve içindekilerde basılmaz (Vizetek, 20.11.2026).
#let ilk-bolum-sayfasi() = {
  let bas = ana-metin-sayfasi()
  let bolumler = query(heading.where(level: 1)).filter(b => b.location().page() >= bas)
  let numarali = bolumler.filter(b => b.numbering != none)
  let aday = if numarali.len() > 0 { numarali } else { bolumler }
  if aday.len() > 0 { aday.first().location().page() } else { bas }
}

// Bölüm ya da kısım açılış sayfası mı? (Üst bilgi basılmaz.)
#let acilis-sayfasi-mi(p) = (
  query(heading.where(level: 1)).any(b => b.location().page() == p)
    or query(<dizgi-kisim>).any(k => k.location().page() == p)
)

// Bölümü sağ sayfaya almak için eklenmiş boş sayfa mı? Her bölüm başlığı sayfa sonundan önce
// <dizgi-bolum-oncesi> izi bırakır; iz ile başlık arasında iki sayfa varsa aradaki sayfa boştur.
#let bos-sayfa-mi(p) = (
  query(<dizgi-bolum-oncesi>).any(iz => {
    let bp = iz.value.page()
    p == bp - 1 and bp - iz.location().page() == 2
  })
    or query(<dizgi-kisim-oncesi>).zip(query(<dizgi-kisim>)).any(((o, k)) => {
      let kp = k.location().page()
      p == kp - 1 and kp - o.location().page() == 2
    })
)

#let ust-bilgi(a) = context {
  let p = here().page()
  let bas = if a.ust-bilgi-baslangici == "ilk-bolum" { ilk-bolum-sayfasi() } else { ana-metin-sayfasi() }
  if p >= bas and not acilis-sayfasi-mi(p) and not bos-sayfa-mi(p) {
    set text(font: a.ust-bilgi-yazi-tipi, size: a.ust-bilgi-punto)
    set par(first-line-indent: 0pt, justify: false, leading: 0.4em)
    show footnote: none
    if a.ust-bilgi-bicimi == "kitap" {
      align(center, {
        a.ust-bilgi-ust
        if a.ust-bilgi-alt != none { linebreak() + text(style: "italic", a.ust-bilgi-alt) }
        v(0.25em)
        line(length: 43mm, stroke: 0.5pt)
      })
    } else if calc.even(p) {
      align(center, text(style: "italic", a.ust-bilgi-ust))
    } else {
      let onceki = query(selector(heading.where(level: 1)).before(here()))
      if onceki.len() > 0 { align(center, text(style: "italic", onceki.last().body)) }
    }
  }
}

#let alt-bilgi(a) = context {
  let p = here().page()
  if p >= ana-metin-sayfasi() and not bos-sayfa-mi(p) {
    align(center, text(font: a.sayfa-no-yazi-tipi, size: a.sayfa-no-punto, counter(page).display()))
  }
}

// --- Başlıklar --------------------------------------------------------------------------------

// Başlık boyu: sayı verilirse gövde puntosunun katı (1.08 → %8 büyük), uzunluk verilirse olduğu gibi.
// em kullanılmaz: Typst başlığın içinde kendi büyütmesini uygular, em ona göre büyür.
#let boy(x, punto) = if type(x) in (int, float) { x * punto } else { x }

#let baslik-no(..s) = {
  let s = s.pos()
  if s.len() == 1 { str(s.first()) } else { s.map(str).join(".") + "." }
}

// Yalnız bölüm (1. düzey) numaralı; yazarların kendi numaralı ara başlıkları ikinci kez numaralanmaz.
#let bolum-no(..s) = if s.pos().len() == 1 { str(s.pos().first()) }

#let bolum-acilisi(it, a) = {
  [#metadata(it.location()) <dizgi-bolum-oncesi>]
  pagebreak(to: if a.bolum-sag-sayfada { "odd" } else { none }, weak: true)
  if a.sekil-numarasi != "surekli" {
    counter(figure.where(kind: table)).update(0)
    counter(figure.where(kind: image)).update(0)
  }
  if a.dipnot-bolumde-sifirla { counter(footnote).update(0) }
  v(a.bolum-basi-boslugu)
  block(width: 100%, below: 1.8em, {
    set par(first-line-indent: 0pt, justify: false, leading: 0.35em)
    set align(center)
    set text(font: a.baslik-yazi-tipi)
    let b = a.bolum-basligi
    // Bölüm etiketi başlığın üstünde: metin ("BÖLÜM" → BÖLÜM 1) ya da işlev (n => [#n. Bölüm] → 1. Bölüm).
    if it.numbering != none and a.bolum-etiketi != none {
      let no = counter(heading).display("1")
      let etiket = if type(a.bolum-etiketi) == function { (a.bolum-etiketi)(no) } else [#a.bolum-etiketi #no]
      let boyu = if a.bolum-etiketi-punto == auto { boy(b.punto, a.punto) * 1.2 } else { a.bolum-etiketi-punto }
      text(size: boyu, weight: "regular", etiket)
      v(0.7em)
    }
    let govde = if b.buyuk { tr-buyuk(it.body) } else { it.body }
    let no = if it.numbering != none and a.bolum-etiketi == none [#counter(heading).display("1"). ]
    text(size: boy(b.punto, a.punto), weight: if b.kalin { "bold" } else { "regular" }, no + govde)
    context {
      let n = bolum-notu.get()
      if n != none { footnote(numbering: _ => "*", n) }
    }
  })
}

#let ara-baslik(it, s, punto, numarali) = {
  let govde = if s.at("buyuk", default: false) { tr-buyuk(it.body) } else { it.body }
  let no = if numarali and it.numbering != none { counter(heading).display(it.numbering) + h(0.4em) }
  block(above: s.at("ust", default: 1.5em), below: s.at("alt", default: 0.8em), sticky: true, width: 100%, pad(
    left: s.at("girinti", default: 0pt),
    align(s.at("hiza", default: left), {
      set par(first-line-indent: 0pt, justify: false, leading: 0.3em)
      set text(
        size: boy(s.at("punto", default: 1), punto),
        weight: if s.at("kalin", default: true) { "bold" } else { "regular" },
        style: if s.at("italik", default: false) { "italic" } else { "normal" },
      )
      no + govde
    }),
  ))
}

// --- Tablolar ---------------------------------------------------------------------------------

// Tablo bir sayfaya sığıyorsa bölünmez (başlığıyla birlikte sonraki sayfaya geçer). Sığmıyorsa sıradaki küçük
// punto denenir (Vizetek: 10 → 9 → 8,5 pt). Hiçbirinde sığmayan tablo bölünür; başlığı ilk satırlarıyla aynı
// sayfada kalır. Elle punto: #tablo-puntosu(9pt)[…] (ogeler.typ). alan: (metin genişliği, metin yüksekliği).
#let tablo-yerlesimi(it, puntolar, alan) = context {
  let elle = tablo-elle.get()
  let adaylar = if elle != none { (elle,) } else { puntolar }
  let yukseklik(p) = measure({
    show table: set text(size: p)
    it
  }, width: alan.first()).height
  let sigan = adaylar.find(p => yukseklik(p) <= alan.last())
  show table: set text(size: if sigan == none { adaylar.last() } else { sigan })
  if sigan != none { block(breakable: false, width: 100%, it) } else {
    block(above: 1.4em, below: 0.65em, sticky: true, width: 100%, it.caption)
    block(below: 1.4em, breakable: true, width: 100%, it.body)
  }
}

// --- Ana şablon -------------------------------------------------------------------------------

#let kitap(
  // Kitap
  baslik: "Kitap Adı", alt-baslik: none, ucuncu-satir: none, yazar: "Yazar Adı", yayinevi: "Yayınevi",
  kunye: (), ithaf: none, logo: none, on-sayfa-duzeni: "klasik", icindekiler: "basta", icindekiler-derinligi: 2,
  e-kitap: false,
  // Sayfa
  genislik: 135mm, yukseklik: 210mm, simetrik: false,
  ic-bosluk: 20mm, dis-bosluk: 15mm, ust-bosluk: 20mm, alt-bosluk: 22mm,
  ust-bilgi-araligi: 30% + 0pt, alt-bilgi-araligi: 30% + 0pt,
  // Yazı
  yazi-tipi: "Libertinus Serif", punto: 10.5pt, satir-carpani: 1.3, paragraf-araligi: 0pt,
  girinti: 1.2em, ilk-paragraf-girintisi: false,
  // Üst ve alt bilgi
  ust-bilgi-bicimi: "bolum", ust-bilgi-ust: auto, ust-bilgi-alt: auto, ust-bilgi-yazi-tipi: auto,
  ust-bilgi-punto: 0.85em, sayfa-no-yazi-tipi: auto, sayfa-no-punto: 0.85em,
  ust-bilgi-baslangici: "ana-metin", // ya da "ilk-bolum": birinci bölümün ilk sayfasından sonra
  // Başlıklar
  baslik-yazi-tipi: auto, baslik-numarasi: false, bolum-numarasi: false, bolum-etiketi: none, bolum-etiketi-punto: auto,
  bolum-sag-sayfada: true,
  bolum-basi-boslugu: 28mm, bolum-basligi: (punto: 1.6, kalin: true, buyuk: false),
  basliklar: ("2": (punto: 1.08), "3": (italik: true)),
  icindekiler-bolum-kalin: false,
  // Şekil, tablo, dipnot
  sekil-numarasi: "surekli", sekil-yazisi: (punto: 0.85em, stil: "normal"), tablo-yazisi-hizasi: left,
  tablo-punto: 0.88em, tablo-kucuk-puntolar: (), tablo-baslik-zemini: none,
  dipnot-punto: 0.8em, dipnot-satir-carpani: 1.15, dipnot-bolumde-sifirla: false,
  // İmla provası: imla_denetle.py --isaret dosyasındaki desen; eşleşen yerler sarıyla işaretlenir (baskıda none)
  sari-desen: none,
  govde,
) = {
  let a = (
    punto: punto, baslik: baslik, alt-baslik: alt-baslik, ucuncu-satir: ucuncu-satir, yazar: yazar, yayinevi: yayinevi,
    kunye: kunye, ithaf: ithaf, logo: logo, ust-bilgi-bicimi: ust-bilgi-bicimi,
    ust-bilgi-ust: if ust-bilgi-ust == auto {
      if ust-bilgi-bicimi == "kitap" { tr-buyuk(baslik) } else { baslik }
    } else { ust-bilgi-ust },
    ust-bilgi-alt: if ust-bilgi-alt == auto { alt-baslik } else { ust-bilgi-alt },
    ust-bilgi-yazi-tipi: if ust-bilgi-yazi-tipi == auto { yazi-tipi } else { ust-bilgi-yazi-tipi },
    ust-bilgi-punto: ust-bilgi-punto,
    sayfa-no-yazi-tipi: if sayfa-no-yazi-tipi == auto { yazi-tipi } else { sayfa-no-yazi-tipi },
    sayfa-no-punto: sayfa-no-punto,
    baslik-yazi-tipi: if baslik-yazi-tipi == auto { yazi-tipi } else { baslik-yazi-tipi },
    ust-bilgi-baslangici: ust-bilgi-baslangici, bolum-etiketi: bolum-etiketi, bolum-etiketi-punto: bolum-etiketi-punto,
    bolum-sag-sayfada: bolum-sag-sayfada, bolum-basi-boslugu: bolum-basi-boslugu,
    bolum-basligi: bolum-basligi, sekil-numarasi: sekil-numarasi, dipnot-bolumde-sifirla: dipnot-bolumde-sifirla,
  )
  set document(title: baslik, author: yazar)
  set page(
    width: genislik, height: yukseklik, binding: left, numbering: "1",
    margin: if simetrik { (x: dis-bosluk, top: ust-bosluk, bottom: alt-bosluk) } else {
      (inside: ic-bosluk, outside: dis-bosluk, top: ust-bosluk, bottom: alt-bosluk)
    },
    header-ascent: ust-bilgi-araligi, footer-descent: alt-bilgi-araligi,
    header: ust-bilgi(a), footer: alt-bilgi(a),
  )
  // Satır adımı = punto × satir-carpani; yazı tipinin iç ölçülerinden bağımsız.
  set text(font: yazi-tipi, size: punto, lang: "tr", region: "TR", hyphenate: true, fill: black,
    top-edge: 0.8em, bottom-edge: -0.2em)
  set par(
    justify: true, leading: (satir-carpani - 1) * 1em, spacing: (satir-carpani - 1) * 1em + paragraf-araligi,
    first-line-indent: (amount: girinti, all: ilk-paragraf-girintisi),
  )

  set heading(numbering: if baslik-numarasi { baslik-no } else if bolum-numarasi { bolum-no } else { none })
  show heading: set text(hyphenate: false)
  show heading: it => if it.level == 1 { bolum-acilisi(it, a) } else {
    ara-baslik(it, basliklar.at(str(it.level), default: (:)), punto, baslik-numarasi)
  }

  set figure(numbering: if sekil-numarasi == "bolum" {
    n => numbering("1.1", counter(heading).get().first(), n)
  } else { "1" })
  set figure.caption(separator: [. ])
  show figure: set block(above: 1.4em, below: 1.4em)
  show figure: set par(first-line-indent: 0pt)              // görsel paragraf girintisiyle kaymasın
  show figure.where(kind: table): set block(breakable: true) // bölünüp bölünmeyeceğine tablo-yerlesimi karar verir
  show figure.where(kind: table): set figure.caption(position: top)
  show figure.caption: it => {
    set text(size: sekil-yazisi.punto, style: if sekil-yazisi.stil == "italik" { "italic" } else { "normal" },
      weight: if sekil-yazisi.stil == "kalin" { "bold" } else { "regular" })
    set par(first-line-indent: 0pt, justify: false, hanging-indent: 0pt)
    align(if it.kind == table { tablo-yazisi-hizasi } else { center }, it)
  }
  set table(stroke: 0.5pt + black, inset: 4pt, fill: (x, y) => if y == 0 { tablo-baslik-zemini })
  show table: set text(size: tablo-punto)
  show table: set par(justify: false, first-line-indent: 0pt, hanging-indent: 0pt, leading: 0.2em, spacing: 0.4em)
  show table: set list(indent: 0pt)                         // tablo içi metin girintisiz (Vizetek, 20.11.2026)
  show table: set enum(indent: 0pt)
  let metin-alani = (
    genislik - if simetrik { 2 * dis-bosluk } else { ic-bosluk + dis-bosluk },
    yukseklik - ust-bosluk - alt-bosluk,
  )
  show figure.where(kind: table): it => tablo-yerlesimi(it, (tablo-punto,) + tablo-kucuk-puntolar, metin-alani)

  set footnote.entry(separator: line(length: 25%, stroke: 0.4pt), clearance: 0.9em, gap: 0.4em, indent: 0pt)
  show footnote.entry: set text(size: dipnot-punto)
  show footnote.entry: set par(first-line-indent: 0pt, leading: (dipnot-satir-carpani - 1) * 1em, justify: false)
  // E-posta adresi bölünmez, tirelenmez ("sti-lev@gmail.com" olmasın). Bağlantılar kutulanmaz: uzun DOI taşar.
  show regex("[\\w.+\\-]+@[\\w\\-]+(\\.[\\w\\-]+)+"): it => box(it)

  show quote.where(block: true): it => block(above: 1.2em, below: 1.2em, pad(x: girinti, {
    set text(size: 0.92em)
    set par(first-line-indent: 0pt)
    it.body
    if it.attribution != none { block(above: 0.6em, width: 100%, align(right)[— #it.attribution]) }
  }))
  set list(indent: girinti)
  set enum(indent: girinti)
  // Bağlantılar siyah ve altı çizgisiz (Vizetek, 20.11.2026); e-kitapta tıklanır kalır. Word'den altı çizili gelen
  // adres (pandoc: #underline[https:/\/…]) de düz basılır; altı çizili sıradan yazıya dokunulmaz.
  show link: it => {
    show underline: u => u.body
    set text(fill: black)
    if e-kitap { it } else { it.body }
  }
  show underline: it => if duz-metin(it.body).trim().starts-with(regex("(https?://|www\\.|doi:|10\\.\\d{4,9}/)")) {
    it.body
  } else { it }
  // Times New Roman'da olmayan karakterler eşdeğerine (kaynak metin değişmez; yedek yazı tipi ve kutucuk olmasın)
  show regex("[\u{2010}\u{2011}]"): "-"
  show "\u{1F86A}": sym.arrow.r
  show regex("[₀₁₂₃₄₅₆₇₈₉]+"): it => sub(it.text.clusters().map(c => str("₀₁₂₃₄₅₆₇₈₉".clusters().position(x => x == c))).join())
  show regex("[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]*[⁰⁴⁵⁶⁷⁸⁹⁺⁻][⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]*"): it => super(it.text.clusters().map(c => {
    let i = "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻".clusters().position(x => x == c)
    if i == none { c } else { "0123456789+−".clusters().at(i) }
  }).join())

  set outline(indent: auto, depth: icindekiler-derinligi)
  show outline.entry: it => {
    show footnote: none
    let yer = it.element.location()
    if yer.page() >= ana-metin-sayfasi() { it } else {  // ön söz: romen rakamı (ana metin 1'den başlar)
      link(yer, it.indented(it.prefix(), [#it.body() #box(width: 1fr, it.fill) #sayfa-etiketi(yer)]))
    }
  }
  show outline.entry.where(level: 1): set block(above: 0.9em)
  show outline.entry.where(level: 1): set text(weight: if icindekiler-bolum-kalin { "bold" } else { "regular" })

  on-sayfalar(on-sayfa-duzeni, a)
  if icindekiler == "basta" { outline(title: [İçindekiler]) }
  [#metadata("oto") <dizgi-ana-metin>]
  if sari-desen == none { govde } else {
    show regex(sari-desen): it => highlight(fill: rgb("#FFE44D"), extent: 1pt, it)
    govde
  }
  context [#metadata(kitap-haritasi(baslik, yazar)) <dizgi-harita>]  // bolum_pdfleri.py okur
}
