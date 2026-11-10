"""Validaciones de la documentación SENA (V1–V5) y generación de PENDIENTES.md.

Uso: python -X utf8 validar.py   (sale con código 1 si hay errores)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Iterable

from generar import CONTENIDO, DOCUMENTOS, PLANTILLAS, RAIZ, construir
from plantilla_yaml import cargar_contexto, cargar_yaml

ID = re.compile(r"\b(?:OBJ|IND|STK|ACT|ALC|EXC|RSK)-\d{2}\b|\b(?:EP|FEAT|RF|RNF|RN|HU|CU)-\d{3}\b")
PENDIENTE = re.compile(r"\[PENDIENTE:[^\]]*\]")
COLECCIONES = [
    "objetivos", "indicadores", "interesados", "actores", "epicas", "funcionalidades",
    "requisitos", "rnf", "reglas", "historias", "casos_uso", "alcance", "exclusiones", "riesgos",
]
RESIDUOS = [
    "___", "A/M/B", "Sí / No", "Alta / Media / B", "Propuesto / ", "novia", "Directo / Indire",
    "Corto / Medio", "Verde / Amarillo", "Evitar / Mitigar", "Viable / Condici", "Disponible / Par",
    "Técnica / Tempor", "Restricción / Su", "Humano / sistema", "Público / intern", "API / archivo",
    "Inspección / dem", "Dato / Servicio", "Interna / extern", "Éxito / error", "Semanal / por hi",
    "Reunión / correo", "Decide / propone", "Cliente / usuari", "Desconoce / Neut",
    "Líder / análisis", "Web / Móvil", "MVP / posterior", "Debe / no debe", "Crítica / mayor",
    "Técnico / gestió", "Aprobar / rechaz", "Alcance / tiempo", "HU / CU / RF / U",
]


def _cadenas(valor: Any) -> Iterable[str]:
    if isinstance(valor, str):
        yield valor
    elif isinstance(valor, dict):
        for k, v in valor.items():
            yield from _cadenas(k)
            yield from _cadenas(v)
    elif isinstance(valor, list):
        for v in valor:
            yield from _cadenas(v)


def ids_citados(texto: str) -> set[str]:
    return set(ID.findall(texto))


def ids_catalogo(cat: dict) -> set[str]:
    return {i for c in COLECCIONES for i in cat.get(c, {})}


def v1_ids_existen(contenidos: dict[str, Any], catalogo: dict) -> list[str]:
    conocidos = ids_catalogo(catalogo)
    errores = []
    for nombre, datos in contenidos.items():
        citados = set().union(*(ids_citados(s) for s in _cadenas(datos)))
        errores += [f"{nombre}: {i} no existe en el catálogo" for i in sorted(citados - conocidos)]
    return errores


def v2_consistencia_catalogo(cat: dict) -> list[str]:
    e = []
    rfs, hus = cat.get("requisitos", {}), cat.get("historias", {})
    epicas, feats = cat.get("epicas", {}), cat.get("funcionalidades", {})
    for fid, f in feats.items():
        if f.get("epica") not in epicas:
            e.append(f"{fid}: épica {f.get('epica')} inexistente")
    for rid, r in rfs.items():
        if r.get("epica") not in epicas:
            e.append(f"{rid}: épica {r.get('epica')} inexistente")
        if r.get("feat") not in feats:
            e.append(f"{rid}: funcionalidad {r.get('feat')} inexistente")
        elif feats[r["feat"]].get("epica") != r.get("epica"):
            e.append(f"{rid}: su FEAT pertenece a otra épica")
        for rn in r.get("rn", []):
            if rn not in cat.get("reglas", {}):
                e.append(f"{rid}: regla {rn} inexistente")
        hu = "HU-" + rid.split("-")[1]
        if hu not in hus:
            e.append(f"{rid}: falta la historia {hu}")
    for hid, h in hus.items():
        esperado = "RF-" + hid.split("-")[1]
        if h.get("rf") != esperado:
            e.append(f"{hid}: debe corresponder a {esperado}")
        elif h.get("nombre") != rfs.get(esperado, {}).get("nombre"):
            e.append(f"{hid}: el nombre debe ser igual al de {esperado}")
    citadas = {rn for r in rfs.values() for rn in r.get("rn", [])}
    for rn in cat.get("reglas", {}):
        if rn not in citadas:
            e.append(f"{rn}: ningún RF la cita")
    for cid, c in cat.get("casos_uso", {}).items():
        for hu in c.get("hu", []):
            if hu not in hus:
                e.append(f"{cid}: cita {hu}, que no existe")
    return e


def v3_residuos(tablas) -> list[str]:
    errores = []
    for n, t in enumerate(tablas):
        for fila in t.rows:
            for celda in fila.cells:
                for patron in RESIDUOS:
                    if patron in celda.text:
                        errores.append(f"tabla llenada #{n}: residuo '{patron}' en '{celda.text[:50]}'")
    return sorted(set(errores))


def v4_pendientes(dir_contenido: Path) -> dict[str, list[str]]:
    resultado = {}
    for ruta in sorted(dir_contenido.glob("*.yaml")):
        encontrados = []
        for s in _cadenas(cargar_yaml(ruta)):
            for p in PENDIENTE.findall(s):
                if p not in encontrados:
                    encontrados.append(p)
        if encontrados:
            resultado[ruta.name] = encontrados
    return resultado


def v5_criterios_por_historia(backlog: dict, catalogo: dict) -> list[str]:
    filas = next((t["filas"] for t in backlog.get("tablas", []) if t.get("indice") == 18), [])
    errores = []
    for hu in sorted(catalogo.get("historias", {})):
        propias = [f for f in filas if f[1] == hu]
        if len(propias) < 2:
            errores.append(f"{hu}: tiene {len(propias)} criterios de aceptación (mínimo 2)")
        elif not any(str(f[3]).startswith("Error") for f in propias):
            errores.append(f"{hu}: ningún criterio de tipo Error")
    return errores


def escribir_pendientes(pendientes: dict[str, list[str]], ruta: Path) -> None:
    lineas = [
        "# Pendientes de la documentación SENA",
        "",
        "Generado por `herramientas/sena/validar.py`. El equipo debe completar estos datos",
        "en los YAML de `docs/sena/contenido/` y regenerar antes del 2026-12-04.",
        "",
    ]
    for archivo, items in pendientes.items():
        lineas.append(f"## {archivo}")
        lineas += [f"- {i}" for i in items]
        lineas.append("")
    lineas += [
        "## Fuera de los YAML (se completan a mano en Word)",
        "- Listas de verificación (columna «Cumple»), registros de aprobación y firmas.",
        "- Actualizar la tabla de contenido (clic derecho → Actualizar campos).",
        "",
    ]
    ruta.write_text("\n".join(lineas), encoding="utf-8")


def main() -> int:
    ctx = cargar_contexto(CONTENIDO)
    cat = ctx["catalogo"]
    contenidos = {f"{d}.yaml": cargar_yaml(CONTENIDO / f"{d}.yaml") for d in DOCUMENTOS
                  if (CONTENIDO / f"{d}.yaml").exists()}
    errores = v1_ids_existen(contenidos, cat) + v2_consistencia_catalogo(cat)
    for nombre, datos in contenidos.items():
        _, llenadas = construir(datos, PLANTILLAS, ctx)
        errores += [f"{nombre}: {e}" for e in v3_residuos(llenadas)]
    if "backlog.yaml" in contenidos:
        errores += v5_criterios_por_historia(contenidos["backlog.yaml"], cat)
    pendientes = v4_pendientes(CONTENIDO)
    escribir_pendientes(pendientes, RAIZ / "docs" / "sena" / "PENDIENTES.md")
    for e in errores:
        print(f"ERROR {e}")
    total = sum(len(v) for v in pendientes.values())
    print(f"{len(errores)} errores · {total} pendientes (ver docs/sena/PENDIENTES.md)")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
