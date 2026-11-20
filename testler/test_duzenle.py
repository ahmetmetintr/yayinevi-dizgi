"""duzenle.py ve duzenle_kurallari.py testleri (yayınevi düzeni). Çalıştırma: python -m unittest discover -s testler"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eklenti" / "skills" / "dizgi" / "araclar"))
from duzenle_kurallari import (baslik_duzelt, bloklar, kaynakca_cogunlugu, kunye_disarida,  # noqa: E402
                               kunye_duzelt, not_bagla, ozet_cikar, sahte_tablolar)

BAS = '#import "../sablon/ogeler.typ": *\n\n#bolum([Başlık], yazarlar: (\n  ("Ad SOYAD", [{bilgi}]),\n))\n\n'


def bolum(govde, bilgi="Dr., Örnek Üniversitesi. ORCID: 0000-0002-1825-0097"):
    return BAS.format(bilgi=bilgi) + govde


class Bloklar(unittest.TestCase):
    def test_dipnot_icindeki_bos_satir_paragrafi_bolmez(self):
        m = "Birinci paragraf.#footnote[Not bir.\n\nNot iki.] Devamı.\n\nİkinci paragraf.\n"
        self.assertEqual([t for _, _, t in bloklar(m)], ["paragraf", "paragraf"])

    def test_sekil_cagrisi_tek_kod_blogu(self):
        m = "#figure(caption: [Tablo (Ad (2026) ile], table(columns: 1, [a\n\nb]))\n\nMetin.\n"
        self.assertEqual([t for _, _, t in bloklar(m)], ["kod", "paragraf"])


class Ozet(unittest.TestCase):
    def test_ozet_ve_anahtar_kelimeler_cikar(self):
        m = bolum("== ÖZET\n\nÖzet paragrafı.\n\nAnahtar Kelimeler: a, b\n\n== GİRİŞ\n\nMetin.\n")
        yeni, deg, uyari = ozet_cikar(m)
        self.assertNotIn("ÖZET", yeni)
        self.assertNotIn("Anahtar", yeni)
        self.assertIn("== GİRİŞ\n\nMetin.", yeni)
        self.assertEqual((len(deg), uyari), (1, []))

    def test_etiket_basligi_ve_ingilizce_ozet(self):
        m = bolum("== Özet\n\nBir.\n\nİki.\n\n=== Anahtar kelimeler\n\nx, y.\n\n#strong[Abstract]\n\nText.\n\n"
                  "#strong[Keywords:] x, y\n\n== Giriş\n\nMetin.\n")
        yeni, deg, _ = ozet_cikar(m)
        self.assertTrue(yeni.endswith("))\n\n== Giriş\n\nMetin.\n"), yeni)

    def test_duzensiz_ozete_dokunmaz(self):
        m = bolum("ÖZET\n\n== Wilms Tümörü\n\nMetin.\n\nAnahtar kelimeler: a\n")
        yeni, deg, uyari = ozet_cikar(m)
        self.assertEqual((yeni, deg, len(uyari)), (m, [], 1))

    def test_bolum_icindeki_ozet_basligina_dokunmaz(self):
        m = bolum("== Giriş\n\nMetin.\n\n=== Özet\n\nAra özet.\n")
        self.assertEqual(ozet_cikar(m)[0], m)


class Kunye(unittest.TestCase):
    def test_eposta_silinir(self):
        ornekler = {
            "Op. Dr., Hastane. ORCID: 0000-0001-5109-3700, ad\\@ornek.com": "Op. Dr., Hastane. ORCID: 0000-0001-5109-3700",
            "Prof. Dr. Üniversite. ORCID: 0000-0003-1415-9269 ad\\_soyad\\@ornek.com.tr": "Prof. Dr. Üniversite. ORCID: 0000-0003-1415-9269",
            "Doç. Dr. ORCID: 0000-0001-2345-678X Email: ad.80\\@ornek.org": "Doç. Dr. ORCID: 0000-0001-2345-678X",
            "Dr., Kurum (e-posta: a\\@b.edu.tr), Ankara": "Dr., Kurum, Ankara",
        }
        for bilgi, beklenen in ornekler.items():
            self.assertIn(f"[{beklenen}]", kunye_duzelt(bolum("", bilgi))[0], bilgi)

    def test_orcid_standart_yazilir(self):
        ornekler = ['Orcid id:#link("https://orcid.org/0000-0002-1825-0097")[0000-0002-1825-0097]',
                    "ORCID: https://orcid.org/0000-0002-1825-0097", "orcid no 0000-0002-1825-0097",
                    "ORCİD ID: 0000-0002-1825-0097", "https:/\\/orcid.org/0000-0002-1825-0097"]
        for yazim in ornekler:
            yeni, deg, _ = kunye_duzelt(bolum("", f"Dr., Kurum. {yazim}"))
            self.assertIn("[Dr., Kurum. ORCID: 0000-0002-1825-0097]", yeni, yazim)
        self.assertEqual(kunye_duzelt(bolum(""))[1], [])  # zaten standart

    def test_dipnottaki_kunye_ve_metindeki_kunye(self):
        m = bolum("Metin.#footnote[Dr., Kurum. E-posta: a\\@b.com. ORCID: 0000-0002-1825-0097]\n\nYazar e-mail:x\\@y.com\n")
        yeni = kunye_duzelt(m)[0]
        self.assertIn("#footnote[Dr., Kurum. ORCID: 0000-0002-1825-0097]", yeni)
        self.assertEqual([s for s, _ in kunye_disarida(yeni)], [9])  # metin içindeki künyeye dokunmaz, bildirir


class Baslik(unittest.TestCase):
    def test_giris_sonuc_kaynaklar(self):
        m = "== GİRİŞ\n\n== \\1. GİRİŞ\n\n=== SONUÇ\n\n== Giriş\n\n== FETAL GİRİŞİM\n\n#kaynakca(baslik: [12. KAYNAKLAR])[x]\n"
        yeni, deg, uyari = baslik_duzelt(m, "Kaynaklar")
        self.assertEqual(yeni, "== Giriş\n\n== \\1. Giriş\n\n=== Sonuç\n\n== Giriş\n\n== FETAL GİRİŞİM\n\n"
                               "#kaynakca(baslik: [Kaynaklar])[x]\n")
        self.assertEqual([u[1] for u in uyari], ["tümü büyük harf ara başlık: FETAL GİRİŞİM"])

    def test_kaynakca_adi_cogunluk(self):
        metinler = ["#kaynakca(baslik: [Kaynakça])[x]", "#kaynakca(baslik: [KAYNAKÇA])[x]", "#kaynakca[x]"]
        self.assertEqual(kaynakca_cogunlugu(metinler), "Kaynakça")
        self.assertEqual(kaynakca_cogunlugu(metinler[:1] + ["#kaynakca[x]"]), "Kaynaklar")  # eşitlik
        yeni = baslik_duzelt("#kaynakca(baslik: [REFERANSLAR])[x]\n\n== Kaynaklar\n", "Kaynakça")[0]
        self.assertEqual(yeni, "#kaynakca(baslik: [Kaynakça])[x]\n\n== Kaynakça\n")


class Notlar(unittest.TestCase):
    def test_not_sekle_baglanir(self):
        sekil = '#figure(numbering: none, caption: [#strong[Tablo 1.] Ad (Yazar (2026) ile], kind: table,\n\n  table(columns: 1, [a]))'
        m = f"Metin.\n\n{sekil}\n\n#emph[Not.] Uyarlanmıştır.\n\nKısaltmalar: ÜSYE, üst solunum yolu.\n\nSonraki metin.\n"
        yeni, deg, _ = not_bagla(m)
        self.assertEqual(yeni, f"Metin.\n\n#notlu-sekil({sekil[1:]})[#emph[Not.] Uyarlanmıştır.\n\n"
                               "Kısaltmalar: ÜSYE, üst solunum yolu.]\n\nSonraki metin.\n")
        self.assertEqual(len(deg), 1)

    def test_not_olmayan_paragrafa_dokunmaz(self):
        m = "#figure(table(columns: 1, [a]))\n\nKaynaklar arasında en eskisi budur.\n\nNotlar\n"
        self.assertEqual(not_bagla(m)[0], m)


class SahteTablo(unittest.TestCase):
    def test_tablosuz_tablo_yazisi(self):
        m = "#strong[Tablo 1.] Oranlar \\ Grup 1 8 37.5%\n\nMetin.\n\n#strong[Tablo 2.] Gerçek\n\n#figure(table(columns: 1, [a]))\n"
        self.assertEqual([s for s, _ in sahte_tablolar(m)], [1])


if __name__ == "__main__":
    unittest.main()
