import sys
from pathlib import Path

import pytest
from docx import Document
from docx.shared import Pt

RAIZ_HERRAMIENTA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_HERRAMIENTA))


def _tabla(doc, filas):
    t = doc.add_table(rows=len(filas), cols=len(filas[0]))
    for i, fila in enumerate(filas):
        for j, texto in enumerate(fila):
            t.cell(i, j).text = texto
    return t


@pytest.fixture
def doc_prueba():
    doc = Document()
    doc.add_paragraph("Nombre del proyecto: ________")
    doc.add_paragraph("Limitaciones:")
    doc.add_paragraph("__________")
    t0 = _tabla(doc, [["Campo", "Información"], ["Ficha", ""]])
    run = t0.cell(1, 1).paragraphs[0].add_run("x")
    run.bold = True
    run.font.size = Pt(9)
    _tabla(doc, [["ID", "Nombre", "Estado"], ["RF-001", "", "Propuesto"], ["RF-002", "", ""]])
    _tabla(doc, [["Campo", "Contenido"], ["ID y nombre", "CU-___"]])
    doc.add_paragraph("entre tablas")
    _tabla(doc, [["Paso", "Acción"], ["1", ""]])
    return doc
