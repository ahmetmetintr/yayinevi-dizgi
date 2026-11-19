"""atif skill'i testleri (ağa çıkmaz). Uçtan uca test yalnız pymupdf ve typst kuruluysa çalışır.
Çalıştırma: python -m unittest discover -s testler"""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "eklenti" / "skills" / "atif" / "araclar"))
from atif_kaynakca import (birlestir, bolum_kaynaklari, doi_bul, kaynak_alanlari, kaynakca_parcalari,  # noqa: E402
                           kaynaklara_ayir)
from atif_ortak import anahtar, kaynakca_basligi_mi  # noqa: E402
from atif_uret import denetle, tablo_sayfalari  # noqa: E402
from atif_xlsx import sutun, xlsx_yaz  # noqa: E402
from atif_yapi import (basili_numara, baslik_temizle, bolum_araliklari, bolum_baslari_tahmini, bolum_basi,  # noqa: E402
                       donemde_mi, duzey_araliklari, govde, kenar_kumesi, kisiler, kitap_basligi, kitap_birimi,
                       kunye_alanlari, tarih_coz, yer_imi_baslari)


def satir(t, x=56.7, y=100.0, sayfa=1, s=9.0, h=680.0):
    return {"t": t, "x": x, "x1": x + 300, "y": y, "sayfa": sayfa, "s": s, "h": h}


def satirlar(*parcalar, sayfa=1, s=9.0, adim=12.0, y=90.0):
    """(x, metin) çiftlerinden alt alta satırlar."""
    return [satir(t, x=x, y=y + i * adim, sayfa=sayfa, s=s) for i, (x, t) in enumerate(parcalar)]


SOL, GIR = 56.7, 92.1  # Vizetek kaynakçası: asılı girinti 1,25 cm


class Ortak(unittest.TestCase):
    def test_anahtar(self):
        self.assertEqual(anahtar("5. KAYNAKÇA"), "kaynakça")
        self.assertEqual(anahtar("Ön Söz*"), "ön söz")
        self.assertEqual(anahtar("IV. İÇİNDEKİLER:"), "içindekiler")
        self.assertTrue(kaynakca_basligi_mi("KAYNAKLAR"))
        self.assertTrue(kaynakca_basligi_mi("References"))
        self.assertFalse(kaynakca_basligi_mi("Kaynaklar ve yöntem üzerine bir değerlendirme yapılmıştır."))


class Birlestirme(unittest.TestCase):
    def test_bolunen_adres_ve_heceleme(self):
        self.assertEqual(birlestir(["Pediatrics, 127(3), 575–579. https://doi.org/10.1542/", "peds.2010-3851"]),
                         "Pediatrics, 127(3), 575–579. https://doi.org/10.1542/peds.2010-3851")
        self.assertEqual(birlestir(["https://doi.org/10.", "1136/adc.41.220.681"]), "https://doi.org/10.1136/adc.41.220.681")
        self.assertEqual(birlestir(["https://doi.org/10.1016/S0140-6736(10)62226-", "X"]),
                         "https://doi.org/10.1016/S0140-6736(10)62226-X")
        self.assertEqual(birlestir(["Brown adipose tissue: Function and physiological sig­", "nificance."]),
                         "Brown adipose tissue: Function and physiological significance.")
        self.assertEqual(birlestir(["Anesthesia & Analgesia, 108(5), 1475–", "1479."]),
                         "Anesthesia & Analgesia, 108(5), 1475–1479.")
        self.assertEqual(birlestir(["öğretmen adayla-", "rında yetkinlik"]), "öğretmen adaylarında yetkinlik")

    def test_adresten_sonra_erisim_notu_ayri_kalir(self):
        self.assertEqual(birlestir(["https://www.tuik.gov.tr/veri", "(Erişim tarihi: 5 Mart 2024)"]),
                         "https://www.tuik.gov.tr/veri (Erişim tarihi: 5 Mart 2024)")


