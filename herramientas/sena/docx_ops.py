"""Operaciones sobre plantillas .docx (python-docx) que conservan el formato original."""
from __future__ import annotations

import re
import unicodedata
from copy import deepcopy

from docx.document import Document
from docx.oxml.ns import qn
from docx.table import Table, _Cell

SUBRAYADO = re.compile(r"_{3,}")


class PlantillaCambiadaError(Exception):
    """La tabla de la plantilla no tiene el encabezado esperado."""


def normalizar(texto: str) -> str:
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )
    return " ".join(sin_tildes.lower().split())


def _encabezado_coincide(t: Table, encabezado: list[str]) -> bool:
    celdas = t.rows[0].cells
    if len(celdas) < len(encabezado):
        return False
    return all(normalizar(c.text).startswith(normalizar(e)) for c, e in zip(celdas, encabezado))


def tabla(doc: Document, indice: int, encabezado: list[str]) -> Table:
    tablas = doc.tables
    if indice >= len(tablas):
        raise PlantillaCambiadaError(f"T{indice}: no existe (la plantilla tiene {len(tablas)} tablas)")
    t = tablas[indice]
    if not _encabezado_coincide(t, encabezado):
        real = [c.text.strip()[:20] for c in t.rows[0].cells]
        raise PlantillaCambiadaError(f"T{indice}: se esperaba {encabezado}, hay {real}")
    return t


def _texto_run(r) -> str:
    return "".join(t.text or "" for t in r.findall(qn("w:t")))


def _rpr_con_texto(elemento, excluir=None):
    """rPr del primer run con texto visible dentro de `elemento`."""
    for r in elemento.iter(qn("w:r")):
        if excluir is not None and _dentro_de(r, excluir):
            continue
        rpr = r.find(qn("w:rPr"))
        if rpr is not None and _texto_run(r).strip():
            return rpr
    return None


def _dentro_de(el, ancestro) -> bool:
    while el is not None:
        if el is ancestro:
            return True
        el = el.getparent()
    return False


def _rpr_modelo(tc):
    """Formato a conservar: run con texto en la celda; si no, en otra celda de la fila;
    si no, en otra fila de datos (nunca el encabezado); si no, cualquier rPr de la celda."""
    rpr = _rpr_con_texto(tc)
    if rpr is not None:
        return rpr
    tr = tc.getparent()
    filas = [tr] + [f for f in tr.getparent().findall(qn("w:tr"))[1:] if f is not tr]
    for fila in filas:
        rpr = _rpr_con_texto(fila, excluir=tc)
        if rpr is not None:
            return rpr
    return next((r.find(qn("w:rPr")) for r in tc.iter(qn("w:r")) if r.find(qn("w:rPr")) is not None), None)


def escribir_celda(celda: _Cell, texto: str) -> None:
    tc = celda._tc
    parrafos = tc.findall(qn("w:p"))
    ppr = parrafos[0].find(qn("w:pPr"))
    rpr = _rpr_modelo(tc)
    for p in parrafos:
        tc.remove(p)
    for linea in str(texto).split("\n"):
        p = tc.makeelement(qn("w:p"), {})
        if ppr is not None:
            p.append(deepcopy(ppr))
        r = p.makeelement(qn("w:r"), {})
        if rpr is not None:
            r.append(deepcopy(rpr))
        t = r.makeelement(qn("w:t"), {})
        t.text = linea
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        r.append(t)
        p.append(r)
        tc.append(p)


def llenar_campos(t: Table, campos: dict[str, str | list[str]]) -> None:
    """Escribe en la última celda de la fila cuya primera celda empieza por la clave.
    Si el valor es una lista, llena las últimas len(lista) celdas."""
    for clave, valor in campos.items():
        objetivo = normalizar(clave)
        for tr in t._tbl.tr_lst:
            celdas = _celdas(tr, t)
            if normalizar(celdas[0].text).startswith(objetivo):
                valores = valor if isinstance(valor, list) else [valor]
                if len(valores) >= len(celdas):
                    raise ValueError(f"Campo '{clave}': {len(valores)} valores para {len(celdas)} celdas")
                for celda, texto in zip(celdas[-len(valores):], valores):
                    escribir_celda(celda, texto)
                break
        else:
            raise KeyError(f"Campo '{clave}' no encontrado en la tabla")


