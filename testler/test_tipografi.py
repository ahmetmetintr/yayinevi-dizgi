"""tipografi.py testleri. Çalıştırma: python -m unittest discover -s testler"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eklenti" / "skills" / "dizgi" / "araclar"))
from tipografi import dogrula, duzelt  # noqa: E402


def d(metin, **kw):
    return duzelt(metin, **kw)[0]


class Yazi(unittest.TestCase):
    def test_bosluk_ve_noktalama(self):
        self.assertEqual(d("bir  kitap , iki ( üç ) dört !"), "bir kitap, iki (üç) dört!")
        self.assertEqual(d("elma,armut;kiraz"), "elma, armut; kiraz")
        self.assertEqual(d("3,5 kilo"), "3,5 kilo")  # ondalık virgüle dokunma

    def test_uc_nokta_ve_kesme(self):
        self.assertEqual(d("bekledi... Ankara´da ve İzmir‘de"), "bekledi… Ankara’da ve İzmir’de")
        self.assertEqual(d("1990´lı yıllar"), "1990’lı yıllar")
        self.assertEqual(d("Ankara\\`da"), "Ankara’da")  # pandoc'un kaçışlı ters tırnağı

    def test_tirnak(self):
        self.assertEqual(d("„söz” ve « başka »"), '"söz” ve "başka"')

    def test_cizgiler(self):
        self.assertEqual(d("s. 12-15 arası"), "s.~12–15 arası")
        self.assertEqual(d("ISBN 978-605-00-0000-0 ve 2026-11-19"), "ISBN 978-605-00-0000-0 ve 2026-11-19")
        self.assertEqual(d("yazar - ki usta idi - geldi"), "yazar – ki usta idi – geldi")
        self.assertEqual(d("yazar - geldi", ara="—"), "yazar — geldi")
        self.assertEqual(d("Türk-İslam sentezi"), "Türk-İslam sentezi")
        self.assertEqual(d("bkz. s. 12-15, ayrıca 3-4."), "bkz. s.~12–15, ayrıca 3–4.")
        self.assertEqual(d("oran 1,5-2,5 arası"), "oran 1,5-2,5 arası")  # ondalıklı aralığa dokunma

    def test_konusma_cizgisi(self):
        self.assertEqual(d("\\- Merhaba.\n– Nasılsın?\n- liste ögesi"), "— Merhaba.\n— Nasılsın?\n- liste ögesi")
        self.assertEqual(d("-- Peki.", konusma="–"), "– Peki.")
        self.assertEqual(d("\\- Fizik muayene bulguları", konusma=None), "\\- Fizik muayene bulguları")  # bilimsel kitap

    def test_tip_kitabi_kaliplari(self):
        # Klinik Çocuk Cerrahisi (19.11.2026): dikiş numarası aralık değildir; APA'nın yazar atlama üç noktası kalır
        self.assertEqual(d("5-0 Prolene ve 4-0 PDS ile"), "5-0 Prolene ve 4-0 PDS ile")
        self.assertEqual(d("Shenoy, M., . . . Roe, L. (2020)."), "Shenoy, M., . . . Roe, L. (2020).")

    def test_baglanti_ve_doi_korunur(self):
        # pandoc "//" dizisini "/\/" diye kaçışlar; DOI'deki tire aralık çizgisine dönmemeli
        for s in ("https:/\\/doi.org/10.1542/peds.2010-3851", "https://doi.org/10.1016/S0140-6736(20)30183-5",
                  "doi:10.1542/peds.2010-3851", "yazı 10.1542/peds.2010-3851 numaralı",
                  # eski Wiley (SICI) DOI'si: pandoc < ve > işaretlerini kaçışlar; sondaki "2-1" bozulmamalı
                  "https:/\\/doi.org/10.1002/(SICI)1097-4679(200004)56:4\\<519::AID-JCLP6\\>3.0.CO;2-1"):
            self.assertEqual(d(s), s)

    def test_yuzde_ve_bolunmez_bosluk(self):
        self.assertEqual(d("oran 25% ve % 30"), "oran %25 ve %30")
        self.assertEqual(d("Prof.Dr. Ayşe ile 5 kg un"), "Prof.~Dr.~Ayşe ile 5~kg un")
        self.assertEqual(d("3 saat sürdü"), "3 saat sürdü")


class Kod(unittest.TestCase):
    def test_koda_dokunmaz(self):
        kaynak = (
            '#set text(lang: "tr", font:  "A - B")\n'
            '#image("gorsel-1-2.png")\n'
            "$5 - 3$ ve `ham  - metin` <etiket> @kaynak-2020\n"
            "// yorum  - burada\n"
            "https://ornek.com/a--b,c\n"
        )
        self.assertEqual(d(kaynak), kaynak)

    def test_icerik_bloklari_duzeltilir(self):
        self.assertEqual(d("söz#footnote[bkz. s. 12 , not]"), "söz#footnote[bkz. s.~12, not]")
        self.assertEqual(d('#link("https://a.b/c - d")[bu  - şu]'), '#link("https://a.b/c - d")[bu – şu]')
        self.assertEqual(
            d('#figure(image("a.png"), caption: [Şekil  açıklaması])'),
            '#figure(image("a.png"), caption: [Şekil açıklaması])',
        )
        self.assertEqual(d("#emph[a ,b] ve *kalın  yazı*"), "#emph[a, b] ve *kalın yazı*")

    def test_rapor_sayar(self):
        _, sayac, ornekler = duzelt("a  b  c")
        self.assertEqual(sayac["çift boşluk / sekme"], 2)
        self.assertEqual(ornekler["çift boşluk / sekme"][0][0], 1)
        _, _, ornekler = duzelt("giriş\n\n\\- Merhaba.")
        self.assertEqual(ornekler["konuşma çizgisi"][0][0], 3)


class Dogrulama(unittest.TestCase):
    def test_harf_degisirse_yakalar(self):
        self.assertEqual(dogrula("kitap", "kitab"), (False, True))
        self.assertEqual(dogrula("a #b", "a b"), (True, False))
        self.assertEqual(dogrula("a  ,b", "a, b"), (True, True))


if __name__ == "__main__":
    unittest.main()