class Ayirma(unittest.TestCase):
    def test_asili_girinti_ve_sayfa_gecisi(self):
        s = satirlar((SOL, "Kaya, M., & Demir, A. (2023). Öğretmen adaylarında dijital yetkinlik. Eğitim"),
                     (GIR, "Araştırmaları Dergisi, 12(2), 45–67. https://doi.org/10.0000/ornek.2023.12"),
                     (SOL, "Yılmaz, A. (2024). Dijital çağda öğretmen eğitimi. Örnek Yayıncılık."),
                     (SOL, "Zeren, G. (2018). Uzun bir başlık ki bir sonraki sayfaya"))
        s += satirlar((GIR + 14, "taşar. Örnek Yayıncılık."), (SOL + 14, "Ünal, B. (2020). Son kaynak."), sayfa=2)
        k = kaynaklara_ayir(s)  # 2. sayfanın sol kenarı farklı (aynalı kenar): girinti sayfa tekliğine göre ölçülür
        self.assertEqual(len(k), 4)
        self.assertTrue(k[0].endswith("Eğitim Araştırmaları Dergisi, 12(2), 45–67. https://doi.org/10.0000/ornek.2023.12"))
        self.assertEqual(k[2], "Zeren, G. (2018). Uzun bir başlık ki bir sonraki sayfaya taşar. Örnek Yayıncılık.")

    def test_ilk_satir_girintili_duzen(self):
        k = kaynaklara_ayir(satirlar((GIR, "Kaya, M. (2023). Başlık bir. Dergi, 1(1),"), (SOL, "1–5."),
                                     (GIR, "Yılmaz, A. (2024). Başlık iki.")))
        self.assertEqual(k, ["Kaya, M. (2023). Başlık bir. Dergi, 1(1), 1–5.", "Yılmaz, A. (2024). Başlık iki."])

    def test_numarali_kaynakca_sag_hizali_numara(self):
        s = satirlar((61, "9. Aboagye J, Goldstein SD. Age at presentation. J Pediatr"),
                     (70, "Surg 2014;49:995–9."), (SOL, "10. Best KE, Tennant PW. Epidemiology of small"),
                     (70, "intestinal atresia. Arch Dis Child 2012;97:353."), (SOL, "11. Kısa kaynak 2001."))
        self.assertEqual(kaynaklara_ayir(s), ["Aboagye J, Goldstein SD. Age at presentation. J Pediatr Surg 2014;49:995–9.",
                                              "Best KE, Tennant PW. Epidemiology of small intestinal atresia. Arch Dis "
                                              "Child 2012;97:353.", "Kısa kaynak 2001."])

    def test_girintisiz_kaynakca_yazar_kalibi_ve_aralik(self):
        s = satirlar((SOL, "Kaya, M. (2023). Başlık bir."), (SOL, "Yılmaz, A. (2024). Başlık iki ve"),
                     (SOL, "devamı."), (SOL, "Türkiye İstatistik Kurumu. (2020). Nüfus."))
        self.assertEqual(len(kaynaklara_ayir(s)), 3)
        aralikli = [satir("Ak, B. 2001 yılında yazılmış kaynak", y=90), satir("ikinci satırı", y=101),
                    satir("ayrı paragraf, yazar kalıbı yok", y=125)]
        self.assertEqual(len(kaynaklara_ayir(aralikli)), 2)

    def test_tek_satirlik_doi_ve_alt_baslik(self):
        s = satirlar((SOL, "Türkçe Kaynaklar"), (SOL, "Ak, B. (2020). Başlık. Dergi, 1, 2–3."),
                     (SOL, "https://doi.org/10.3390/ijms24043749"), (SOL, "Yabancı Kaynaklar"),
                     (SOL, "Brown, C. (2019). Title."))
        k = kaynaklara_ayir(s)
        self.assertEqual(k, ["Ak, B. (2020). Başlık. Dergi, 1, 2–3. https://doi.org/10.3390/ijms24043749",
                             "Brown, C. (2019). Title."])


