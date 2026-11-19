"""doi skill'i testleri (ağa çıkmaz, pymupdf gerektirmez). Çalıştırma: python -m unittest discover -s testler"""
import copy
import json
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ARACLAR = Path(__file__).resolve().parents[1] / "eklenti" / "skills" / "doi"
sys.path.insert(0, str(ARACLAR / "araclar"))
from doi_hazirla import bolumleri_esle, kisi_listesi, kunye_oku, tarih_ve_yer, yazar_bilgisi  # noqa: E402
from doi_ortak import ad_ayir, bas_harf, doldur_yerleri, isbn_gecerli, orcid_gecerli  # noqa: E402
from doi_sorgula import crossref_kaydi, doldur, karsilastir  # noqa: E402
from doi_xml import NS, denetle, tablo, xml_uret  # noqa: E402

K = f"{{{NS}}}"
KISI = {"ad": "Ayşe", "soyad": "Yılmaz", "rol": "yazar", "orcid": "0000-0002-1825-0097",
        "kurum": "Örnek Üniversitesi", "birim": "Eğitim Fakültesi"}
KAYIT = {
    "yatiran": {"ad": "Vizetek Yayıncılık", "eposta": "dizgi@example.com"},
    "kitap": {"tur": "editorlu", "baslik": "Eğitimde Güncel Yaklaşımlar", "alt_baslik": "Kuram ve Uygulama",
              "doi": "10.54637/vizetek.9780000000002", "adres": "https://vizetek.com.tr/urun/ornek",
              "isbn_basili": "", "isbn_elektronik": "978-0-00-000000-2", "yayim_tarihi": "2026-11-19",
              "basili": False, "baski_no": 1, "ozet": "Kitabın özeti.", "yayinevi": "Vizetek Yayıncılık",
              "yayin_yeri": "Ankara", "dil": "tr",
              "kisiler": [{"ad": "Cansev", "soyad": "Meşe Yavuz", "rol": "editor", "orcid": "0000-0002-8079-1230",
                           "kurum": "", "birim": ""}]},
    "bolumler": [
        {"no": 1, "baslik": "Birinci Bölüm", "doi": "10.54637/vizetek.9780000000002.ch1", "ilk_sayfa": "5",
         "son_sayfa": "7", "adres": "", "kisiler": [KISI]},
        {"no": 2, "baslik": "İkinci Bölüm", "doi": "10.54637/vizetek.9780000000002.ch2", "ilk_sayfa": "9",
         "son_sayfa": "10", "adres": "", "kisiler": [dict(KISI, ad="Zeynep", soyad="Arslan", orcid="")]},
    ],
}


def kayit(**degisiklik):
    k = copy.deepcopy(KAYIT)
    for yol, deger in degisiklik.items():
        hedef, *anahtarlar = yol.split("__")
        ust = k[hedef]
        for a in anahtarlar[:-1]:
            ust = ust[int(a)] if a.isdigit() else ust[a]
        ust[int(anahtarlar[-1]) if anahtarlar[-1].isdigit() else anahtarlar[-1]] = deger
    return k


class Ortak(unittest.TestCase):
    def test_ad_ayir(self):
        self.assertEqual(ad_ayir("Ayşe YILMAZ"), ("Ayşe", "Yılmaz", True))
        self.assertEqual(ad_ayir("Doç. Dr. Cansev MEŞE YAVUZ"), ("Cansev", "Meşe Yavuz", True))
        self.assertEqual(ad_ayir("Dr. Öğr. Üyesi İbrahim IŞIK"), ("İbrahim", "Işık", True))
        self.assertEqual(ad_ayir("Dan BROWN")[:2], ("Dan", "Brown"))  # noktasız "Dan" unvan değil
        self.assertFalse(ad_ayir("AYŞE YILMAZ")[2])

    def test_bas_harf_turkce(self):
        self.assertEqual(bas_harf("İNCE"), "İnce")
        self.assertEqual(bas_harf("ÖZ-KAYA"), "Öz-Kaya")
        self.assertEqual(bas_harf("IŞIK"), "Işık")

    def test_saglama_haneleri(self):
        self.assertTrue(isbn_gecerli("978-0-00-000000-2"))
        self.assertTrue(isbn_gecerli("9786253825409"))
        self.assertFalse(isbn_gecerli("9786253825408"))
        self.assertTrue(orcid_gecerli("0000-0002-1825-0097"))
        self.assertFalse(orcid_gecerli("0000-0002-1825-0098"))

    def test_doldur_yerleri(self):
        self.assertEqual(doldur_yerleri({"a": [{"b": "[DOLDUR: x]"}], "c": "tamam"}), ["kayıt.a[0].b"])


