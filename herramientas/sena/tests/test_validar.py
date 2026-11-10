import pytest
from docx import Document

from validar import (
    ids_citados,
    v1_ids_existen,
    v2_consistencia_catalogo,
    v3_residuos,
    v4_pendientes,
    v5_criterios_por_historia,
)


@pytest.fixture
def mini():
    return {
        "epicas": {"EP-001": "Identidad"},
        "funcionalidades": {"FEAT-001": {"nombre": "Registro", "epica": "EP-001"}},
        "requisitos": {
            "RF-001": {"nombre": "Registrar usuario", "epica": "EP-001", "feat": "FEAT-001", "rn": ["RN-001"]},
        },
        "historias": {"HU-001": {"nombre": "Registrar usuario", "rf": "RF-001"}},
        "reglas": {"RN-001": {"nombre": "R1", "texto": "t"}},
        "casos_uso": {"CU-001": {"nombre": "C", "hu": ["HU-001"]}},
    }


def test_ids_citados():
    assert ids_citados("ver RF-012, RN-006 y OBJ-03; no RF-12; CA-HU-001-01") == {
        "RF-012", "RN-006", "OBJ-03", "HU-001"}


def test_ids_citados_existen(mini):
    assert v1_ids_existen({"x.yaml": {"a": ["HU-031", "RF-001"]}}, mini) == [
        "x.yaml: HU-031 no existe en el catálogo"]


def test_catalogo_consistente(mini):
    assert v2_consistencia_catalogo(mini) == []


def test_nombres_salen_del_catalogo(mini):
    mini["historias"]["HU-001"]["nombre"] = "Otro nombre"
    assert any("HU-001" in e and "nombre" in e for e in v2_consistencia_catalogo(mini))


def test_rn_sin_requisito(mini):
    mini["reglas"]["RN-002"] = {"nombre": "R2", "texto": "t"}
    assert any("RN-002" in e for e in v2_consistencia_catalogo(mini))


def test_cu_con_hu_inexistente(mini):
    mini["casos_uso"]["CU-001"]["hu"].append("HU-099")
    assert any("CU-001" in e and "HU-099" in e for e in v2_consistencia_catalogo(mini))


def test_detecta_residuos_de_plantilla():
    doc = Document()
    t = doc.add_table(rows=2, cols=2)
    t.cell(1, 0).text = "A/M/B"
    t.cell(1, 1).text = "texto válido"
    assert len(v3_residuos([t])) == 1
    t.cell(1, 0).text = "Alta"
    assert v3_residuos([t]) == []


def test_v4_pendientes(tmp_path):
    (tmp_path / "comun.yaml").write_text('ficha: "[PENDIENTE: número de ficha]"\n', encoding="utf-8")
    (tmp_path / "otro.yaml").write_text("a: sin pendientes\n", encoding="utf-8")
    assert v4_pendientes(tmp_path) == {"comun.yaml": ["[PENDIENTE: número de ficha]"]}


def test_v5_exige_caso_de_error(mini):
    backlog = {"tablas": [{"indice": 18, "filas": [
        ["CA-HU-001-01", "HU-001", "ok", "Éxito", "Alta", "CP"],
        ["CA-HU-001-02", "HU-001", "ok", "Éxito", "Alta", "CP"],
    ]}]}
    assert any("HU-001" in e for e in v5_criterios_por_historia(backlog, mini))
    backlog["tablas"][0]["filas"][1][3] = "Error"
    assert v5_criterios_por_historia(backlog, mini) == []
