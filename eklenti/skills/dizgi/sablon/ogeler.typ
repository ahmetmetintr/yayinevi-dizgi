// ogeler.typ — Metin içinde kullanılan yardımcılar (dizgi skill'i)
//   #import "../sablon/ogeler.typ": *
// Hepsi kitap.typ'nin ayarlarıyla birlikte çalışır; tek başına sayfa kurmazlar.

// Türkçe büyük harf: Typst'in upper() işlevi i → I yapar; burada önce i → İ çevrilir.
#let tr-buyuk(icerik) = {
  show "i": "İ"
  upper(if type(icerik) == str { [#icerik] } else { icerik })  // düz metin de içerik olsun ki kural işlesin
}

// İçeriği düz yazıya çevirir (bölüm haritası, PDF dosya adı, bağlantı denetimi): biçim ve dipnot atılır.
#let duz-metin(c) = {
  if c == none { "" } else if type(c) == str { c } else if c.func() == footnote { "" } else if c.has("text") {
    c.text
  } else if c.has("children") { c.children.map(duz-metin).sum(default: "") } else if c.has("body") {
    duz-metin(c.body)
  } else if c.func() == smartquote { if c.double { "\"" } else { "'" } } else if c.func() in ([ ].func(), linebreak) {
    " "
  } else { "" }
}

// Numarasız ön ya da son bölüm başlığı (Ön Söz, Takdim, Katkıda Bulunanlar, Dizin…).
#let numarasiz(baslik, icindekilerde: true) = heading(level: 1, numbering: none, outlined: icindekilerde, baslik)

// Ön sayfalar bitti, ana metin başlıyor: sayfa numarası buradan 1'den basılır. Vizetek: içindekilerden hemen sonra.
#let ana-metin-baslat(numara-sifirla: true) = {
  pagebreak(to: "odd", weak: true)
  if numara-sifirla { counter(page).update(1) }
  [#metadata("elle") <dizgi-ana-metin>]
}

// Sayfa numarası ve üst bilginin başladığı fiziksel sayfa: #ana-metin-baslat() varsa orası,
// yoksa ön sayfalardan sonraki ilk bölüm (kitap.typ "oto" izini bırakır).
#let ana-metin-sayfasi() = {
  let izler = query(<dizgi-ana-metin>)
  if izler.len() == 0 { return 1 }
  let elle = izler.filter(i => i.value == "elle")
  if elle.len() > 0 { return elle.first().location().page() }
  let sonraki = query(selector(heading.where(level: 1)).after(izler.first().location()))
  if sonraki.len() > 0 { sonraki.first().location().page() } else { izler.first().location().page() }
}

// İçindekilerde sayfa numarası: ana metinden önceki sayfalar (ön söz) romen rakamıyla (iii), sonrası 1, 2, 3.
#let sayfa-etiketi(yer) = numbering(if yer.page() < ana-metin-sayfasi() { "i" } else { "1" }, ..counter(page).at(yer))

// Editörlü kitapta bölüm başı: başlık (yıldızlı not), sağa yaslı yazarlar ve yazar dipnotları.
//   #bolum([Bölüm başlığı], aciklama: [Bu bölüm … tezinden üretilmiştir.], yazarlar: (
//     ("Ad SOYAD", [Prof. Dr., … Üniversitesi, … Fakültesi, … Bölümü. ORCID: 0000-0000-0000-0000]),
//   ))
// Künye (unvan, kurum, ORCID) her zaman dipnottadır; e-posta yazılmaz (Vizetek, 20.11.2026).
// Yazar dipnotları ** ve *** ile işaretlenir; gövde dipnotları her bölümde 1'den başlar.
// Açıklama başlığın içine konmaz (içindekilere ve yer imine taşınmasın); kitap.typ onu başlığın yanına basar.
// Başlık ve yazar adları <dizgi-bolum-bilgi> olarak bırakılır: bolum_pdfleri.py dosya adlarını buradan alır.
#let bolum-notu = state("dizgi-bolum-notu", none)
#let bolum(baslik, yazarlar: (), aciklama: none) = {
  [#metadata((baslik: duz-metin(baslik), yazarlar: yazarlar.map(y => y.first()))) <dizgi-bolum-bilgi>]
  bolum-notu.update(aciklama)
  heading(level: 1, baslik)
  bolum-notu.update(none)
  if yazarlar.len() > 0 {
    block(above: 1.2em, below: 2em, width: 100%, align(right, {
      set par(first-line-indent: 0pt, justify: false)
      for (i, (ad, bilgi)) in yazarlar.enumerate() {
        strong(ad)
        footnote(numbering: _ => "*" * (i + 2), bilgi)
        if i < yazarlar.len() - 1 { linebreak() }
      }
    }))
  }
  counter(footnote).update(0)
}