class Alanlar(unittest.TestCase):
    def test_apa(self):
        a = kaynak_alanlari("Kaya, M., & Demir, A. (2023). Öğretmen adaylarında dijital yetkinlik. Eğitim "
                            "Araştırmaları Dergisi, 12(2), 45–67. https://doi.org/10.0000/ornek.2023.12")
        self.assertEqual((a["ilk_yazar"], a["yil"], a["baslik"], a["doi"], a["bicim"]),
                         ("Kaya", "2023", "Öğretmen adaylarında dijital yetkinlik", "10.0000/ornek.2023.12", "APA"))

    def test_kurum_yazari_parantezli_ve_tarihsiz(self):
        a = kaynak_alanlari("World Health Organization (WHO). (2020a, Mart 3). Report. https://who.int/x")
        self.assertEqual((a["ilk_yazar"], a["yil"], a["bicim"]), ("World Health Organization (WHO)", "2020a", "APA"))
        self.assertEqual(kaynak_alanlari("A.B.A. American Burn Association. (n.d.). Burn prevention.")["yil"], "n.d.")

    def test_apa_disi(self):
        a = kaynak_alanlari("Haight C, Towsley HA. Congenital atresia. Surg Gynecol Obstet1943;76:672.")
        self.assertEqual((a["yil"], a["bicim"], a["ilk_yazar"]), ("1943", "tanınmadı", "Haight C"))

    def test_doi_parantez(self):
        self.assertEqual(doi_bul("The Lancet. https://doi.org/10.1016/S0140-6736(18)32485-1."),
                         "10.1016/S0140-6736(18)32485-1")
        self.assertEqual(doi_bul("(bkz. 10.1234/abc)."), "10.1234/abc")
        self.assertEqual(doi_bul("DOI yok."), "")


class Parcalar(unittest.TestCase):
    def test_birden_cok_kaynakca_ve_govdeye_donus(self):
        bolum = [satir("Gövde metni", s=11, y=80), satir("KAYNAKLAR", s=11, y=100, x=190)]
        bolum += satirlar((SOL, "Ak, B. (2020). Bir."), (SOL, "Can, D. (2021). İki."), (SOL, "Ece, F. (2022). Üç."),
                          y=120)
        bolum += [satir("B. İKİNCİ KISIM", s=11, y=200), satir("Gövde yine 11 punto.", s=11, y=215)]
        bolum += [satir("KAYNAKLAR", s=11, y=60, sayfa=3, x=190), satir("Gül, H. (2019). Dört.", y=80, sayfa=3),
                  satir("Ek 1. Anket Formu", s=11, y=120, sayfa=3), satir("Soru 1", s=11, y=140, sayfa=3)]
        parcalar = kaynakca_parcalari(bolum)
        self.assertEqual([(p, len(x)) for p, x in parcalar], [(1, 3), (3, 1)])
        kayitlar, sayfalar = bolum_kaynaklari(bolum)
        self.assertEqual([k["no"] for k in kayitlar], [1, 2, 3, 4])
        self.assertEqual(sayfalar, [1, 3])
        self.assertEqual(bolum_kaynaklari([satir("Kaynakçasız bölüm")]), ([], []))


KUNYE = """Eğitimde Güncel Yaklaşımlar
ISBN: 978-605-70000-0-4
E-ISBN: 978-605-70000-1-1
DOI: 10.54637/vizetek.9786050000001
Baskı: Ankara | Ocak 2026
Yayıncı Sertifika No: 41575"""


