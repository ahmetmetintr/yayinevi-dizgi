"""imla_denetle.py testleri. Çalıştırma: python -m unittest discover -s testler"""
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eklenti" / "skills" / "imla" / "araclar"))
from imla_denetle import benzerlik_bulgulari, denetle, duz_metin, isaret_dosyasi, kural_bulgulari, sozluk  # noqa: E402

KURALLAR = sozluk()


def bul(metin):
    return [(e, o, g) for _, e, o, _, g in kural_bulgulari(metin, KURALLAR)]


class Kurallar(unittest.TestCase):
    def test_sik_yanlislar_ve_harf_duzeni(self):
        self.assertIn(("herşey", "her şey", "kesin"), bul("Bu herşey demek."))
        self.assertIn(("Barsakta", "Bağırsakta", "kesin"), bul("Barsakta tıkanıklık."))
        self.assertIn(("bir çok", "birçok", "kesin"), bul("bir çok hasta"))
        self.assertEqual(bul("diabetes mellitus ve birçok hasta"), [])   # Latince kalıp ve doğru yazım

    def test_kesme_isareti(self):
        self.assertIn(("2de", "2'de", "kesin"), bul("Tip 2de görülür."))
        self.assertIn(("%75inde", "%75'inde", "kesin"), bul("olguların %75inde"))
        self.assertIn(("MRda", "MR'da", "kesin"), bul("MRda kitle"))
        self.assertEqual(bul("Evre 4a ve Tip 3b, 1990'lı yıllar, MR'de"), [])   # alt tip harfi ek değildir

    def test_baglaclar(self):
        self.assertIn(("ve ve", "ve", "kesin"), bul("bulantı ve ve kusma"))
        self.assertEqual(bul("Türkiye'de de görülür."), [])                       # ek + bağlaç doğrudur
        self.assertIn(("veMcMahon", "ve McMahon", "kesin"), bul("(Ochoa veMcMahon, 2024)"))
        self.assertIn(("gelirmi", "gelir mi", "olası"), bul("Hasta gelirmi?"))
        self.assertIn(("hİpertrofik", "hipertrofik", "kesin"), bul("A-hİpertrofik pİlor stenozu"))
        self.assertEqual([x for x in bul("McMahon, IgG, pH ve HİRSCHSPRUNG") if "İ" in x[0]], [])


class Benzerlik(unittest.TestCase):
    def test_tek_gecen_yazim_hatasi(self):
        sayim = Counter({"perioperatif": 49, "periaoperatif": 1, "steroid": 12, "streoid": 1, "ugulanması": 1,
                         "uygulanması": 30, "olmadığı": 40, "olamadığı": 1})
        b = benzerlik_bulgulari(sayim, frozenset())
        self.assertEqual(b["periaoperatif"][0], "perioperatif")             # ünlü yığılması
        self.assertEqual(b["streoid"][0], "steroid")                         # yer değiştirme
        self.assertEqual(b["ugulanması"][0], "uygulanması")                  # eksik y
        self.assertNotIn("olamadığı", b)                                      # geçerli çekim

    def test_gecerli_ciftler_yakalanmaz(self):
        sayim = Counter({"semptomatik": 47, "asemptomatik": 54, "haftada": 37, "hastada": 53,
                         "bulgularıdır": 2, "bulgulardır": 9, "thomson": 6, "thompson": 1})
        buyuk = Counter({"thomson": 6, "thompson": 1})
        self.assertEqual(benzerlik_bulgulari(sayim, frozenset(), buyuk), {})

    def test_sozcuk_olamayacak_dizi_karsilastirilmaz(self):
        uzun = "abcçdefgğh" * 7                                           # 70 harf: sözcük değil
        kisa = uzun[:60]
        yer = lambda s: s[:20] + s[21] + s[20] + s[22:]                    # yer değiştirmiş harf
        self.assertEqual(benzerlik_bulgulari(Counter({uzun: 20, yer(uzun): 1}), frozenset()), {})
        self.assertIn(yer(kisa), benzerlik_bulgulari(Counter({kisa: 20, yer(kisa): 1}), frozenset()))
        with tempfile.TemporaryDirectory() as d:                         # 300 bin harflik dizi: anında biter
            yol = Path(d) / "dizi.typ"
            yol.write_text("Satır.\n" + "acgt" * 75_000 + "\n", encoding="utf-8")
            self.assertEqual(denetle([str(yol)]), [])

    def test_iki_yazim(self):
        b = benzerlik_bulgulari(Counter({"adolesan": 13, "adölesan": 14}), frozenset())
        self.assertIn("iki yazımı", b["adolesan"][1])


class Dosya(unittest.TestCase):
    def test_kaynakca_ve_kod_taranmaz(self):
        t = duz_metin('#figure(image("../yol/herşey.png"))\nMetin.\n#kaynakca(baslik: [K])[\nBarsak, A. (2020).\n]\n')
        self.assertNotIn("herşey", t)
        self.assertNotIn("Barsak", t)
        self.assertEqual(t.count("\n"), 5)                                   # satır numaraları korunur

    def test_denetle_istisna_ve_isaret(self):
        with tempfile.TemporaryDirectory() as d:
            yol = Path(d) / "bolum-01.typ"
            yol.write_text("Satır bir.\nBurada herşey ve yada var.\n", encoding="utf-8")
            b = denetle([str(yol)], istisna=frozenset({"yada"}))
            self.assertEqual([(x[1], x[2]) for x in b], [(2, "herşey")])
            self.assertIn('#let imla-deseni = "(?:herşey)"', isaret_dosyasi(b))
            self.assertIn("#let imla-deseni = none", isaret_dosyasi([]))


if __name__ == "__main__":
    unittest.main()
