"""kaynakca_denetle.py ve bolum_denetle.py testleri. Çalıştırma: python -m unittest discover -s testler"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eklenti" / "skills" / "dizgi" / "araclar"))
from bolum_denetle import bolum_cagrilari, orcid_gecerli  # noqa: E402
from kaynakca_denetle import atiflar, bolumler, denetle, sira_anahtari  # noqa: E402

METIN = """
= Bölüm
Oyun önemlidir (Arslan, 2022; Çelik ve Kaya, 2021). Öztürk (2020) bunu gösterdi; Işık vd. (2019) de.
#kaynakca[
  Arslan, Z. (2022). _Oyun_. Örnek Yayıncılık. https://doi.org/10.1234/a

  Çelik, A., & Kaya, B. (2021). Başlık. _Dergi_, _2_(1), 1–5. https://doi.org/10.1234/b

  Işık, C., Ak, D., & Su, E. (2019). Başlık. 10.1234/c

  Öztürk, F. (2020). Başlık.

  Zeren, G. (2018). Hiç atıf yapılmamış kaynak. https://doi.org/10.1234/z
]
"""


class Kaynakca(unittest.TestCase):
    def test_turkce_alfabe(self):
        sirali = sorted(["Zeren", "Çelik", "Işık", "İnce", "Cem", "Öztürk", "Oral", "Şahin", "Sarı"], key=sira_anahtari)
        self.assertEqual(sirali, ["Cem", "Çelik", "Işık", "İnce", "Oral", "Öztürk", "Sarı", "Şahin", "Zeren"])

    def test_atiflar(self):
        govde = bolumler(METIN)[0][0]
        self.assertEqual(atiflar(govde), {("arslan", "2022"), ("çelik", "2021"), ("öztürk", "2020"), ("ışık", "2019")})

    def test_sorunlar(self):
        govde, kaynaklar = bolumler(METIN)[0]
        self.assertEqual(len(kaynaklar), 5)
        sorunlar = {(no, ne.split(" (")[0].split(":")[0]) for no, ne, _ in denetle(govde, kaynaklar)[2]}
        self.assertIn((3, "DOI bağlantı biçiminde değil"), sorunlar)
        self.assertIn((4, "DOI yok"), sorunlar)
        self.assertIn((5, "kaynakçada var, metinde atıf bulunamadı"), sorunlar)
        self.assertNotIn((1, "DOI yok"), sorunlar)
        self.assertFalse(any("alfabe" in ne for _, ne in sorunlar))

    def test_atif_var_kaynak_yok_ve_sira(self):
        metin = "Bkz. (Yok, 2001).\n#kaynakca[\n  Zeren, A. (2000). X. https://doi.org/10.1/x\n\n  Arslan, B. (2001). Y. https://doi.org/10.1/y\n]"
        govde, kaynaklar = bolumler(metin)[0]
        nedenler = [ne for _, ne, _ in denetle(govde, kaynaklar)[2]]
        self.assertIn("metinde atıf var, kaynakçada yok", nedenler)
        self.assertTrue(any(ne.startswith("alfabe sırası") for ne in nedenler))

    def test_her_kaynakca_ayri_bolum(self):
        iki = METIN + "\n= İkinci\nMetin (Ak, 2020).\n#kaynakca[\n  Ak, B. (2020). Z. https://doi.org/10.1/q\n]\n"
        self.assertEqual([len(k) for _, k in bolumler(iki)], [5, 1])

    def test_basligi_ayarli_kaynakca(self):
        # Klinik Çocuk Cerrahisi (19.11.2026): #kaynakca(baslik: [KAYNAKLAR], duzey: 3)[…] da okunmalı
        metin = "Metin (Ak, 2020).\n#kaynakca(baslik: [KAYNAKLAR], duzey: 3)[\n  Ak, B. (2020). Z. https://doi.org/10.1/q\n]\n"
        self.assertEqual([len(k) for _, k in bolumler(metin)], [1])

    def test_baslik_altindaki_kaynakca(self):
        metin = "Metin (Ak, 2020).\n\n= Kaynakça\n\nAk, B. (2020). Z. https://doi.org/10.1/q\n"
        self.assertEqual(len(bolumler(metin)[0][1]), 1)


class Bolum(unittest.TestCase):
    def test_orcid_saglama(self):
        self.assertTrue(orcid_gecerli("0000-0002-1825-0097"))
        self.assertTrue(orcid_gecerli("0000-0001-5109-3700"))
        self.assertTrue(orcid_gecerli("0000-0002-1694-233X"))
        self.assertFalse(orcid_gecerli("0000-0001-5109-3701"))
        self.assertFalse(orcid_gecerli("0000-0001-5109"))

    def test_bolum_cagrilari(self):
        metin = '#bolum([Başlık (alt)], yazarlar: (("Ad SOYAD", [Prof. Dr., X Üniversitesi. ORCID: 0000-0002-1825-0097]),))'
        self.assertEqual(bolum_cagrilari(metin), [("Başlık (alt)", [("Ad SOYAD", "Prof. Dr., X Üniversitesi. ORCID: 0000-0002-1825-0097")])])


if __name__ == "__main__":
    unittest.main()