class Kunye(unittest.TestCase):
    def test_vizetek_kunyesi(self):
        self.assertEqual(kunye_alanlari(KUNYE), {"isbn": "978-605-70000-0-4", "e_isbn": "978-605-70000-1-1",
                                                 "doi": "10.54637/vizetek.9786050000001",
                                                 "yayim_tarihi": "2026-01", "yayin_yeri": "Ankara"})

    def test_taslak_ve_baska_bicimler(self):
        taslak = kunye_alanlari("ISBN: [DOLDUR]\nBaskı: [DOLDUR: Ankara | Ay Yıl]\nSertifika")
        self.assertEqual((taslak["isbn"], taslak["yayim_tarihi"], taslak["yayin_yeri"]), ("", "", ""))
        diger = kunye_alanlari("Elektronik ISBN: 978-1-00-000000-2\n1. Basım: Şubat 2026, İstanbul")
        self.assertEqual((diger["isbn"], diger["e_isbn"], diger["yayim_tarihi"], diger["yayin_yeri"]),
                         ("", "978-1-00-000000-2", "2026-02", "İstanbul"))

    def test_tarih_ve_donem(self):
        self.assertEqual(tarih_coz("Ankara | Mart 2026"), "2026-03")
        self.assertEqual(tarih_coz("Ankara, 2026"), "2026")
        self.assertTrue(donemde_mi("2026-02", "2026-01..2026-03"))
        self.assertFalse(donemde_mi("2026-04", "2026-01..2026-03"))
        self.assertTrue(donemde_mi("2026-11", "2026"))
        self.assertIsNone(donemde_mi("2026", "2026-01..2026-03"))
        self.assertFalse(donemde_mi("2025", "2026-01..2026-03"))
        self.assertIsNone(donemde_mi("", "2026"))


