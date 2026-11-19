"""tashih_oku.py ve tashih_uygula.py testleri. Çalıştırma: python -m unittest discover -s testler"""
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ARACLAR = Path(__file__).resolve().parents[1] / "eklenti" / "skills" / "tashih" / "araclar"
sys.path.insert(0, str(ARACLAR))
from tashih_oku import ayristir, docx_oku  # noqa: E402
from tashih_uygula import normallestir, planla, uygula  # noqa: E402

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def madde(eski, yeni, **ek):
    return dict({"islem": "Değiştir", "eski": eski, "yeni": yeni}, **ek)


def uygula_hepsi(maddeler, metin):
    plan = planla(maddeler, metin)
    return uygula(metin, plan), [d for _, d, _ in plan]


class Ayristir(unittest.TestCase):
    def test_kanonik_bicimler(self):
        self.assertEqual(ayristir("Değiştir: «E-mail» → «E-posta»\nTDK karşılığı.")["yeni"], "E-posta")
        self.assertEqual(ayristir("Değiştir: «E-mail» → «E-posta»\nTDK karşılığı.")["aciklama"], "TDK karşılığı.")
        self.assertEqual(ayristir('"kaygı" yerine "korku"')["islem"], "Değiştir")
        self.assertEqual(ayristir("Sil: «çok»")["eski"], "çok")
        self.assertEqual(ayristir("Ekle: «,»")["yeni"], ",")
        self.assertEqual(ayristir("Biçim: italik olsun")["islem"], "Biçim")

    def test_yorumsuz_isaretler(self):
        self.assertEqual(ayristir("", "StrikeOut", "fazla")["islem"], "Sil")
        self.assertEqual(ayristir("", "StrikeOut", "fazla")["eski"], "fazla")
        self.assertEqual(ayristir("", "Highlight")["islem"], "Vurgu")
        self.assertEqual(ayristir("Burada bir sorun var")["islem"], "Not")


class Uygula(unittest.TestCase):
    def test_tipografik_farklar_eslesir(self):
        metin = "Prof.~Dr.~Ayşe’nin “kaygı” dediği 1990–2000 arası…\n"
        sonuc, durum = uygula_hepsi([madde("Prof. Dr. Ayşe'nin \"kaygı\"", "Prof. Dr. Ayşe'nin \"korku\"")], metin)
        self.assertEqual(durum, ["uygulanacak"])
        self.assertIn("korku", sonuc)
        self.assertEqual(normallestir("a~b c  d")[0], "a b c d")

    def test_birden_cok_yer_baglamla_secilir(self):
        metin = "Birinci bölüm. Yöntem uygun değildir. Sonra A geldi.\n\nYöntem uygun değildir. Sonra B geldi.\n"
        m = madde("uygun değildir", "uygun olmayabilir", once="Yöntem", sonra="Sonra B geldi")
        sonuc, durum = uygula_hepsi([m], metin)
        self.assertEqual(durum, ["uygulanacak"])
        self.assertIn("uygun değildir. Sonra A", sonuc)
        self.assertIn("uygun olmayabilir. Sonra B", sonuc)
        _, durum = uygula_hepsi([madde("uygun değildir", "x")], metin)
        self.assertEqual(durum, ["birden çok yer (2)"])
        sonuc, _ = uygula_hepsi([madde("uygun değildir", "x", tum=True)], metin)
        self.assertEqual(sonuc.count("x."), 2)

    def test_uygulanmayan_durumlar(self):
        metin = "Bir _italik sözcük_ ve düz metin.\n"
        sonuc, _ = uygula_hepsi([madde("italik sözcük", "eğik yazı")], metin)
        self.assertEqual(sonuc, "Bir _eğik yazı_ ve düz metin.\n")  # biçimin içindeki değişiklik biçimi korur
        _, durum = uygula_hepsi([
            madde("Bir italik", "Bir eğik"),
            madde("olmayan", "z"),
            madde("düz", "düz"),
            {"islem": "Biçim", "eski": "", "yeni": ""},
            madde("ve", "ile", karar="atla"),
        ], metin)
        self.assertEqual(durum, ["elle (biçim içeriyor)", "bulunamadı", "uygulanacak", "elle (Biçim)", "atlandı (karar)"])
        _, durum = uygula_hepsi([madde("düz metin", "yeni metin"), madde("metin", "yazı")], metin)
        self.assertEqual(durum, ["uygulanacak", "çakışma"])
        _, durum = uygula_hepsi([madde("eski metin", "düz metin")], metin)
        self.assertEqual(durum, ["zaten uygulanmış olabilir"])

    def test_typst_karakterleri_kacirilir(self):
        sonuc, _ = uygula_hepsi([madde("yüzde", "#1 ve 5$")], "yüzde\n")
        self.assertEqual(sonuc, "\\#1 ve 5\\$\n")


