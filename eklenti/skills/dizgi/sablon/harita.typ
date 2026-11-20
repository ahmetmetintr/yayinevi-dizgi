// harita.typ — Kitabın bölüm haritası (dizgi skill'i); kitap.typ belgenin sonuna <dizgi-harita> olarak koyar.
// bolum_pdfleri.py okur (jenerik, bölüm PDF'leri ve atıf bülteni):
//   typst eval 'query(<dizgi-harita>).first().value' --in kitap.typ   (Typst 0.13: typst query … --field value --one)
// Sayfalar PDF'in fiziksel sayfasıdır (1'den). Bölüm: numaralı 1. düzey başlık ya da #bolum ile açılan başlık.
// Bölüm, kendisinden sonraki ilk bölüm, kısım ya da numarasız başlık izinden önceki sayfada biter
// (araya giren boş sayfa bölüme katılmaz). Jenerik: ana metinden (sayfa 1) önceki bütün sayfalar.

#import "ogeler.typ": ana-metin-sayfasi, duz-metin

// Başlığın hemen önündeki #bolum bilgisi (yoksa none).
#let bolum-bilgisi(baslik, onceki) = {
  let secici = selector(<dizgi-bolum-bilgi>).before(baslik.location())
  if onceki != none { secici = secici.after(onceki.location()) }
  let bulunan = query(secici)
  if bulunan.len() > 0 { bulunan.last().value } else { none }
}

// Bölümün bittiği sayfa: başlıktan sonraki ilk bölüm-öncesi ya da kısım-öncesi izi (bölümün kendi izi hariç).
#let bolum-sonu(baslik, son-sayfa) = {
  let izler = query(selector(<dizgi-bolum-oncesi>).or(<dizgi-kisim-oncesi>).after(baslik.location()))
    .filter(i => i.value != baslik.location())
  if izler.len() > 0 { (sayfa: izler.first().location().page(), iz: izler.first()) } else { (sayfa: son-sayfa, iz: none) }
}

// Bölümün kaynakçaları: <dizgi-kaynakca> "bas" ve "son" izleri çift çift.
#let kaynakca-araliklari(baslik, sonu) = {
  let secici = selector(<dizgi-kaynakca>).after(baslik.location())
  if sonu.iz != none { secici = secici.before(sonu.iz.location()) }
  let araliklar = ()
  let bas = none
  for iz in query(secici) {
    if iz.value == "bas" { bas = iz.location().page() } else if bas != none {
      araliklar.push((ilk: bas, son: iz.location().page()))
      bas = none
    }
  }
  araliklar
}

#let kitap-haritasi(kitap-adi, kitap-yazari) = {
  let son-sayfa = here().page()
  let ana = ana-metin-sayfasi()
  // Ana metindeki 1. düzey başlıklar; numaralı ya da #bolum ile açılanlar varsa yalnız onlar (ek, dizin dışarıda).
  let adaylar = ()
  let onceki = none
  for b in query(heading.where(level: 1)) {
    let bilgi = bolum-bilgisi(b, onceki)
    onceki = b
    if b.location().page() >= ana { adaylar.push((b, bilgi)) }
  }
  let secilen = adaylar.filter(((b, bilgi)) => b.numbering != none or bilgi != none)
  if secilen.len() == 0 { secilen = adaylar }
  let bolumler = ()
  for (b, bilgi) in secilen {
    let ilk = b.location().page()
    let sonu = bolum-sonu(b, son-sayfa)
    bolumler.push((
      no: bolumler.len() + 1,
      numara: if b.numbering != none { counter(heading).at(b.location()).first() } else { none },
      baslik: if bilgi != none { bilgi.baslik } else { duz-metin(b.body) },
      yazarlar: if bilgi != none { bilgi.yazarlar } else { () },
      ilk: ilk,
      son: calc.max(ilk, sonu.sayfa),
      kaynakca: kaynakca-araliklari(b, sonu),
    ))
  }
  (
    surum: 1,
    baslik: duz-metin(kitap-adi),
    yazar: duz-metin(kitap-yazari),
    sayfa-sayisi: son-sayfa,
    ana-metin: ana,
    jenerik: (ilk: 1, son: calc.max(0, ana - 1)),
    bolumler: bolumler,
  )
}
