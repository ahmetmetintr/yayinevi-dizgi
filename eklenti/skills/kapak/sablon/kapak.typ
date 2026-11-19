// kapak.typ — Kitap kapağı ölçü şablonu (kapak skill'i)
//
// Tasarımı değil, ölçüyü taşır: kesim, sırt ve taşma payı hep doğru yerde olur; tasarım kendi dosyasında kalır.
//   #import "sablon/kapak.typ": kapak-olcu, tam-kapak, on-kapak-eskiz
//   #let o = kapak-olcu(sayfa-sayisi: 304, yaprak-kalinligi: 0.1mm)
//   #show: tam-kapak.with(olcu: o, on: [...], arka: [...], sirt: [...])
// Renkleri cmyk(...) ile verin: baskıya dönüşümsüz gider.

// Bütün ölçüler tek yerde. Sırtı matbaa verdiyse `sirt` ile kesin değeri yazın.
#let kapak-olcu(
  genislik: 135mm,
  yukseklik: 210mm,
  sayfa-sayisi: 200,
  yaprak-kalinligi: 0.1mm, // kâğıdın bir yaprağının kalınlığı (matbaadan)
  sirt: auto,
  tasma: 3mm,
) = {
  let s = if sirt == auto { yaprak-kalinligi * sayfa-sayisi / 2 } else { sirt }
  (
    genislik: genislik,
    yukseklik: yukseklik,
    sirt: s,
    tasma: tasma,
    tam-genislik: 2 * genislik + s + 2 * tasma,
    tam-yukseklik: yukseklik + 2 * tasma,
    x-arka: tasma,
    x-sirt: tasma + genislik,
    x-on: tasma + genislik + s,
  )
}

// Prova kılavuzu: kesim (macenta), sırt katlama (cyan), güvenli alan (gri kesikli). Baskı dosyasında kapatın.
#let kilavuz-ciz(o, guvenli: 5mm) = {
  let cizgi(x0, y0, x1, y1, renk, kesikli: false) = place(
    line(start: (x0, y0), end: (x1, y1), stroke: (paint: renk, thickness: 0.4pt, dash: if kesikli { "dashed" } else { none })),
  )
  let kesim = cmyk(0%, 100%, 0%, 0%)
  let katlama = cmyk(100%, 0%, 0%, 0%)
  cizgi(0pt, o.tasma, o.tam-genislik, o.tasma, kesim)
  cizgi(0pt, o.tasma + o.yukseklik, o.tam-genislik, o.tasma + o.yukseklik, kesim)
  cizgi(o.tasma, 0pt, o.tasma, o.tam-yukseklik, kesim)
  cizgi(o.tam-genislik - o.tasma, 0pt, o.tam-genislik - o.tasma, o.tam-yukseklik, kesim)
  cizgi(o.x-sirt, 0pt, o.x-sirt, o.tam-yukseklik, katlama)
  cizgi(o.x-on, 0pt, o.x-on, o.tam-yukseklik, katlama)
  for x in (o.x-arka, o.x-on) {
    place(dx: x + guvenli, dy: o.tasma + guvenli, rect(
      width: o.genislik - 2 * guvenli,
      height: o.yukseklik - 2 * guvenli,
      stroke: (paint: luma(60%), thickness: 0.4pt, dash: "dashed"),
    ))
  }
}

// Sırt yazısı. "yukaridan-asagi": kitap sırtüstü yatınca ön kapak üstteyken okunur.
#let sirt-yazisi(o, icerik, yon: "yukaridan-asagi", kenar: 6mm) = {
  let aci = if yon == "yukaridan-asagi" { 90deg } else { -90deg }
  block(width: o.sirt, height: o.yukseklik, align(center + horizon, rotate(aci, reflow: true, block(
    width: o.yukseklik - 2 * kenar,
    height: o.sirt,
    align(horizon, icerik),
  ))))
}

// Tam kapak: arka + sırt + ön, taşma paylı tek sayfa.
// `zemin`: bütün açılımı kaplayan çizim (koordinat sayfanın sol üstünden; kapak-olcu değerleriyle).
#let tam-kapak(
  olcu: kapak-olcu(),
  zemin-rengi: cmyk(0%, 0%, 0%, 0%),
  zemin: none,
  arka: none,
  sirt: none,
  on: none,
  sirt-yonu: "yukaridan-asagi",
  kilavuz: false,
  govde,
) = {
  let o = olcu
  set page(width: o.tam-genislik, height: o.tam-yukseklik, margin: 0pt, fill: zemin-rengi)
  set text(lang: "tr", region: "TR", hyphenate: false)
  if zemin != none { place(zemin) }
  place(dx: o.x-arka, dy: o.tasma, block(width: o.genislik, height: o.yukseklik, arka))
  if sirt != none { place(dx: o.x-sirt, dy: o.tasma, sirt-yazisi(o, sirt, yon: sirt-yonu)) }
  place(dx: o.x-on, dy: o.tasma, block(width: o.genislik, height: o.yukseklik, on))
  if kilavuz { kilavuz-ciz(o) }
  govde
}

// Eskiz: yalnız ön kapak, kesim ölçüsünde. Yönleri karşılaştırmak için her yön ayrı sayfa olur.
#let on-kapak-eskiz(olcu: kapak-olcu(), zemin-rengi: cmyk(0%, 0%, 0%, 0%), icerik) = {
  page(width: olcu.genislik, height: olcu.yukseklik, margin: 0pt, fill: zemin-rengi, {
    set text(lang: "tr", region: "TR", hyphenate: false)
    icerik
  })
}
