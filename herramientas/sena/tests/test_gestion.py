from conftest import generar_y_abrir, tabla_texto


def test_gestion():
    d = generar_y_abrir("gestion")
    assert [d.tables[10].cell(i, 0).text for i in range(1, 8)] == [f"STK-0{n}" for n in range(1, 8)]
    assert [d.tables[16].cell(i, 0).text for i in range(1, 5)] == [f"EQ-0{n}" for n in range(1, 5)]
    sprints = d.tables[24]
    assert sprints.cell(1, 0).text == "S01" and "2027-01-11" in sprints.cell(1, 4).text
    assert sprints.cell(11, 0).text == "S11" and "2027-06-11" in sprints.cell(11, 4).text
    decisiones = tabla_texto(d.tables[30])
    assert "DEC-06" in decisiones and "IA" in decisiones
    assert d.tables[0].cell(4, 1).text == "3144585"
