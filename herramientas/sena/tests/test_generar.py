import hashlib

import pytest
import yaml
from docx import Document

from generar import generar_documento
from plantilla_yaml import expandir_todas, resolver


@pytest.fixture
def ctx_prueba():
    return {
        "comun": {"ficha": "3045678", "integrantes": {"EQ-01": "Ana"}},
        "catalogo": {
            "requisitos": {
                "RF-002": {"nombre": "Iniciar sesión", "rn": ["RN-001"]},
                "RF-001": {"nombre": "Registrar usuario", "rn": []},
            },
            "historias": {"HU-001": {"nombre": "Registrar usuario", "rf": "RF-001"}},
            "casos_uso": {"CU-001": {"nombre": "Realizar pedido", "hu": ["HU-001"]}},
            "reglas": {"RN-001": {"nombre": "Verificado", "texto": "Solo verificados"}},
        },
    }


@pytest.fixture
def plantilla_prueba(tmp_path, doc_prueba):
    d = tmp_path / "plantillas"
    d.mkdir()
    ruta = d / "prueba.docx"
    doc_prueba.save(ruta)
    return ruta


def _yaml(tmp_path, datos):
    ruta = tmp_path / "doc.yaml"
    ruta.write_text(yaml.safe_dump(datos, allow_unicode=True), encoding="utf-8")
    return ruta


def _hash(ruta):
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def test_genera_y_no_toca_plantilla(tmp_path, plantilla_prueba, ctx_prueba):
    antes = _hash(plantilla_prueba)
    y = _yaml(tmp_path, {
        "plantilla": "prueba.docx",
        "salida": "salida.docx",
        "lineas": [{"etiqueta": "Nombre del proyecto:", "valor": "AgroConecta"}],
        "tablas": [{"indice": 0, "encabezado": ["Campo"], "campos": {"Ficha": "{{comun.ficha}}"}}],
    })
    salida = generar_documento(y, plantilla_prueba.parent, tmp_path / "out", ctx_prueba)
    assert _hash(plantilla_prueba) == antes
    d = Document(salida)
    assert d.tables[0].cell(1, 1).text == "3045678"
    assert "Nombre del proyecto: AgroConecta" in [p.text for p in d.paragraphs]


def test_resolver_marcadores(ctx_prueba):
    assert resolver("{{rf.RF-001}} / {{comun.ficha}}", ctx_prueba) == "RF-001 — Registrar usuario / 3045678"
    assert resolver({"a": ["{{comun.integrantes.EQ-01}}"]}, ctx_prueba) == {"a": ["Ana"]}


def test_resolver_ruta_del_catalogo(ctx_prueba):
    assert resolver("{{catalogo.reglas.RN-001.texto}}", ctx_prueba) == "Solo verificados"


def test_marcador_desconocido_falla(ctx_prueba):
    with pytest.raises(KeyError, match="comun.nada"):
        resolver("{{comun.nada}}", ctx_prueba)


def test_expandir_todas(ctx_prueba):
    filas = expandir_todas({"filas": ["{{todas: requisitos}}"], "columnas": ["{id}", "{nombre}"]}, ctx_prueba)
    assert filas == [["RF-001", "Registrar usuario"], ["RF-002", "Iniciar sesión"]]


def test_campos_calculados(ctx_prueba):
    reglas = expandir_todas({"filas": ["{{todas: reglas}}"], "columnas": ["{id}", "{rf_que_citan}"]}, ctx_prueba)
    assert reglas == [["RN-001", "RF-002"]]
    rf = expandir_todas({"filas": ["{{todas: requisitos}}"], "columnas": ["{id}", "{hu}", "{cu}", "{rn}"]}, ctx_prueba)
    assert rf[0] == ["RF-001", "HU-001", "CU-001", "—"]
    hu = expandir_todas({"filas": ["{{todas: historias}}"], "columnas": ["{id}", "{rf}", "{cu}"]}, ctx_prueba)
    assert hu == [["HU-001", "RF-001", "CU-001"]]


def test_imagenes_del_yaml(tmp_path, plantilla_prueba, ctx_prueba):
    from test_docx_ops import _png_minimo

    png = _png_minimo(tmp_path / "d.png")
    y = _yaml(tmp_path, {
        "plantilla": "prueba.docx", "salida": "salida.docx",
        "imagenes": [{"despues_de": "Limitaciones:", "ruta": str(png), "ancho_cm": 8}],
    })
    d = Document(generar_documento(y, plantilla_prueba.parent, tmp_path / "out", ctx_prueba))
    assert len(d.inline_shapes) == 1


def test_salida_pide_actualizar_campos(tmp_path, plantilla_prueba, ctx_prueba):
    # la tabla de contenido cambia de páginas al llenar; Word la actualiza al abrir
    y = _yaml(tmp_path, {"plantilla": "prueba.docx", "salida": "salida.docx"})
    d = Document(generar_documento(y, plantilla_prueba.parent, tmp_path / "out", ctx_prueba))
    assert d.settings.element.xpath("./w:updateFields[@w:val='true']")


def test_clonado_no_corre_indices(tmp_path, plantilla_prueba, ctx_prueba):
    y = _yaml(tmp_path, {
        "plantilla": "prueba.docx",
        "salida": "salida.docx",
        "grupos": [{
            "tablas": [2],
            "encabezados": [["Campo"]],
            "instancias": [
                {2: {"campos": {"ID y nombre": "{{cu.CU-001}}"}}},
                {2: {"campos": {"ID y nombre": "CU-002 — Otro"}}},
            ],
        }],
        "tablas": [{"indice": 3, "encabezado": ["Paso"], "filas": [["1", "Buscar"]]}],
    })
    d = Document(generar_documento(y, plantilla_prueba.parent, tmp_path / "out", ctx_prueba))
    assert len(d.tables) == 5
    assert d.tables[2].cell(1, 1).text == "CU-001 — Realizar pedido"
    assert d.tables[3].cell(1, 1).text == "CU-002 — Otro"
    assert d.tables[4].cell(1, 1).text == "Buscar"
