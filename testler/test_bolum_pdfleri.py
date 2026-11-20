"""bolum_pdfleri.py testleri (jenerik, bölüm PDF'leri, atıf bülteni). Uçtan uca test typst ve pymupdf ister."""
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
ARACLAR = KOK / "eklenti" / "skills" / "dizgi" / "araclar"
sys.path.insert(0, str(ARACLAR))
from bolum_pdfleri import benzersiz, bulten_plani, denetle, dosya_adi, yazar_listesi  # noqa: E402

HARITA = {"baslik": "Kitap", "yazar": "Editör", "sayfa-sayisi": 12, "ana-metin": 5, "jenerik": {"ilk": 1, "son": 4},
          "bolumler": [
              {"no": 1, "numara": 1, "baslik": "Bir", "yazarlar": ["A B"], "ilk": 5, "son": 8,
               "kaynakca": [{"ilk": 8, "son": 8}]},
              {"no": 2, "numara": 2, "baslik": "İki", "yazarlar": [], "ilk": 9, "son": 12, "kaynakca": []}]}


class Adlar(unittest.TestCase):
    def test_yazar_listesi(self):
        self.assertEqual(yazar_listesi(["A"]), "A")
        self.assertEqual(yazar_listesi(["A", "B"]), "A ve B")
        self.assertEqual(yazar_listesi(["A", "B", "C"]), "A, B ve C")

    def test_dosya_adi_vizetek_ornegi(self):
        self.assertEqual(dosya_adi(["Ayşe YILMAZ"], "Gastroşizis: Tanı/Tedavi?"), "Ayşe YILMAZ, Gastroşizis Tanı Tedavi")
        self.assertEqual(dosya_adi([], "Başlık."), "Başlık")
        uzun = dosya_adi(["A"], "x" * 300)
        self.assertTrue(len(uzun) <= 150 and uzun.endswith("…"))

    def test_benzersiz(self):
        self.assertEqual(benzersiz(["a", "b", "a"]), ["a", "b", "a (2)"])


class Plan(unittest.TestCase):
    def test_bulten_jenerik_ilk_sayfa_ve_kaynakca(self):
        plan = bulten_plani(HARITA, [1, 2, 3])
        self.assertEqual([s for s, _ in plan], [1, 2, 3, 5, 8, 9])
        self.assertEqual([y for _, y in plan if y], [(1, "Jenerik"), (1, "1. Bölüm: Bir"), (2, "Kaynaklar"),
                                                     (1, "2. Bölüm: İki")])

    def test_denetim(self):
        hatalar, uyarilar = denetle(HARITA, 12)
        self.assertEqual(hatalar, [])
        self.assertEqual(len(uyarilar), 2)  # 2. bölümde yazar ve kaynakça yok
        self.assertIn("son derlemesi değil", denetle(HARITA, 13)[0][0])


@unittest.skipUnless(importlib.util.find_spec("pymupdf") and shutil.which("typst"), "pymupdf ve typst gerekir")
class UctanUca(unittest.TestCase):
    def test_vizetek_editorlu_ornek(self):
        import pymupdf
        kitap = KOK / "testler/ornek-vizetek/editorlu.typ"
        with tempfile.TemporaryDirectory() as k:
            pdf, cikti = Path(k) / "kitap.pdf", Path(k) / "teslim"
            subprocess.run(["typst", "compile", "--root", str(KOK), str(kitap), str(pdf)], check=True, capture_output=True)
            sonuc = subprocess.run([sys.executable, str(ARACLAR / "bolum_pdfleri.py"), str(kitap), str(pdf),
                                    "--root", str(KOK), "--cikti", str(cikti)], capture_output=True, text=True)
            self.assertEqual(sonuc.returncode, 0, sonuc.stderr)
            bolumler = sorted(p.name for p in (cikti / "bolumler").iterdir())
            self.assertEqual(bolumler, ["Ayşe YILMAZ ve Mehmet KAYA, Öğretmen Eğitiminde Dijital Dönüşüm.pdf",
                                        "Zeynep ARSLAN, Okul Öncesinde Oyun Temelli Öğrenme.pdf"])
            jenerik = pymupdf.open(cikti / "Eğitimde Güncel Yaklaşımlar, Jenerik.pdf")
            self.assertIn("İÇİNDEKİLER", jenerik[-1].get_text())  # boş sayfalar atıldı, içindekiler son sayfa
            b1 = pymupdf.open(cikti / "bolumler" / bolumler[0])
            self.assertIn("1. Bölüm", b1[0].get_text())
            self.assertIn("Kaynaklar", b1[-1].get_text())
            bulten = pymupdf.open(cikti / "Eğitimde Güncel Yaklaşımlar, Atıf bülteni.pdf")
            self.assertEqual(len(bulten), len(jenerik) + 4)  # her bölüm: ilk sayfa + kaynakça sayfası
            from bolum_pdfleri import harita_oku
            harita = harita_oku(kitap, KOK)
            self.assertEqual([(b["ilk"], b["son"]) for b in harita["bolumler"]], [(7, 10), (11, 13)])


if __name__ == "__main__":
    unittest.main()