def _celdas(tr, t: Table) -> list[_Cell]:
    return [_Cell(tc, t) for tc in tr.tc_lst]


def _agregar_desde_prototipo(t: Table, prototipo, filas: list[list[str]]) -> None:
    n = len(prototipo.tc_lst)
    for fila in filas:
        if len(fila) != n:
            raise ValueError(f"La fila tiene {len(fila)} columnas y la tabla {n}: {fila}")
    for fila in filas:
        tr = deepcopy(prototipo)
        t._tbl.append(tr)
        for celda, texto in zip(_celdas(tr, t), fila):
            escribir_celda(celda, texto)


def reemplazar_filas(
    t: Table, filas: list[list[str]], nuevo_encabezado: list[str] | None = None
) -> None:
    trs = t._tbl.tr_lst
    prototipo = deepcopy(trs[1] if len(trs) > 1 else trs[0])
    n = len(prototipo.tc_lst)
    for fila in filas:
        if len(fila) != n:
            raise ValueError(f"La fila tiene {len(fila)} columnas y la tabla {n}: {fila}")
    if nuevo_encabezado is not None:
        celdas = _celdas(trs[0], t)
        if len(nuevo_encabezado) != len(celdas):
            raise ValueError("El nuevo encabezado no coincide con el número de columnas")
        for celda, texto in zip(celdas, nuevo_encabezado):
            escribir_celda(celda, texto)
    for tr in trs[1:]:
        t._tbl.remove(tr)
    _agregar_desde_prototipo(t, prototipo, filas)


def agregar_filas(t: Table, filas: list[list[str]]) -> None:
    _agregar_desde_prototipo(t, deepcopy(t._tbl.tr_lst[-1]), filas)


def _poner_texto_parrafo(p, valor: str) -> None:
    runs = p.runs
    for i, r in enumerate(runs):
        r.text = valor if i == 0 else ""


def rellenar_linea(doc: Document, etiqueta: str, valor: str) -> None:
    parrafos = doc.paragraphs
    objetivo = normalizar(etiqueta)
    for i, p in enumerate(parrafos):
        if not normalizar(p.text).startswith(objetivo):
            continue
        if SUBRAYADO.search(p.text):
            usado = False
            for r in p.runs:
                if SUBRAYADO.search(r.text):
                    reemplazo = "" if usado else valor
                    r.text = SUBRAYADO.sub("", SUBRAYADO.sub(lambda _: reemplazo, r.text, count=1))
                    usado = True
            if not usado:  # subrayado partido entre runs
                _poner_texto_parrafo(p, f"{etiqueta} {valor}")
            return
        for siguiente in parrafos[i + 1 :]:
            texto = siguiente.text.strip()
            if texto and set(texto) == {"_"}:
                _poner_texto_parrafo(siguiente, valor)
                return
            if texto:
                break
        break
    raise KeyError(f"Línea '{etiqueta}' no encontrada")


def clonar_bloque(primera: Table, ultima: Table) -> list[Table]:
    elementos = []
    el = primera._tbl
    while el is not None:
        elementos.append(el)
        if el is ultima._tbl:
            break
        el = el.getnext()
    else:
        raise ValueError("La última tabla no sigue a la primera en el documento")
    separador = ultima._tbl.makeelement(qn("w:p"), {})
    ultima._tbl.addnext(separador)  # Word fusiona tablas contiguas
    ancla = separador
    nuevas = []
    for original in elementos:
        copia = deepcopy(original)
        ancla.addnext(copia)
        ancla = copia
        if copia.tag == qn("w:tbl"):
            nuevas.append(Table(copia, primera._parent))
    return nuevas
