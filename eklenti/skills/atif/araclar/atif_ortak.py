"""Atıf dizini becerisinin ortak yardımcıları: Türkçe küçük harf, başlık anahtarı, dizin dosyasını okuma ve yazma.

atif_kaynakca.py, atif_yapi.py, atif_hazirla.py ve atif_uret.py bu modülü içe aktarır. Saat ve ağ kullanmaz.
Dizin dosyasının (atif-dizini/dizin.json) biçimi: sablon/dizin-ornegi.json.
"""
import json
import re
from pathlib import Path

SURUM = 1
KAYNAKCA_BASLIKLARI = {"kaynakça", "kaynakca", "kaynaklar", "kaynakçalar", "yararlanılan kaynaklar",
                       "başvurulan kaynaklar", "references", "bibliography", "referanslar"}
ON_SON = {"ön söz", "önsöz", "takdim", "takdim yazıları", "içindekiler", "katkıda bulunanlar", "dizin", "dizinler",
          "editörden", "sunuş", "teşekkür", "yazarlar hakkında", "editörler hakkında", "kısaltmalar", "sözlük",
          "sözlükçe", "künye", "iç kapak", "bilim kurulu", "hakem kurulu", "ekler", "hızlı başvuru haritası",
          "contents", "preface", "index"} | KAYNAKCA_BASLIKLARI
AYLAR = ["ocak", "şubat", "mart", "nisan", "mayıs", "haziran", "temmuz", "ağustos", "eylül", "ekim", "kasım", "aralık"]


def tr_kucuk(metin):
    return metin.replace("I", "ı").replace("İ", "i").lower()


def anahtar(baslik):
    """Başlığı karşılaştırmak için: baştaki numara ('5.', 'IV.'), sondaki dipnot işareti ve iki nokta atılır,
    Türkçe küçük harfe çevrilir. '5. KAYNAKÇA' → 'kaynakça', 'Ön Söz*' → 'ön söz'."""
    m = re.sub(r"^\s*(?:\d+(?:\.\d+)*|[IVXLC]+)[.):]?\s+", "", baslik.strip())
    m = re.sub(r"[\s*†‡:.¹²³⁴⁵⁶⁷⁸⁹⁰]+$", "", m)
    return " ".join(tr_kucuk(m).split())


def kaynakca_basligi_mi(metin):
    return len(metin) < 60 and anahtar(metin) in KAYNAKCA_BASLIKLARI


def dizin_oku(yol):
    yol = Path(yol)
    if not yol.exists():
        return {"surum": SURUM, "kitaplar": []}
    return json.loads(yol.read_text(encoding="utf-8-sig"))


def dizin_yaz(yol, dizin):
    """Kitaplar koda göre sıralı yazılır: aynı içerik her zaman aynı dosyayı verir."""
    dizin["kitaplar"].sort(key=lambda k: k["kod"])
    Path(yol).parent.mkdir(parents=True, exist_ok=True)
    Path(yol).write_text(json.dumps(dizin, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
