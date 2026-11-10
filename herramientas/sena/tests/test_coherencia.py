"""Coherencia del contenido entre documentos (hallazgos de la revisión final)."""
from conftest import generar_y_abrir, tabla_por_encabezado

from generar import CONTENIDO, RAIZ
from plantilla_yaml import cargar_yaml


def _texto(nombre):
    return (CONTENIDO / f"{nombre}.yaml").read_text(encoding="utf-8")


def test_tabla_de_actores_sale_del_catalogo():
    cat = cargar_yaml(CONTENIDO / "catalogo.yaml")
    d = generar_y_abrir("requisitos")
    t = tabla_por_encabezado(d, ["ID", "Actor", "Tipo", "Objetivo"])
    for fila in t.rows[1:]:
        actor = fila.cells[0].text
        esperado = sorted(r for r, v in cat["requisitos"].items() if actor in v["actores"])
        assert fila.cells[4].text == ", ".join(esperado), actor


def test_diagrama_incluye_todos_los_actores():
    puml = (RAIZ / "docs" / "sena" / "diagramas" / "casos_de_uso.puml").read_text(encoding="utf-8")
    assert all(f"ACT-0{n}" in puml for n in range(1, 8))


def test_hitos_y_sprints_coherentes():
    assert "HIT-" not in _texto("requisitos")  # Alcance usa los hitos del catálogo (H-0N)
    assert "sprints S07 a S10" not in _texto("formulacion")  # RF-024..030 van en S08-S10


def test_sin_contradicciones_de_contenido():
    assert "Stack conocido" not in _texto("formulacion")  # contradice RSK-03
    backlog = _texto("backlog")
    assert "intentar de nuevo" not in backlog  # CANCELADO es estado final
    assert "EN_DISPUTA" in backlog.split("{{cu.CU-002}}")[1].split("{{cu.CU-003}}")[0]