class Hazirla(unittest.TestCase):
    KITAP_TYP = '''#show: kitap.with(..vizetek-editorlu,
  baslik: "Eğitimde Güncel Yaklaşımlar", alt-baslik: none, yazar: "Editörler: Prof. Dr. Ali VELİ, Doç. Dr. Ayşe KARA",
  yayinevi: "Vizetek Yayıncılık",
  kunye: (("ISBN", "[DOLDUR]"), ("E-ISBN", "978-0-00-000000-2"), ("DOI", "10.54637/vizetek.9780000000002"),
    ("Baskı", "Ankara | Kasım 2026")))'''

    def test_kunye(self):
        k = kunye_oku(self.KITAP_TYP)
        self.assertEqual((k["baslik"], k["alt_baslik"], k["profil"]), ("Eğitimde Güncel Yaklaşımlar", None,
                                                                         "vizetek-editorlu"))
        self.assertNotIn("ISBN", k["kunye"])  # [DOLDUR] değer alınmaz
        self.assertEqual(k["kunye"]["DOI"], "10.54637/vizetek.9780000000002")
        self.assertEqual(tarih_ve_yer(k["kunye"]["Baskı"], None), ("2026-11", "Ankara"))
        self.assertEqual(tarih_ve_yer(k["kunye"]["Baskı"], "2026-11-19")[0], "2026-11-19")

    def test_editorler(self):
        uyarilar = []
        kisiler = kisi_listesi("Editörler: Prof. Dr. Ali VELİ, Doç. Dr. Ayşe KARA", "editor", uyarilar)
        self.assertEqual([(k["ad"], k["soyad"], k["rol"]) for k in kisiler],
                         [("Ali", "Veli", "editor"), ("Ayşe", "Kara", "editor")])
        self.assertEqual(uyarilar, [])

    def test_yazar_bilgisi(self):
        k = yazar_bilgisi("Ayşe YILMAZ", r"Prof. Dr., Örnek Üniversitesi, Eğitim Fakültesi, Eğitim Bilimleri "
                                         r"Bölümü. ORCID: 0000-0002-1825-0097, ayse\@ornek.edu.tr", [])
        self.assertEqual((k["ad"], k["soyad"], k["orcid"]), ("Ayşe", "Yılmaz", "0000-0002-1825-0097"))
        self.assertEqual((k["kurum"], k["birim"]), ("Örnek Üniversitesi", "Eğitim Fakültesi, Eğitim Bilimleri Bölümü"))

    def test_bolum_esleme(self):
        pdf = [{"baslik": "Ön Söz", "ilk": "1", "son": "1", "etiketli": True},
               {"baslik": "Öğretmen Eğitiminde Dijital Dönüşüm", "ilk": "5", "son": "7", "etiketli": True},
               {"baslik": "Sahipsiz Başlık", "ilk": "8", "son": "8", "etiketli": True},
               {"baslik": "Okul Öncesinde Oyun", "ilk": "9", "son": "10", "etiketli": True}]
        typ = [("Okul Öncesinde _Oyun_", []), ("Öğretmen Eğitiminde Dijital Dönüşüm", []), ("Kayıp Bölüm", [])]
        uyarilar = []
        sonuc = bolumleri_esle(pdf, typ, uyarilar)
        self.assertEqual([g["ilk"] for g, _ in sonuc], ["5", "9"])  # PDF sırası, Ön Söz bölüm değil
        self.assertEqual(len(uyarilar), 2)  # sahipsiz başlık + PDF'te olmayan bölüm
        self.assertEqual(len(bolumleri_esle(pdf, None, [])), 3)  # yalnız PDF: ön/son sayfalar dışı


class Denetim(unittest.TestCase):
    def sorunlar(self, k):
        return [ne for _, ne in denetle(k)[0]]

    def test_gecerli_kayit(self):
        hatalar, uyarilar = denetle(KAYIT)
        self.assertEqual(hatalar, [])
        self.assertEqual(len(uyarilar), 1)  # ikinci bölüm yazarının ORCID'i yok

    def test_hatalar(self):
        self.assertIn("[DOLDUR] kalmış", self.sorunlar(kayit(kitap__adres="[DOLDUR: adres]")))
        self.assertTrue(any("iki kez" in s for s in self.sorunlar(kayit(bolumler__1__doi=KAYIT["bolumler"][0]["doi"]))))
        self.assertTrue(any("sağlama" in s for s in self.sorunlar(kayit(bolumler__0__kisiler__0__orcid="0000-0002-1825-0098"))))
        self.assertTrue(any("en az bir editör" in s for s in self.sorunlar(kayit(kitap__kisiler=[]))))
        self.assertTrue(any("aynı önekte" in s for s in self.sorunlar(kayit(bolumler__0__doi="10.1234/baska.ch1"))))
        self.assertTrue(any("küçük" in s for s in self.sorunlar(kayit(bolumler__0__son_sayfa="3"))))
        self.assertTrue(any("sırayla" in s for s in self.sorunlar(kayit(bolumler__1__no=3))))
        self.assertTrue(any("e-posta" in s for s in self.sorunlar(kayit(yatiran__eposta="yok"))))

    def test_tablo(self):
        metin = tablo(KAYIT)
        self.assertIn("| 1 | 10.54637/vizetek.9780000000002.ch1 | Birinci Bölüm | Ayşe Yılmaz (ORCID ✓) | 5–7 | "
                      "kitap sayfası |", metin)