// Kısım (bölüm grubu) sayfası: sağ sayfada grup adı ve içindeki bölümlerin listesi; arkası boş kalır.
// Editör grupları "BÖLÜM 1: …" diye adlandırdıysa: #kisim("1", etiket: "BÖLÜM")[Temel İlkeler ve Fizyoloji]
#let kisim(no, baslik, etiket: "KISIM") = {
  [#metadata(none) <dizgi-kisim-oncesi>]  // boş sayfa tespiti için (kitap.typ → bos-sayfa-mi)
  pagebreak(to: "odd", weak: true)
  [#metadata((no: no, baslik: baslik, etiket: etiket)) <dizgi-kisim>]
  set par(first-line-indent: 0pt, justify: false)
  set text(hyphenate: false)
  v(42mm)
  align(center, text(size: 1.9em)[#etiket #no])
  v(6mm)
  align(center, text(size: 1.55em, baslik))
  v(12mm)
  context {
    let bu = here()
    let sonraki = query(selector(<dizgi-kisim>).after(bu)).filter(k => k.location() != bu)
    let secici = selector(heading.where(level: 1)).or(<dizgi-alt-grup>).after(bu)
    if sonraki.len() > 0 { secici = secici.before(sonraki.first().location()) }
    set text(size: 0.92em, style: "italic")
    for b in query(secici) {
      if b.func() == metadata {
        align(center, block(above: 0.9em, below: 0.5em, text(style: "normal", weight: "bold", b.value)))
      } else if b.numbering != none {
        align(center, block(below: 0.6em)[#counter(heading).at(b.location()).first(). #b.body])
      }
    }
  }
  // Arkası boş kalır: sonraki bölüm sağ sayfada açılır, araya numarasız boş sayfa girer.
}

// Bölüm grubunun içinde alt grup (ör. "Üst Gastrointestinal Sistem"): yalnız kısım sayfasında ve
// içindekilerde görünür, sayfa açmaz. İlk bölümünden hemen önce yazılır.
#let alt-grup(baslik) = [#metadata(baslik) <dizgi-alt-grup>]

// İçindekiler istenen yerde (profil `icindekiler: "elle"` ise, ör. Ön Söz'den sonra). Ön söz romen rakamlı. Kısım varsa
// gruplu yazılır: grup satırı kalın, alt grup italik, bölümler numarası ve sayfasıyla; tıklanır.
#let icindekiler-sayfasi(baslik: [İçindekiler]) = {
  heading(level: 1, numbering: none, outlined: false, baslik)
  set text(hyphenate: false)
  context if query(<dizgi-kisim>).len() == 0 { outline(title: none) } else {
    set par(first-line-indent: 0pt, justify: false)
    let satir(govde, yer, kalin: false) = block(above: 0.45em, below: 0.45em, link(yer, {
      set text(weight: if kalin { "bold" } else { "regular" })
      govde
      box(width: 1fr, repeat[#h(2pt).#h(2pt)])
      sayfa-etiketi(yer)
    }))
    for o in query(selector(heading.where(level: 1)).or(<dizgi-kisim>).or(<dizgi-alt-grup>).after(here())) {
      if o.func() == metadata and type(o.value) == dictionary {
        block(above: 1.3em, below: 0.5em, link(o.location(), strong[#o.value.etiket #o.value.no: #tr-buyuk(o.value.baslik)]))
      } else if o.func() == metadata {
        block(above: 0.8em, below: 0.4em, emph(o.value))
      } else if o.outlined {
        let no = if o.numbering != none [#counter(heading).at(o.location()).first(). ]
        satir([#no#o.body], o.location())
      }
    }
  }
}

// Kaynakça: asılı girinti, küçük punto. Her kaynak ayrı paragraf; DOI satır sonunda.
// Yeni sayfadan başlar: metin biter bitmez kaynakçaya geçilmez (kullanıcı kararı, 19.11.2026).
// Başı ve sonu <dizgi-kaynakca> izi bırakır: atıf bülteni bölümün kaynakça sayfalarını buradan alır.
#let kaynakca(baslik: [Kaynaklar], duzey: 2, punto: 0.82em, asili: 1.25cm, yeni-sayfa: true, govde) = {
  if yeni-sayfa { pagebreak(weak: true) }
  [#metadata("bas") <dizgi-kaynakca>]
  heading(level: duzey, numbering: none, outlined: false, baslik)
  set text(size: punto)
  set par(first-line-indent: 0pt, hanging-indent: asili, justify: true, spacing: 0.55em)
  show link: it => it.body
  govde
  [#metadata("son") <dizgi-kaynakca>]
}

// Tablo ya da şekil altındaki not ve kaynak ("Not.", "Kaynak:", "Kısaltmalar:"): 9 pt, girintisiz, iki yana yaslı.
#let sekil-notu(punto: 0.82em, govde) = block(above: 0.5em, below: 1.2em, width: 100%, {
  set text(size: punto)
  set par(first-line-indent: 0pt, justify: true, hanging-indent: 0pt)
  govde
})

// Şekil ya da tablo ve altındaki not birlikte: not hemen altta durur, ayrı sayfaya düşmez (Vizetek, 20.11.2026).
//   #notlu-sekil(figure(…))[#emph[Not.] … uyarlanmıştır.]
// duzenle.py şekilden sonra gelen not paragraflarını bu biçime getirir (figure'ın önündeki # düşer).
#let notlu-sekil(sekil, notu, punto: 0.82em) = {
  show figure: set block(below: 0.5em, sticky: true)
  sekil
  sekil-notu(punto: punto, notu)
}

// Bir tablonun puntosunu elle seçmek (şablon kendisi 10 → 9 → 8,5 pt dener): #tablo-puntosu(9pt)[#figure(…)]
#let tablo-elle = state("dizgi-tablo-punto", none)
#let tablo-puntosu(punto, govde) = {
  tablo-elle.update(punto)
  govde
  tablo-elle.update(none)
}

// Bilgi kutusu (ör. "Uygulamaya Köprü", "Özet"). Tek renk baskıda gri kalır.
#let kutu(baslik: none, renk: luma(40%), zemin: luma(95%), govde) = block(
  width: 100%, inset: (x: 10pt, y: 8pt), above: 1.2em, below: 1.2em, fill: zemin,
  stroke: (left: 2pt + renk), breakable: true, {
    set par(first-line-indent: 0pt)
    if baslik != none { block(below: 0.6em, strong(baslik)) }
    govde
  },
)

// Roman ve öyküde sahne arası.
#let sahne-arasi = block(above: 1.3em, below: 1.3em, width: 100%, align(center)[\* #h(0.6em) \* #h(0.6em) \*])
