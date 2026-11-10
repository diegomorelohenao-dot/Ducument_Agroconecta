from conftest import generar_y_abrir, tabla_por_encabezado, tabla_texto


def test_requisitos():
    d = generar_y_abrir("requisitos")
    assert len(d.tables[19].rows) == 31 and d.tables[19].cell(12, 1).text == "Generar pedidos desde el carrito"
    reglas = tabla_por_encabezado(d, ["ID", "Nombre", "Regla", "Fuente"])
    assert len(reglas.rows) == 16 and "RF-020" in reglas.cell(6, 5).text  # fila de RN-006
    assert tabla_por_encabezado(d, ["Recurso / acción"]).cell(0, 1).text == "Productor"
    escenarios = tabla_texto(tabla_por_encabezado(d, ["ID requisito", "Escenario"]))
    assert "4.000" in escenarios


def test_requisitos_fichas_clonadas():
    d = generar_y_abrir("requisitos")
    fichas_rf = [t.cell(1, 1).text for t in d.tables
                 if len(t.rows) > 1 and len(t.columns) == 2 and t.cell(0, 0).text == "Campo"
                 and t.cell(1, 1).text.startswith("RF-0")]
    assert [f[:6] for f in fichas_rf] == ["RF-012", "RF-019", "RF-020"]
