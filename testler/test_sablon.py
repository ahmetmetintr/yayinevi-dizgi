"""Şablon testleri (Vizetek dizgi istekleri, 20.11.2026): örnek kitapları derleyip PDF'e bakar.
typst ve pymupdf ister; yoksa atlanır."""
import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
GEREKLI = importlib.util.find_spec("pymupdf") and shutil.which("typst")


def derle(ad, klasor):
    pdf = Path(klasor) / f"{ad}.pdf"
    subprocess.run(["typst", "compile", "--root", str(KOK), str(KOK / f"testler/ornek-vizetek/{ad}.typ"), str(pdf)],
                   check=True, capture_output=True)
    import pymupdf
    return pymupdf.open(pdf)


def satirlar(sayfa):
    return [s.strip() for s in sayfa.get_text().splitlines() if s.strip()]


@unittest.skipUnless(GEREKLI, "pymupdf ve typst gerekir")
class EditorluKitap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.klasor = tempfile.TemporaryDirectory()
        cls.pdf = derle("editorlu", cls.klasor.name)

    @classmethod
    def tearDownClass(cls):
        cls.klasor.cleanup()

    def test_bolum_etiketi_basligin_ustunde(self):
        s = satirlar(self.pdf[6])
        self.assertEqual(s[:2], ["1. Bölüm", "ÖĞRETMEN EĞİTİMİNDE DİJİTAL DÖNÜŞÜM*"])

    def test_sayfa_numarasi_icindekilerden_sonra_birden(self):
        self.assertEqual(satirlar(self.pdf[6])[-1], "1")          # 1. bölümün ilk sayfası
        for p in range(6):                                        # ön sayfalarda numara yok
            self.assertFalse(satirlar(self.pdf[p]) and satirlar(self.pdf[p])[-1].isdigit(), p + 1)
        self.assertIn("iii", self.pdf[4].get_text())              # içindekilerde ön söz romen rakamıyla

    def test_ust_bilgi_birinci_bolumun_ilk_sayfasindan_sonra(self):
        ust = "EĞİTİMDE GÜNCEL YAKLAŞIMLAR"
        self.assertEqual([p + 1 for p in range(len(self.pdf)) if satirlar(self.pdf[p])[:1] == [ust]],
                         [8, 9, 10, 12, 13])                      # 7 ve 11: bölüm açılışı

    def test_ara_baslik_sola_yasli_ve_tumu_buyuk_degil(self):
        sayfa = self.pdf[6]
        giris = next(b for b in sayfa.get_text("dict")["blocks"] for l in b.get("lines", [])
                     for s in l["spans"] if s["text"].strip() == "Giriş")
        self.assertLess(giris["bbox"][0] - sayfa.rect.x0, 60)  # sol kenar boşluğunda (20 mm ≈ 57 pt)


@unittest.skipUnless(GEREKLI, "pymupdf ve typst gerekir")
class KunyesiBosYazar(unittest.TestCase):
    """Künyesi boş yazara dipnot konmaz; yıldızlar boşluksuz (**, ***) yalnız dipnotu olanlara."""

    def test_bos_kunye_dipnotsuz(self):
        with tempfile.TemporaryDirectory() as klasor:
            pdf = derle("bos-kunye", klasor)
            sayfa = next(p for p in pdf if "Birinci YAZAR" in p.get_text())  # başlık Türkçe büyük harfle basılır
            metin = " ".join(satirlar(sayfa))
            dipnotlar = [s for s in satirlar(sayfa) if s.startswith("*")]
        self.assertIn("Birinci YAZAR**", metin)
        self.assertIn("Üçüncü YAZAR***", metin)
        self.assertNotIn("İkinci YAZAR*", metin)
        self.assertNotIn("Dördüncü YAZAR*", metin)
        self.assertNotIn("****", metin)
        self.assertEqual(dipnotlar, ["**Örnek Üniversitesi. ORCID: 0000-0002-1825-0097", "***Başka Üniversite"])


@unittest.skipUnless(GEREKLI, "pymupdf ve typst gerekir")
class Tablolar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.klasor = tempfile.TemporaryDirectory()
        cls.pdf = derle("tablolar", cls.klasor.name)

    @classmethod
    def tearDownClass(cls):
        cls.klasor.cleanup()

    def bul(self, yazi):
        return [(p, s) for p, sayfa in enumerate(self.pdf) for b in sayfa.get_text("dict")["blocks"]
                for l in b.get("lines", []) for s in l["spans"] if s["text"].startswith(yazi)]

    def test_sigan_tablo_bolunmez_basligi_ortali(self):
        (p, _), = self.bul("Tablo 1.")
        satir_sayfalari = {q for q, _ in self.bul("Satır ")[:15]}
        self.assertEqual(satir_sayfalari, {p})
        satir = next(l for b in self.pdf[p].get_text("dict")["blocks"] for l in b.get("lines", [])
                     if l["spans"] and l["spans"][0]["text"].startswith("Tablo 1."))
        self.assertAlmostEqual((satir["bbox"][0] + satir["bbox"][2]) / 2, self.pdf[p].rect.width / 2, delta=3)

    def test_tablo_10_punto_sigmayan_kuculur(self):
        self.assertEqual(round(self.bul("Madde 0")[0][1]["size"], 1), 10.0)
        self.assertEqual(round(self.bul("Değer 0")[0][1]["size"], 1), 8.5)

    def test_bolunen_tablonun_basligi_ilk_satirla_ayni_sayfada(self):
        (p, _), = self.bul("Tablo 3.")
        self.assertIn(p, {q for q, s in self.bul("Satır 0")})

    def test_not_9_punto_baglanti_siyah_alti_cizgisiz(self):
        (p, notu), = self.bul("Not.")
        self.assertEqual(round(notu["size"], 1), 9.0)
        adres = [s for q, s in self.bul(" Değerler") if "doi.org" in s["text"]][0]
        self.assertEqual(adres["color"], 0)
        cizgiler = [d for d in self.pdf[p].get_drawings()
                    if d["rect"].height < 1.5 and abs(d["rect"].y0 - adres["bbox"][3]) < 4]
        self.assertEqual(cizgiler, [])


if __name__ == "__main__":
    unittest.main()