class Word(unittest.TestCase):
    def test_izli_degisiklik_ve_yorum(self):
        govde = (
            f'<w:document {W}><w:body>'
            '<w:p><w:r><w:t xml:space="preserve">Bu kitap </w:t></w:r>'
            '<w:del w:author="Hoca"><w:r><w:delText>kaygıyı</w:delText></w:r></w:del>'
            '<w:ins w:author="Hoca"><w:r><w:t>korkuyu</w:t></w:r></w:ins>'
            '<w:r><w:t xml:space="preserve"> anlatır ve </w:t></w:r>'
            '<w:ins w:author="Hoca"><w:r><w:t xml:space="preserve">çok </w:t></w:r></w:ins>'
            '<w:r><w:t>sade</w:t></w:r><w:commentRangeStart w:id="0"/><w:r><w:t xml:space="preserve"> yazılmıştır.</w:t></w:r>'
            '<w:commentRangeEnd w:id="0"/></w:p></w:body></w:document>'
        )
        yorum = f'<w:comments {W}><w:comment w:id="0" w:author="Hoca"><w:p><w:r><w:t>Sil: «yazılmıştır»</w:t></w:r></w:p></w:comment></w:comments>'
        with tempfile.TemporaryDirectory() as k:
            yol = Path(k) / "hoca.docx"
            with zipfile.ZipFile(yol, "w") as z:
                z.writestr("word/document.xml", govde)
                z.writestr("word/comments.xml", yorum)
            maddeler = docx_oku(yol)
        self.assertEqual([(m["islem"], m["eski"], m["yeni"]) for m in maddeler], [
            ("Değiştir", "kaygıyı", "korkuyu"),
            ("Değiştir", "anlatır ve ", "anlatır ve çok "),
            ("Sil", "yazılmıştır", ""),
        ])
        metin = "Bu kitap kaygıyı anlatır ve sade yazılmıştır.\n"
        sonuc, _ = uygula_hepsi(maddeler[:1], metin)
        sonuc, _ = uygula_hepsi(maddeler[1:2], sonuc)
        self.assertEqual(sonuc, "Bu kitap korkuyu anlatır ve çok sade yazılmıştır.\n")


class KomutSatiri(unittest.TestCase):
    def test_onceki_tur_denetimi(self):
        with tempfile.TemporaryDirectory() as k:
            k = Path(k)
            (k / "tashih" / "tur-01").mkdir(parents=True)
            (k / "tashih" / "tur-01" / "liste.sonuc.json").write_text(
                json.dumps([dict(madde("kaygı", "korku"), durum="uygulandı")]), encoding="utf-8")
            (k / "eski.typ").write_text("kaygı vardı\n", encoding="utf-8")
            (k / "yeni.typ").write_text("korku vardı\n", encoding="utf-8")
            komut = [sys.executable, str(ARACLAR / "tashih_uygula.py"), "--onceki", str(k / "tashih")]
            self.assertEqual(subprocess.run(komut + [str(k / "eski.typ")], capture_output=True).returncode, 1)
            self.assertEqual(subprocess.run(komut + [str(k / "yeni.typ")], capture_output=True).returncode, 0)


if __name__ == "__main__":
    unittest.main()
