from conftest import generar_y_abrir, tabla_texto, textos_parrafos


def test_formulacion():
    d = generar_y_abrir("formulacion")
    assert any(t.startswith("Nombre del proyecto: AgroConecta") for t in textos_parrafos(d))
    assert [d.tables[19].cell(i, 0).text for i in range(1, 6)] == [f"OBJ-0{n}" for n in range(1, 6)]
    assert "novia" not in tabla_texto(d.tables[22])
    assert d.tables[17].cell(4, 4).text.startswith("Seleccionada")
    assert [d.tables[43].cell(i, 0).text for i in range(1, 7)] == [f"RSK-0{n}" for n in range(1, 7)]
    assert d.tables[0].cell(2, 1).text == "AgroConecta"
