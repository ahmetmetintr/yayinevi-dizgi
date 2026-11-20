"""tablo_kur.py testleri: boşlukla dizilmiş tablonun Typst taslağı (örnek, eski .doc dosyalarındaki biçimi taklit eder)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eklenti" / "skills" / "dizgi" / "araclar"))
from tablo_kur import hucreler, tablo_bul, typst_taslagi  # noqa: E402

SATIRLAR = [
    "Tablo 2. Örnek olgular",
    "İlk yazar (*)             Yıl        Histoloji                   Evre",
    "Yılmaz(18)         1987       Skuamöz hücreli    T4N0M0",
    "karsinom ",
    "Kaya(19)              1989       Adenokarsinom     T2N0M0",
    "* Kaynaklar",
    "Sonraki Ara Başlık",
    "Bu paragraf tablodan sonra gelen olağan metindir; sütun sınırı taşımaz ve devam satırı sayılmayacak kadar uzundur.",
]


class TabloKur(unittest.TestCase):
    def test_hucreler_iki_bosluk_ya_da_sekme(self):
        self.assertEqual(hucreler("Grup 1 (1964–1969)    8\t37.5%  "), ["Grup 1 (1964–1969)", "8", "37.5%"])

    def test_devam_satiri_ve_tablo_notu(self):
        satirlar, uyarilar, son = tablo_bul(SATIRLAR, 0)
        self.assertEqual(satirlar[1], ["Yılmaz(18)", "1987", "Skuamöz hücreli karsinom", "T4N0M0"])
        self.assertEqual((len(satirlar), son), (3, 4))  # "* Kaynaklar" ve ara başlık tabloya girmez
        self.assertIn("tablo notu olabilir", uyarilar[-1])

    def test_taslak_kacis_ve_denetle_isareti(self):
        taslak = typst_taslagi(2, "Ad", [["İlk yazar (*)", "Yıl"], ["A"]])
        self.assertIn("table.header([İlk yazar (\\*)], [Yıl]),", taslak)
        self.assertIn("[A], [],  // DENETLE: 1 hücre, 2 sütun", taslak)


if __name__ == "__main__":
    unittest.main()