class Yapi(unittest.TestCase):
    def test_sayfa_numarasi(self):
        alt = [satir("5", y=632.5, s=8), satir("metin", y=300)]
        self.assertEqual(basili_numara("ageLabel5", alt), "5")  # pymupdf 1.26'nın bozuk etiketi
        self.assertEqual(basili_numara("12", alt), "12")
        self.assertEqual(basili_numara("", [satir("metin")]), None)

    def test_ust_bilgi_atilir_kaynakca_basligi_kalir(self):
        tum = [satir("EĞİTİMDE GÜNCEL YAKLAŞIMLAR", y=24, sayfa=p) for p in (3, 4, 5)]
        tum += [satir("KAYNAKLAR", y=40, sayfa=p) for p in (3, 4, 5)] + [satir(str(p), y=640, sayfa=p) for p in (3, 4)]
        tum += [satir("Kaya, M. (2023). Tek seferlik satır üst bantta.", y=50, sayfa=5)]
        kalan = [s["t"] for s in govde(tum, kenar_kumesi(tum))]
        self.assertEqual(kalan, ["KAYNAKLAR"] * 3 + ["Kaya, M. (2023). Tek seferlik satır üst bantta."])

    def test_baslik_temizle(self):
        self.assertEqual(baslik_temizle("1 Çocuklarda Fizyolojik Farklılıklar"), "Çocuklarda Fizyolojik Farklılıklar")
        self.assertEqual(baslik_temizle("BÖLÜM 3: Yöntem*"), "Yöntem")
        self.assertEqual(baslik_temizle("COVID-19 ve Okul"), "COVID-19 ve Okul")

    def test_ayni_sayfadaki_girdiler_birlesir(self):
        toc = [[1, "KISIM I", 27], [1, "Giriş ve Temeller", 27], [1, "BÖLÜM 2", 34], [1, "Tarihsel Geçmiş:", 34],
               [1, "Rousseau'dan Bugüne", 34], [2, "2.1. Neden Tarih", 34], [1, "BÖLÜM 3", 50]]
        self.assertEqual(duzey_araliklari(toc, 1, 60), [("KISIM I: Giriş ve Temeller", 27, 33),
                                                        ("Tarihsel Geçmiş: Rousseau'dan Bugüne", 34, 49),
                                                        ("BÖLÜM 3", 50, 60)])

    def test_bolum_duzeyi(self):
        # Klinik kitap: 1. düzey bölüm, 2. düzey alt başlık; bir bölümde iki kaynakça (alt kısımlı bölüm)
        toc = [[1, "Ön Söz", 3], [1, "1 Birinci", 5], [2, "Giriş", 5], [2, "Sonuç", 9], [1, "2 İkinci", 12],
               [2, "A. Kısım", 12], [2, "B. Kısım", 15], [1, "3 Üçüncü", 20], [2, "Giriş", 20], [2, "Yöntem", 22]]
        self.assertEqual([a[0] for a in bolum_araliklari(toc, 25, [10, 14, 18, 24])],
                         ["1 Birinci", "2 İkinci", "3 Üçüncü"])
        # Kısımlı kitap: 1. düzey kısım, bölümler 2. düzeyde
        kisimli = [[1, "Kısım I", 3], [2, "Bölüm A", 4], [2, "Bölüm B", 10], [1, "Kısım II", 16], [2, "Bölüm C", 17],
                   [2, "Bölüm D", 22]]
        self.assertEqual([a[0] for a in bolum_araliklari(kisimli, 28, [9, 15, 21, 28])],
                         ["Bölüm A", "Bölüm B", "Bölüm C", "Bölüm D"])
        self.assertEqual(bolum_araliklari([[1, "Giriş", 3]], 10, []), [])

    def test_bolum_basi(self):
        ilk = [satir("5. PEDİATRİK ANESTEZİ VE AĞRI KONTROLÜ", s=13, y=133, x=90),
               satir("Göksun GÜNAYDIN KEÇELİ**", s=11, y=172, x=264),
               satir("Ayşe YILMAZ*, Mehmet KAYA**", s=11, y=186, x=264),
               satir("GİRİŞ", s=11, y=207, x=211), satir("Pediatrik anestezi, yaşa bağlı ...", s=11, y=228, x=70)]
        self.assertEqual(bolum_basi(ilk), ("5. PEDİATRİK ANESTEZİ VE AĞRI KONTROLÜ",
                                           ["Göksun GÜNAYDIN KEÇELİ", "Ayşe YILMAZ", "Mehmet KAYA"]))
        telif = [satir("BÖLÜM 1", s=24, y=80), satir("Giriş: Dizgi Nedir", s=20, y=120),
                 satir("İlk Kavramlar", s=11, y=160, x=56.7), satir("Dizgi, metni okunur kılan…", s=11, y=180)]
        self.assertEqual(bolum_basi(telif), ("Giriş: Dizgi Nedir", []))

    def test_telif_kitap_tek_birim(self):
        toc = [[1, "İÇİNDEKİLER", 13], [1, "KISIM I", 27], [1, "Giriş ve Temeller", 27], [1, "BÖLÜM 1", 29],
               [1, "Giriş", 29], [1, "BÖLÜM 2", 34], [1, "Tarih", 34], [1, "BÖLÜM 15", 246], [1, "Görüşmeler", 246]]
        baslar = yer_imi_baslari(toc, 290, 2)
        self.assertEqual(baslar, [29, 34, 246])  # içindekiler ve kısım sayfası bölüm değil
        self.assertEqual(kitap_birimi(baslar, [265]), 29)
        self.assertIsNone(kitap_birimi(baslar, [33, 265]))  # bölüm sonlarında kaynakça: editörlü düzen
        self.assertIsNone(kitap_birimi([29, 246], [265]))

    def test_ic_kapak_ve_kisiler(self):
        ic_kapak = [satir("ALIŞTIRMA TERAPİSİ", s=20, y=100), satir("Korkuyla Yüzleşmeyi Öğrenmek", s=14, y=130),
                    satir("Dr. Ahmet METİN", s=12, y=170)]
        self.assertEqual(kitap_basligi(ic_kapak, 11), ("ALIŞTIRMA TERAPİSİ", "Korkuyla Yüzleşmeyi Öğrenmek",
                                                       "Dr. Ahmet METİN"))
        editorlu = [satir("Eğitimde Güncel Yaklaşımlar", s=20, y=100), satir("Editör: Doç. Dr. Örnek EDİTÖR", y=150)]
        self.assertEqual(kitap_basligi(editorlu, 11)[2], "Doç. Dr. Örnek EDİTÖR")
        self.assertEqual(kisiler("Doç. Dr. Ayşe YILMAZ*, Prof. Dr. Ali KAYA ve Dr. Öğr. Üyesi Can ÖZ"),
                         ["Ayşe YILMAZ", "Ali KAYA", "Can ÖZ"])

    def test_bolum_baslari_tahmini(self):
        ozet = [(1, "Kitap Adı", 20), (2, "ISBN: …", 8), (3, "ÖN SÖZ", 13), (5, "BİRİNCİ BÖLÜM BAŞLIĞI", 13),
                (6, "gövde", 11), (8, "KAYNAKLAR", 13), (9, "İKİNCİ BÖLÜM", 14)]
        self.assertEqual(bolum_baslari_tahmini(ozet, 11, 2), [5, 9])


