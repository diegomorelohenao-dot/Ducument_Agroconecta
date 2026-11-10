from conftest import generar_y_abrir

from generar import CONTENIDO, RAIZ
from plantilla_yaml import cargar_yaml
from validar import v5_criterios_por_historia


def test_backlog():
    d = generar_y_abrir("backlog")
    maestro = d.tables[13]
    assert sum(1 for f in maestro.rows if f.cells[1].text.startswith("HU-")) == 30
    fichas_cu = [t for t in d.tables
                 if len(t.rows) > 1 and len(t.columns) == 2 and t.cell(1, 1).text.startswith("CU-00")]
    assert [t.cell(1, 1).text[:6] for t in fichas_cu] == ["CU-001", "CU-002", "CU-003", "CU-004"]
    assert len(d.inline_shapes) >= 1
    # el ejemplo de la sección 9.5 ("CU-001: Registrar préstamo") se reemplaza por nuestro CU-001;
    # los recuadros de guía de la plantilla (p. ej. "Ejemplo de división") se dejan intactos
    resumenes = [t.cell(0, 0).text for t in d.tables if t.cell(0, 0).text.startswith("CU-001:")]
    assert resumenes and all(r.startswith("CU-001: Realizar pedido y pago") for r in resumenes)


def test_backlog_criterios_y_diagrama():
    cat = cargar_yaml(CONTENIDO / "catalogo.yaml")
    assert v5_criterios_por_historia(cargar_yaml(CONTENIDO / "backlog.yaml"), cat) == []
    assert (RAIZ / "docs" / "sena" / "diagramas" / "casos_de_uso.png").exists()
