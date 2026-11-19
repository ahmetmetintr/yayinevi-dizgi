#!/usr/bin/env python3
"""Eğitim sayfasını üretir.

Girdi:  egitim/sayfa.html (sayfa iskeleti) · egitim/promptlar/*.md · eklenti/.claude-plugin/plugin.json
Çıktı:  cikti/dizgi-egitimi.html — elle düzenlenmez, her değişiklikten sonra yeniden üretilir.
Kullanım: python3 egitim/uret.py

İşaretler: {{KART:KOD|Başlık|Açıklama}} prompt kartı · {{KOMUT:kimlik::etiket::komut}} terminal kutusu ·
{{P:KOD}} promptlar/KOD-*.md içeriği · {{SURUM}} eklentinin sürümü. Her prompt sayfada tam bir kez kullanılır.
"""
import html
import json
import re
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
PROMPTLAR = KOK / "egitim" / "promptlar"
SABLON = KOK / "egitim" / "sayfa.html"
EKLENTI = KOK / "eklenti" / ".claude-plugin" / "plugin.json"
CIKTI = KOK / "cikti" / "dizgi-egitimi.html"

KART = """<article class="kart" id="{kod}"><span class="kesim"></span>
  <div class="kart-bas"><span class="kod">{kod}</span><h3>{baslik}</h3>
    <label class="tik-etiket"><input type="checkbox" class="tik" data-kod="{kod}"> Yapıldı</label></div>
  <p class="ne-zaman">{aciklama}</p>
  <div class="metin-kutu"><div class="arac-cubugu"><span class="etiket">Prompt · Claude Code</span><div class="dugmeler"><button class="kopyala" data-hedef="p-{kod}">Kopyala</button></div></div><pre id="p-{kod}">{{{{P:{kod}}}}}</pre></div>
</article>"""
KOMUT = """<div class="metin-kutu"><div class="arac-cubugu"><span class="etiket">{etiket}</span><div class="dugmeler"><button class="kopyala" data-hedef="{kimlik}">Kopyala</button></div></div><pre id="{kimlik}">{komut}</pre></div>"""


def main():
    sayfa = SABLON.read_text(encoding="utf-8")
    kullanilan = []
    sayfa = re.sub(r"\{\{KART:([^|}]+)\|([^|}]+)\|([^}]+)\}\}",
                   lambda e: KART.format(kod=e.group(1), baslik=e.group(2), aciklama=e.group(3)), sayfa)
    sayfa = re.sub(r"\{\{KOMUT:(.+?)::(.+?)::(.+?)\}\}",
                   lambda e: KOMUT.format(kimlik=e.group(1), etiket=e.group(2), komut=html.escape(e.group(3), quote=False)), sayfa)

    def prompt(e):
        adaylar = list(PROMPTLAR.glob(f"{e.group(1)}-*.md"))
        if len(adaylar) != 1:
            sys.exit(f"{e.group(1)}: tek prompt dosyası bekleniyordu, bulunan {len(adaylar)}")
        kullanilan.append(adaylar[0].name)
        return html.escape(adaylar[0].read_text(encoding="utf-8").rstrip() + "\n", quote=False)

    sayfa = re.sub(r"\{\{P:([A-Z]\d+[a-z]?)\}\}", prompt, sayfa)
    sayfa = sayfa.replace("{{SURUM}}", json.loads(EKLENTI.read_text(encoding="utf-8"))["version"])
    eksik = sorted({p.name for p in PROMPTLAR.glob("*.md")} - set(kullanilan))
    cift = sorted({k for k in kullanilan if kullanilan.count(k) > 1})
    if eksik or cift or "{{" in sayfa:
        sys.exit(f"Sayfada kullanılmayan prompt: {eksik} · iki kez kullanılan: {cift} · artık işaret: {'{{' in sayfa}")
    CIKTI.parent.mkdir(exist_ok=True)
    CIKTI.write_text(sayfa, encoding="utf-8")
    print(f"Üretildi: {CIKTI.relative_to(KOK)} ({len(sayfa.encode()) // 1024} KB, {len(kullanilan)} prompt)")


if __name__ == "__main__":
    main()
