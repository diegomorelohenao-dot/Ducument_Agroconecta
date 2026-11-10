"""Genera los documentos SENA llenos a partir de las plantillas y los YAML de contenido.

Uso: python -X utf8 generar.py [formulacion|gestion|requisitos|backlog|todos]
"""
from __future__ import annotations

import sys
from pathlib import Path

from docx import Document

import docx_ops
from plantilla_yaml import cargar_contexto, cargar_yaml, expandir_todas, resolver

RAIZ = Path(__file__).resolve().parents[2]
CONTENIDO = RAIZ / "docs" / "sena" / "contenido"
PLANTILLAS = RAIZ / "docs" / "sena" / "plantillas"
ENTREGABLES = RAIZ / "docs" / "sena" / "entregables"
DOCUMENTOS = ["formulacion", "gestion", "requisitos", "backlog"]


def _aplicar(t, op: dict, ctx: dict) -> None:
    if "campos" in op:
        docx_ops.llenar_campos(t, resolver(op["campos"], ctx))
    elif "filas" in op:
        filas = resolver(expandir_todas(op, ctx), ctx)
        encabezado = resolver(op.get("nuevo_encabezado"), ctx) if op.get("nuevo_encabezado") else None
        docx_ops.reemplazar_filas(t, filas, encabezado)
    elif "agregar" in op:
        docx_ops.agregar_filas(t, resolver(op["agregar"], ctx))
    else:
        raise ValueError(f"Operación sin campos/filas/agregar: {op}")


def _pedir_actualizar_campos(doc) -> None:
    """Hace que Word actualice la tabla de contenido al abrir (las páginas cambian al llenar)."""
    from docx.oxml.ns import qn

    settings = doc.settings.element
    if settings.find(qn("w:updateFields")) is None:
        el = settings.makeelement(qn("w:updateFields"), {qn("w:val"): "true"})
        settings.append(el)


def generar_documento(yaml_doc: Path, dir_plantillas: Path, dir_salida: Path, ctx: dict) -> Path:
    datos = cargar_yaml(yaml_doc)
    doc, _ = construir(datos, dir_plantillas, ctx)
    dir_salida.mkdir(parents=True, exist_ok=True)
    salida = dir_salida / datos["salida"]
    doc.save(salida)
    return salida


def construir(datos: dict, dir_plantillas: Path, ctx: dict):
    """Devuelve (documento lleno, tablas que se llenaron)."""
    doc = Document(dir_plantillas / datos["plantilla"])

    # 1) Resolver TODAS las tablas por índice original antes de modificar nada.
    entradas = [(docx_ops.tabla(doc, e["indice"], e["encabezado"]), e) for e in datos.get("tablas", [])]
    grupos = []
    for g in datos.get("grupos", []):
        originales = [
            docx_ops.tabla(doc, i, enc) for i, enc in zip(g["tablas"], g["encabezados"])
        ]
        grupos.append((g, originales))

    # 2) Clonar bloques (en orden inverso para que queden instancia 1, 2, 3...).
    planes = []
    for g, originales in grupos:
        instancias = g["instancias"]
        bloques = [originales]
        clones = [docx_ops.clonar_bloque(originales[0], originales[-1]) for _ in instancias[1:]]
        bloques += list(reversed(clones))
        for bloque, instancia in zip(bloques, instancias):
            for indice, t in zip(g["tablas"], bloque):
                op = instancia.get(indice)
                if op:
                    planes.append((t, op))

    # 3) Llenar.
    for t, op in entradas + planes:
        _aplicar(t, op, ctx)
    for linea in datos.get("lineas", []):
        docx_ops.rellenar_linea(doc, linea["etiqueta"], resolver(linea["valor"], ctx))
    for img in datos.get("imagenes", []):
        docx_ops.insertar_imagen_despues_de(doc, img["despues_de"], RAIZ / img["ruta"], img["ancho_cm"])
    _pedir_actualizar_campos(doc)
    return doc, [t for t, _ in entradas + planes]


def main(argv: list[str]) -> int:
    objetivo = argv[1] if len(argv) > 1 else "todos"
    nombres = DOCUMENTOS if objetivo == "todos" else [objetivo]
    ctx = cargar_contexto(CONTENIDO)
    for nombre in nombres:
        salida = generar_documento(CONTENIDO / f"{nombre}.yaml", PLANTILLAS, ENTREGABLES, ctx)
        print(f"Generado: {salida.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