class Xlsx(unittest.TestCase):
    def test_sutun_harfi(self):
        self.assertEqual([sutun(0), sutun(25), sutun(26), sutun(701)], ["A", "Z", "AA", "ZZ"])

    def test_gecerli_ve_belirlenimci(self):
        with tempfile.TemporaryDirectory() as k:
            sayfalar = [("Kaynaklar", ["Kod", "Kaynak", "No"], [["978", "Işık & <Öz> \x01", 3]], [10, 50, 5]),
                        ("Bölümler: [1]", ["A"], [], [10])]
            xlsx_yaz(Path(k) / "a.xlsx", sayfalar)
            xlsx_yaz(Path(k) / "b.xlsx", sayfalar)
            self.assertEqual((Path(k) / "a.xlsx").read_bytes(), (Path(k) / "b.xlsx").read_bytes())
            with zipfile.ZipFile(Path(k) / "a.xlsx") as z:
                for ad in z.namelist():
                    ET.fromstring(z.read(ad))  # her parça iyi biçimli XML
                sayfa = z.read("xl/worksheets/sheet1.xml").decode()
                self.assertIn("Işık &amp; &lt;Öz&gt; </t>", sayfa)
                self.assertIn('<c r="C2"><v>3</v></c>', sayfa)
                self.assertIn('name="Bölümler   1 "', z.read("xl/workbook.xml").decode())


def ornek_dizin():
    kaynak = {"no": 1, "metin": "Ak, B. (2020). Başlık.", "ilk_yazar": "Ak", "yil": "2020", "baslik": "Başlık",
              "doi": "", "bicim": "APA"}
    bolum = {"no": 1, "baslik": "Birinci", "yazarlar": ["Ayşe YILMAZ"], "doi": "", "ilk_sayfa": "5",
             "son_sayfa": "9", "pdf_ilk": 7, "pdf_son": 11, "kaynakca_sayfalari": [11], "atla": False,
             "kaynaklar": [kaynak, dict(kaynak, no=2, yil="")]}
    kitap = {"kod": "9786050000001", "dosya": "test_atif.py", "baslik": "Kitap", "alt_baslik": "Alt",
             "editorler": "Ed", "isbn": "", "e_isbn": "978-605-000-00-1", "doi": "", "yayin_yeri": "Ankara",
             "yayim_tarihi": "2026-01", "kunye_sayfasi": 2, "bolum_kaynagi": "yer imleri", "uyarilar": [],
             "bolumler": [bolum, dict(bolum, no=2, kaynaklar=[], kaynakca_sayfalari=[], atla=True)]}
    return {"surum": 1, "kitaplar": [kitap]}


