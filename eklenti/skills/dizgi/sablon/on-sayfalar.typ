// on-sayfalar.typ — Kitabın ön sayfaları (dizgi skill'i); kitap.typ çağırır.
//   "klasik":  1 yarım başlık · 2 boş · 3 iç kapak · 4 künye · (5 ithaf)
//   "vizetek": 1 iç kapak · 2 künye (başlık bloğu, ISBN/DOI, telif notu, emeği geçenler, e-kitap bilgisi, adres)
// Künye: (etiket, değer) çiftlerinden dizi; "---" ayırıcı çizgi, ("", metin) etiketsiz satır.

#let kunye-satirlari(kunye, hiza) = {
  if type(kunye) == content { return kunye }
  for k in kunye {
    if k == "---" {
      v(0.3em)
      align(hiza, line(length: 80%, stroke: 0.4pt))
      v(0.3em)
    } else {
      let (etiket, deger) = k
      align(hiza, block(above: 0.35em, below: 0.35em, if etiket == "" { deger } else [*#etiket:* #deger]))
    }
  }
}

#let baslik-blogu(baslik, alt-baslik, ucuncu-satir, yazar, olcek: 1) = align(center, {
  text(size: 1.9em * olcek, weight: "bold", baslik)
  if alt-baslik != none {
    v(0.4em)
    text(size: 1.25em * olcek, style: "italic", alt-baslik)
  }
  if ucuncu-satir != none {
    v(0.3em)
    text(size: 1.05em * olcek, ucuncu-satir)
  }
  v(1.4em * olcek)
  text(size: 1.05em * olcek, weight: "bold", yazar)
})

#let logo-ciz(logo, genislik: 26mm) = if logo != none { align(center, image(logo, width: genislik)) }

#let on-sayfalar-klasik(a) = {
  set par(first-line-indent: 0pt, justify: false)
  v(28%)
  align(center, text(size: 1.35em, a.baslik))
  pagebreak(to: "odd")
  v(10%)
  baslik-blogu(a.baslik, a.alt-baslik, a.ucuncu-satir, a.yazar)
  place(bottom + center, {
    logo-ciz(a.logo)
    align(center, a.yayinevi)
  })
  pagebreak()
  place(bottom + left, block(width: 100%, {
    set text(size: 0.78em)
    set par(leading: 0.5em, spacing: 0.6em)
    if type(a.kunye) == content { a.kunye } else {
      grid(
        columns: (auto, 1fr), column-gutter: 1em, row-gutter: 0.55em,
        ..a.kunye.filter(k => k != "---").map(((e, d)) => (strong(e), d)).flatten(),
      )
    }
  }))
  if a.ithaf != none {
    pagebreak(to: "odd")
    place(horizon + center, text(style: "italic", a.ithaf))
  }
}

#let on-sayfalar-vizetek(a) = {
  set par(first-line-indent: 0pt, justify: false)
  v(18%)
  baslik-blogu(a.baslik, a.alt-baslik, a.ucuncu-satir, a.yazar)
  place(bottom + center, logo-ciz(a.logo, genislik: 30mm))
  pagebreak()
  v(2%)
  baslik-blogu(a.baslik, a.alt-baslik, a.ucuncu-satir, a.yazar, olcek: 0.8)
  v(1.2em)
  block(width: 100%, {
    set text(size: 0.72em)
    kunye-satirlari(a.kunye, center)
    if a.logo != none {
      v(0.8em)
      logo-ciz(a.logo, genislik: 22mm)
    }
  })
  if a.ithaf != none {
    pagebreak(to: "odd")
    place(horizon + center, text(style: "italic", a.ithaf))
  }
}

#let on-sayfalar(duzen, a) = if duzen == "vizetek" { on-sayfalar-vizetek(a) } else { on-sayfalar-klasik(a) }
