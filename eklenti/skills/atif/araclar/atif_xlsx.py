"""Küçük XLSX yazıcı (atıf dizini skill'i): yalnız Python'un standart kitaplığı, ek paket gerekmez.

Her sayfada kalın ve dondurulmuş başlık satırı, süzgeç, sütun genişlikleri; hücreler metin ya da tam sayı.
Aynı girdiden bayt bayt aynı dosya çıkar (zip içindeki tarihler sabit).
"""
import re
import zipfile
from xml.sax.saxutils import escape

YASAK = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")
SABIT_TARIH = (1980, 1, 1, 0, 0, 0)
NS = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
NS_R = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
BELGE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
TUR = "application/vnd.openxmlformats-officedocument.spreadsheetml"

STILLER = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet {NS}><fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts>
<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FFE7E6E6"/><bgColor indexed="64"/></patternFill></fill></fills>
<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/></cellXfs>
<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>"""


def sutun(n):
    """0 → A, 25 → Z, 26 → AA."""
    harf = ""
    n += 1
    while n:
        n, kalan = divmod(n - 1, 26)
        harf = chr(65 + kalan) + harf
    return harf


def hucre(ref, deger, kalin=False):
    stil = ' s="1"' if kalin else ""
    if isinstance(deger, int) and not isinstance(deger, bool):
        return f'<c r="{ref}"{stil}><v>{deger}</v></c>'
    metin = escape(YASAK.sub("", "" if deger is None else str(deger)))[:32767]
    return f'<c r="{ref}" t="inlineStr"{stil}><is><t xml:space="preserve">{metin}</t></is></c>'


def sayfa_xml(basliklar, satirlar, genislikler):
    son = f"{sutun(len(basliklar) - 1)}{len(satirlar) + 1}"
    sutunlar = "".join(f'<col min="{i + 1}" max="{i + 1}" width="{g}" customWidth="1"/>'
                       for i, g in enumerate(genislikler))
    govde = [f'<row r="1">' + "".join(hucre(f"{sutun(i)}1", b, True) for i, b in enumerate(basliklar)) + "</row>"]
    for r, satir in enumerate(satirlar, 2):
        govde.append(f'<row r="{r}">' + "".join(hucre(f"{sutun(i)}{r}", d) for i, d in enumerate(satir)) + "</row>")
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<worksheet {NS} {NS_R}>'
            f'<dimension ref="A1:{son}"/><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" '
            f'activePane="bottomLeft" state="frozen"/></sheetView></sheetViews><sheetFormatPr defaultRowHeight="15"/>'
            f'<cols>{sutunlar}</cols><sheetData>{"".join(govde)}</sheetData><autoFilter ref="A1:{son}"/></worksheet>')


def xlsx_yaz(yol, sayfalar):
    """sayfalar: [(ad, başlıklar, satırlar, genişlikler)]; ad en çok 31 karakter, []:*?/\\ içermez."""
    adlar = [re.sub(r"[\[\]:*?/\\]", " ", ad)[:31] for ad, _, _, _ in sayfalar]
    kitap = "".join(f'<sheet name="{escape(a)}" sheetId="{i}" r:id="rId{i}"/>' for i, a in enumerate(adlar, 1))
    suzgec = "".join(f'<definedName name="_xlnm._FilterDatabase" localSheetId="{i}" hidden="1">'
                     f"'{escape(a)}'!$A$1:${sutun(len(b) - 1)}${len(s) + 1}</definedName>"
                     for i, (a, (_, b, s, _)) in enumerate(zip(adlar, sayfalar)))
    dosyalar = {
        "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Types xmlns="http://'
        'schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/'
        'vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
        f'<Override PartName="/xl/workbook.xml" ContentType="{TUR}.sheet.main+xml"/>'
        f'<Override PartName="/xl/styles.xml" ContentType="{TUR}.styles+xml"/>'
        + "".join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="{TUR}.worksheet+xml"/>'
                  for i in range(1, len(sayfalar) + 1)) + "</Types>",
        "_rels/.rels": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://'
        'schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" '
        f'Type="{BELGE}/officeDocument" Target="xl/workbook.xml"/></Relationships>',
        "xl/workbook.xml": f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<workbook {NS} {NS_R}>'
        f"<sheets>{kitap}</sheets><definedNames>{suzgec}</definedNames></workbook>",
        "xl/_rels/workbook.xml.rels": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships '
        'xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(f'<Relationship Id="rId{i}" Type="{BELGE}/worksheet" Target="worksheets/sheet{i}.xml"/>'
                  for i in range(1, len(sayfalar) + 1))
        + f'<Relationship Id="rId{len(sayfalar) + 1}" Type="{BELGE}/styles" Target="styles.xml"/></Relationships>',
        "xl/styles.xml": STILLER,
    }
    for i, (_, basliklar, satirlar, genislikler) in enumerate(sayfalar, 1):
        dosyalar[f"xl/worksheets/sheet{i}.xml"] = sayfa_xml(basliklar, satirlar, genislikler)
    with zipfile.ZipFile(yol, "w", zipfile.ZIP_DEFLATED) as z:
        for ad, icerik in dosyalar.items():
            bilgi = zipfile.ZipInfo(ad, SABIT_TARIH)
            bilgi.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(bilgi, icerik.encode("utf-8"))