class Xml(unittest.TestCase):
    def setUp(self):
        self.metin = xml_uret(KAYIT, "20261119220000")
        self.kok = ET.fromstring(self.metin.encode("utf-8"))

    def test_belirlenimci(self):
        self.assertEqual(self.metin, xml_uret(copy.deepcopy(KAYIT), "20261119220000"))
        self.assertEqual(self.kok.find(f"{K}head/{K}timestamp").text, "20261119220000")

    def test_kitap(self):
        kitap = self.kok.find(f"{K}body/{K}book")
        self.assertEqual(kitap.get("book_type"), "edited_book")
        m = kitap.find(f"{K}book_metadata")
        self.assertEqual([p.get("contributor_role") for p in m.iter(f"{K}person_name")], ["editor"])
        self.assertEqual(m.find(f"{K}isbn").text, "9780000000002")
        self.assertEqual(m.find(f"{K}doi_data/{K}doi").text, "10.54637/vizetek.9780000000002")
        sira = [c.tag.split("}")[1] for c in m]
        self.assertEqual(sira, ["contributors", "titles", "abstract", "edition_number", "publication_date", "isbn",
                                "publisher", "doi_data"])  # Crossref şemasındaki sıra

    def test_bolumler(self):
        bolumler = self.kok.findall(f"{K}body/{K}book/{K}content_item")
        self.assertEqual([b.find(f"{K}doi_data/{K}doi").text for b in bolumler],
                         ["10.54637/vizetek.9780000000002.ch1", "10.54637/vizetek.9780000000002.ch2"])
        ilk = bolumler[0]
        self.assertEqual(ilk.find(f"{K}doi_data/{K}resource").text, "https://vizetek.com.tr/urun/ornek")
        self.assertEqual((ilk.find(f"{K}pages/{K}first_page").text, ilk.find(f"{K}pages/{K}last_page").text), ("5", "7"))
        kisi = ilk.find(f"{K}contributors/{K}person_name")
        self.assertEqual([c.tag.split("}")[1] for c in kisi], ["given_name", "surname", "affiliations", "ORCID"])
        self.assertEqual(kisi.find(f"{K}ORCID").text, "https://orcid.org/0000-0002-1825-0097")
        self.assertEqual([c.tag.split("}")[1] for c in ilk], ["contributors", "titles", "component_number",
                                                              "publication_date", "pages", "doi_data"])

    def test_telif_bolume_kitap_yazari(self):
        telif = kayit(kitap__tur="telif", kitap__kisiler=[dict(KISI, rol="yazar")])
        for b in telif["bolumler"]:
            b["kisiler"] = []
        kok = ET.fromstring(xml_uret(telif, "20261119220000").encode("utf-8"))
        self.assertEqual(kok.find(f"{K}body/{K}book").get("book_type"), "monograph")
        bolum_kisi = kok.find(f"{K}body/{K}book/{K}content_item/{K}contributors/{K}person_name/{K}surname")
        self.assertEqual(bolum_kisi.text, "Yılmaz")


class Sorgu(unittest.TestCase):
    CR = {"title": ["Eğitimde Güncel Yaklaşımlar"], "abstract": "<jats:p>Crossref özeti.</jats:p>",
          "resource": {"primary": {"URL": "https://vizetek.com.tr/urun/eski"}}, "ISBN": ["9780000000002"],
          "isbn-type": [{"type": "electronic", "value": "9780000000002"}], "published": {"date-parts": [[2026, 10, 28]]},
          "author": [{"family": "Yılmaz"}], "editor": [{"family": "Meşe Yavuz", "ORCID": "https://orcid.org/0000-0002-8079-1230"}]}

    def test_karsilastir_ve_doldur(self):
        k = kayit(kitap__ozet="", kitap__adres="[DOLDUR: adres]", kitap__isbn_elektronik="",
                  kitap__yayim_tarihi="[DOLDUR]", kitap__kisiler__0__orcid="")["kitap"]
        alanlar = [a for a, _ in karsilastir(k, self.CR)]
        self.assertEqual(alanlar, ["özet", "adres", "ISBN", "kişiler"])
        degisen = doldur(k, self.CR)
        self.assertEqual(degisen, ["özet", "adres", "isbn_elektronik", "yayım tarihi", "ORCID (Meşe Yavuz)"])
        self.assertEqual((k["ozet"], k["yayim_tarihi"]), ("Crossref özeti.", "2026-10-28"))

    def test_gecersiz_doi_istek_atmaz(self):
        self.assertEqual(crossref_kaydi("10.54637/x y?a=1"), ("hata: DOI biçimi geçersiz", None))

    def test_ornek_kayit_sablonu(self):
        ornek = json.loads((ARACLAR / "sablon" / "kayit-ornegi.json").read_text(encoding="utf-8"))
        self.assertEqual(set(ornek), set(KAYIT))
        self.assertEqual(set(ornek["kitap"]), set(KAYIT["kitap"]))
        self.assertEqual(set(ornek["bolumler"][0]), set(KAYIT["bolumler"][0]))
        self.assertTrue(doldur_yerleri(ornek))


if __name__ == "__main__":
    unittest.main()