class Uret(unittest.TestCase):
    def test_denetim(self):
        dizin = ornek_dizin()
        hatalar, uyarilar = denetle(dizin, Path(__file__).parent)
        self.assertEqual(hatalar, [])  # atlanan bölümün kaynaksız olması hata değil
        self.assertEqual(uyarilar, ["9786050000001 · 1. bölüm: 1 kaynakta yıl okunamadı"])
        dizin["kitaplar"].append(dict(dizin["kitaplar"][0], kunye_sayfasi=None, dosya="yok.pdf"))
        dizin["kitaplar"][1]["bolumler"] = [dict(dizin["kitaplar"][0]["bolumler"][0], kaynaklar=[])]
        hatalar, _ = denetle(dizin, Path(__file__).parent)
        self.assertIn("9786050000001: aynı kodlu 2 kitap var", hatalar)
        self.assertTrue(any("künye sayfası yok" in h for h in hatalar))
        self.assertTrue(any("PDF'i bulunamadı" in h for h in hatalar))
        self.assertTrue(any("1. bölüm: kaynak yok" in h for h in hatalar))

    def test_ornek_sablon(self):
        sablon = KOK / "eklenti" / "skills" / "atif" / "sablon"
        dizin = json.loads((sablon / "dizin-ornegi.json").read_text(encoding="utf-8"))
        hatalar, uyarilar = denetle(dizin, sablon)
        self.assertEqual(hatalar, ["9780000000001: kitabın PDF'i bulunamadı (kitaplar/egitimde-guncel-yaklasimlar.pdf)"])
        self.assertEqual(uyarilar, [])

    def test_tablo(self):
        kaynaklar, bolumler, kitaplar = tablo_sayfalari(ornek_dizin())
        self.assertEqual([len(kaynaklar[2]), len(bolumler[2]), len(kitaplar[2])], [2, 1, 1])
        ilk = dict(zip(kaynaklar[1], kaynaklar[2][0]))
        self.assertEqual((ilk["Kitap"], ilk["Bölüm sayfaları"], ilk["Bölüm PDF'i"]),
                         ("Kitap: Alt", "5–9", "pdf/9786050000001/9786050000001-bolum-01.pdf"))
        self.assertTrue(all(len(s) == len(b) for _, b, satirlar, g in (kaynaklar, bolumler, kitaplar)
                            for s in satirlar + [g]))


@unittest.skipUnless(importlib.util.find_spec("pymupdf") and shutil.which("typst"), "pymupdf ve typst gerekir")
class UctanUca(unittest.TestCase):
    def test_vizetek_editorlu_ornek(self):
        from atif_hazirla import kitap_oku
        from atif_uret import bolum_pdf
        import pymupdf
        with tempfile.TemporaryDirectory() as k:
            pdf = Path(k) / "editorlu.pdf"
            subprocess.run(["typst", "compile", "--root", str(KOK), str(KOK / "testler/ornek-vizetek/editorlu.typ"),
                            str(pdf)], check=True, capture_output=True)
            kitap = kitap_oku(pdf)
            self.assertEqual((kitap["e_isbn"], kitap["yayim_tarihi"], kitap["kunye_sayfasi"]),
                             ("978-000-00-0000-1", "2026-11", 2))
            b1, b2 = kitap["bolumler"]
            self.assertEqual((b1["baslik"], b1["yazarlar"], b1["ilk_sayfa"], b1["son_sayfa"], len(b1["kaynaklar"])),
                             ("Öğretmen Eğitiminde Dijital Dönüşüm", ["Ayşe YILMAZ", "Mehmet KAYA"], "5", "7", 2))
            self.assertEqual(b1["kaynaklar"][0]["doi"], "10.0000/ornek.2023.12")
            self.assertEqual((b2["yazarlar"], len(b2["kaynaklar"])), (["Zeynep ARSLAN"], 1))
            bolum_pdf(pymupdf.open(pdf), kitap, b1, Path(k) / "b1.pdf")
            cikti = pymupdf.open(Path(k) / "b1.pdf")
            self.assertEqual(len(cikti), 3)
            self.assertIn("ISBN", cikti[0].get_text())
            self.assertIn("KAYNAKLAR", cikti[2].get_text())


if __name__ == "__main__":
    unittest.main()
