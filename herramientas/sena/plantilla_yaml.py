"""Carga de YAML de contenido, sustitución de marcadores {{...}} y expansión {{todas: ...}}."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

MARCADOR = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")
TODAS = re.compile(r"^\{\{\s*todas:\s*(\w+)\s*\}\}$")
CAMPO_SIMPLE = re.compile(r"(?<!\{)\{(\w+)\}(?!\})")
COLECCION_POR_PREFIJO = {"rf": "requisitos", "hu": "historias", "cu": "casos_uso"}


def cargar_yaml(ruta: Path) -> Any:
    with open(ruta, encoding="utf-8") as f:
        return yaml.safe_load(f)


def cargar_contexto(dir_contenido: Path) -> dict:
    return {
        "comun": cargar_yaml(dir_contenido / "comun.yaml"),
        "catalogo": cargar_yaml(dir_contenido / "catalogo.yaml"),
    }


def _valor_marcador(marcador: str, ctx: dict) -> str:
    prefijo, _, resto = marcador.partition(".")
    try:
        if prefijo == "comun":
            valor: Any = ctx["comun"]
            for parte in resto.split("."):
                valor = valor[parte]
            return str(valor)
        if prefijo in COLECCION_POR_PREFIJO:
            item = ctx["catalogo"][COLECCION_POR_PREFIJO[prefijo]][resto]
            return f"{resto} — {item['nombre']}"
    except (KeyError, TypeError):
        pass
    raise KeyError(f"Marcador desconocido: {{{{{marcador}}}}}")


def resolver(valor: Any, ctx: dict) -> Any:
    if isinstance(valor, str):
        return MARCADOR.sub(lambda m: _valor_marcador(m.group(1), ctx), valor)
    if isinstance(valor, list):
        return [resolver(v, ctx) for v in valor]
    if isinstance(valor, dict):
        return {k: resolver(v, ctx) for k, v in valor.items()}
    if valor is None:
        return ""
    return str(valor)


def _texto(v: Any) -> str:
    if isinstance(v, list):
        return ", ".join(str(x) for x in v) if v else "—"
    if v is None or v == "":
        return "—"
    return str(v)


def _hu_de_rf(cat: dict) -> dict[str, str]:
    return {h["rf"]: hid for hid, h in cat.get("historias", {}).items()}


def _cu_de_hu(cat: dict, hu: str) -> list[str]:
    return sorted(cid for cid, c in cat.get("casos_uso", {}).items() if hu in c.get("hu", []))


def campos_item(coleccion: str, id_: str, cat: dict) -> dict[str, str]:
    item = cat[coleccion][id_]
    campos: dict[str, Any] = dict(item) if isinstance(item, dict) else {"texto": item}
    campos["id"] = id_
    if coleccion == "reglas":
        campos["rf_que_citan"] = sorted(
            rid for rid, r in cat.get("requisitos", {}).items() if id_ in r.get("rn", [])
        )
    elif coleccion == "requisitos":
        hu = _hu_de_rf(cat).get(id_, "")
        campos["hu"] = hu
        campos["cu"] = _cu_de_hu(cat, hu)
    elif coleccion == "historias":
        for k, v in cat.get("requisitos", {}).get(item["rf"], {}).items():
            campos.setdefault(k if k != "nombre" else "rf_nombre", v)
        campos["cu"] = _cu_de_hu(cat, id_)
    return {k: _texto(v) for k, v in campos.items()}


def expandir_todas(entrada: dict, ctx: dict) -> list[list[str]]:
    filas = entrada.get("filas")
    if not (isinstance(filas, list) and len(filas) == 1 and isinstance(filas[0], str)):
        return filas
    m = TODAS.match(filas[0].strip())
    if not m:
        return filas
    coleccion = m.group(1)
    cat = ctx["catalogo"]
    resultado = []
    for id_ in sorted(cat[coleccion]):
        campos = campos_item(coleccion, id_, cat)
        resultado.append(
            [CAMPO_SIMPLE.sub(lambda c: campos[c.group(1)], col) for col in entrada["columnas"]]
        )
    return resultado
