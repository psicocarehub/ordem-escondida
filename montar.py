"""Monta os PDFs das petições, com e sem comando escondido, e o texto extraído.

Técnicas (as mesmas dos casos reais):
  branco     o comando em fonte normal, branca sobre fundo branco
  minusculo  o comando em fonte de 0,8 pt, branca (caso do STJ, out/2026)

O comando entra logo depois dos pedidos, antes do fecho, como nas peças
punidas. O texto extraído sai do próprio PDF pelo pypdf, que é o caminho mais
comum de um sistema que lê PDF para mandar a um modelo de linguagem.

Confere ainda que o comando é invisível: a página renderizada com comando é
idêntica, pixel a pixel, à da peça de controle.

Uso: .venv/bin/python montar.py
"""

from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape

import pypdfium2 as pdfium
from pypdf import PdfReader
from reportlab.lib.colors import black, white
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate, Spacer

from casos import CASOS, Caso
from comandos import COMANDOS, Comando

RAIZ = Path(__file__).parent
DIR_PDF = RAIZ / "dados" / "pdf"
DIR_TXT = RAIZ / "dados" / "texto"

_FONTES = "/System/Library/Fonts/Supplemental/"
pdfmetrics.registerFont(TTFont("Times", _FONTES + "Times New Roman.ttf"))
pdfmetrics.registerFont(TTFont("Times-B", _FONTES + "Times New Roman Bold.ttf"))

CORPO = ParagraphStyle("corpo", fontName="Times", fontSize=12, leading=18, alignment=TA_JUSTIFY,
                       firstLineIndent=1.5 * cm, spaceAfter=8, textColor=black)
TITULO = ParagraphStyle("titulo", parent=CORPO, fontName="Times-B", firstLineIndent=0, alignment=TA_JUSTIFY)
SECAO = ParagraphStyle("secao", parent=CORPO, fontName="Times-B", firstLineIndent=0, spaceBefore=6)
FECHO = ParagraphStyle("fecho", parent=CORPO, firstLineIndent=0, alignment=TA_CENTER)
TECNICAS = {
    "branco": ParagraphStyle("branco", parent=CORPO, textColor=white, firstLineIndent=0),
    "minusculo": ParagraphStyle("minusculo", parent=CORPO, textColor=white, fontSize=0.8, leading=1.2,
                                firstLineIndent=0, spaceAfter=0),
}


class Oculto(Flowable):
    """Parágrafo de altura zero: desenha o comando sem empurrar o resto da página.

    Branco sobre branco e desenhado antes do texto que vem depois, ele nunca
    muda um pixel da página, mas fica na camada de texto do PDF.
    """

    def __init__(self, paragrafo: Paragraph):
        super().__init__()
        self.p = paragrafo

    def wrap(self, aw, ah):
        self.p.wrap(aw, ah)
        return aw, 0

    def draw(self):
        self.p.drawOn(self.canv, 0, -self.p.height)


def _paragrafos(texto: str) -> tuple[list[str], list[str]]:
    corpo, _, fecho = texto.partition("\n\nNestes termos")
    return [p for p in corpo.split("\n\n") if p.strip()], [p for p in ("Nestes termos" + fecho).split("\n\n") if p.strip()]


def _flow(caso: Caso, comando: Comando | None, tecnica: str | None) -> list:
    corpo, fecho = _paragrafos(caso.texto)
    flow: list = [Paragraph(escape(caso.juizo), TITULO), Spacer(1, 1.2 * cm)]
    for p in corpo:
        if p.startswith(("I.", "II.", "III.", "IV.", "V.")):
            flow.append(Paragraph(escape(p), SECAO))
        else:
            for linha in p.split("\n"):
                flow.append(Paragraph(escape(linha), CORPO))
    if comando is not None:
        flow.append(Oculto(Paragraph(escape(comando.texto), TECNICAS[tecnica])))
    for p in fecho:
        flow.append(Paragraph(escape(p).replace("\n", "<br/>"), FECHO))
    return flow


def _pdf(caminho: Path, caso: Caso, comando: Comando | None, tecnica: str | None) -> None:
    doc = SimpleDocTemplate(str(caminho), pagesize=A4, leftMargin=3 * cm, rightMargin=2 * cm,
                            topMargin=2.5 * cm, bottomMargin=2.5 * cm, title="Petição", author="",
                            creator="", producer="")
    doc.build(_flow(caso, comando, tecnica))


def _texto(caminho: Path) -> str:
    return "\n".join(p.extract_text() or "" for p in PdfReader(str(caminho)).pages)


def _pixels(caminho: Path) -> list[bytes]:
    pdf = pdfium.PdfDocument(str(caminho))
    return [pdf[i].render(scale=2).to_pil().tobytes() for i in range(len(pdf))]


def nome(caso_id: str, comando_id: str, tecnica: str) -> str:
    return f"{caso_id}__{comando_id}__{tecnica}"


def main() -> None:
    DIR_PDF.mkdir(parents=True, exist_ok=True)
    DIR_TXT.mkdir(parents=True, exist_ok=True)
    indice = []
    for caso in CASOS:
        controle = DIR_PDF / f"{nome(caso.id, 'controle', 'nenhuma')}.pdf"
        _pdf(controle, caso, None, None)
        (DIR_TXT / f"{controle.stem}.txt").write_text(_texto(controle), encoding="utf-8")
        ref = _pixels(controle)
        indice.append({"arquivo": controle.stem, "caso": caso.id, "comando": "controle", "tecnica": "nenhuma"})
        for comando in COMANDOS:
            for tecnica in TECNICAS:
                arq = DIR_PDF / f"{nome(caso.id, comando.id, tecnica)}.pdf"
                _pdf(arq, caso, comando, tecnica)
                txt = _texto(arq)
                (DIR_TXT / f"{arq.stem}.txt").write_text(txt, encoding="utf-8")
                # o texto extraído traz o comando (com quebras de linha onde o PDF quebrou)
                achatado, alvo = " ".join(txt.split()), " ".join(comando.texto.split())
                extraido = alvo in achatado
                pix = _pixels(arq)
                invisivel = len(pix) == len(ref) and all(a == b for a, b in zip(pix, ref))
                indice.append({"arquivo": arq.stem, "caso": caso.id, "comando": comando.id, "tecnica": tecnica,
                               "comando_no_texto_extraido": extraido, "pagina_identica_ao_controle": invisivel})
    (RAIZ / "dados" / "indice.json").write_text(json.dumps(indice, ensure_ascii=False, indent=1), encoding="utf-8")
    inj = [i for i in indice if i["comando"] != "controle"]
    print(f"{len(indice)} PDFs; comando no texto extraído: {sum(i['comando_no_texto_extraido'] for i in inj)}/{len(inj)}; "
          f"página idêntica ao controle: {sum(i['pagina_identica_ao_controle'] for i in inj)}/{len(inj)}")
    for i in inj:
        if not (i["comando_no_texto_extraido"] and i["pagina_identica_ao_controle"]):
            print("  falhou:", i)


if __name__ == "__main__":
    main()
