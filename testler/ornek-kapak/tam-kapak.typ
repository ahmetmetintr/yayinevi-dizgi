// Kapak şablonu testi: "Satırların Arasında" için tipografik yön (başlık iki satır çizgisinin arasında).
#import "/eklenti/skills/kapak/sablon/kapak.typ": kapak-olcu, tam-kapak

#let o = kapak-olcu(sayfa-sayisi: 304, yaprak-kalinligi: 0.1mm)
#let murekkep = cmyk(0%, 0%, 0%, 92%)
#let tashih = cmyk(0%, 85%, 80%, 0%)
#let kagit = cmyk(2%, 3%, 8%, 0%)

#let cizgiler(genislik, adet, aralik, vurgu: none) = for i in range(adet) {
  place(dy: i * aralik, line(length: genislik, stroke: (paint: if i == vurgu { tashih } else { murekkep }, thickness: if i == vurgu { 0.9pt } else { 0.35pt })))
}

#show: tam-kapak.with(
  olcu: o,
  zemin-rengi: kagit,
  kilavuz: true,
  on: {
    place(dx: 14mm, dy: 30mm, cizgiler(o.genislik - 14mm + o.tasma, 13, 6.2mm, vurgu: 7))
    place(dx: 14mm, dy: 30mm + 6 * 6.2mm + 0.9mm, text(font: "Libertinus Serif", size: 25pt, fill: murekkep, tracking: -0.01em)[Satırların Arasında])
    place(dx: 14mm, dy: 128mm, text(font: "Libertinus Serif", size: 11pt, style: "italic", fill: murekkep)[Dizgi üzerine denemeler])
    place(dx: 14mm, bottom + left, dy: -16mm, text(font: "Libertinus Serif", size: 12pt, fill: murekkep)[Deneme Yazarı])
  },
  sirt: text(font: "Libertinus Serif", size: 9.5pt, fill: murekkep)[Deneme Yazarı #h(1fr) Satırların Arasında #h(1fr) ÖRNEK],
  arka: pad(x: 16mm, top: 28mm, {
    set text(font: "Libertinus Serif", size: 10.5pt, fill: murekkep)
    set par(justify: true, leading: 0.7em)
    [Bir kitabın sayfasını açtığımızda gözümüz önce metne değil, metnin çevresindeki boşluğa takılır.]
    place(bottom + right, dy: -14mm, rect(width: 38mm, height: 22mm, stroke: 0.4pt + murekkep)[#align(center + horizon, text(size: 7pt)[ISBN barkodu \ (yayınevinden)])])
  }),
)
