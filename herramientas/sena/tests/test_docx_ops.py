import pytest
from docx.shared import Pt

from docx_ops import (
    PlantillaCambiadaError,
    agregar_filas,
    clonar_bloque,
    escribir_celda,
    llenar_campos,
    reemplazar_filas,
    rellenar_linea,
    tabla,
)


def test_tabla_con_encabezado_distinto_falla(doc_prueba):
    with pytest.raises(PlantillaCambiadaError, match="T1"):
        tabla(doc_prueba, 1, ["Código"])


def test_tabla_acepta_prefijo_sin_tildes(doc_prueba):
    assert tabla(doc_prueba, 0, ["campo", "informacion"])._tbl is doc_prueba.tables[0]._tbl


def test_escribir_celda_conserva_formato(doc_prueba):
    celda = doc_prueba.tables[0].cell(1, 1)
    escribir_celda(celda, "3045678\nsegunda")
    r = celda.paragraphs[0].runs[0]
    assert (r.text, r.bold, r.font.size.pt) == ("3045678", True, 9)
    assert celda.paragraphs[1].runs[0].bold is True
    assert celda.paragraphs[1].runs[0].text == "segunda"
    assert len(celda.paragraphs) == 2


def test_celda_vacia_toma_formato_de_la_fila(doc_prueba):
    t = doc_prueba.tables[1]
    r = t.cell(1, 0).paragraphs[0].runs[0]
    r.font.size = Pt(8)
    escribir_celda(t.cell(1, 1), "nuevo")  # celda sin formato propio
    assert t.cell(1, 1).paragraphs[0].runs[0].font.size.pt == 8


def test_run_vacio_no_impone_formato(doc_prueba):
    t = doc_prueba.tables[1]
    t.cell(1, 0).paragraphs[0].runs[0].font.size = Pt(8)
    vacio = t.cell(1, 1).paragraphs[0].add_run("")
    vacio.font.size = Pt(14)
    escribir_celda(t.cell(1, 1), "nuevo")
    assert t.cell(1, 1).paragraphs[0].runs[0].font.size.pt == 8


def test_llenar_campos(doc_prueba):
    llenar_campos(doc_prueba.tables[0], {"Ficha": "3045678"})
    assert doc_prueba.tables[0].cell(1, 1).text == "3045678"


def test_llenar_campos_lista_llena_ultimas_columnas(doc_prueba):
    t = doc_prueba.tables[1]
    llenar_campos(t, {"RF-002": ["Iniciar sesión", "Aprobado"]})
    assert [c.text for c in t.rows[2].cells] == ["RF-002", "Iniciar sesión", "Aprobado"]


def test_llenar_campos_clave_inexistente(doc_prueba):
    with pytest.raises(KeyError, match="Regional"):
        llenar_campos(doc_prueba.tables[0], {"Regional": "x"})


def test_reemplazar_filas(doc_prueba):
    t = doc_prueba.tables[1]
    reemplazar_filas(t, [["RF-010", "A", "B"]] * 3, nuevo_encabezado=["ID", "Nombre", "Prioridad"])
    assert [c.text for c in t.rows[0].cells] == ["ID", "Nombre", "Prioridad"]
    assert len(t.rows) == 4 and t.cell(3, 0).text == "RF-010"


def test_reemplazar_filas_columnas_distintas(doc_prueba):
    with pytest.raises(ValueError):
        reemplazar_filas(doc_prueba.tables[1], [["solo una"]])


def test_agregar_filas(doc_prueba):
    agregar_filas(doc_prueba.tables[1], [["RF-003", "X", "Y"]])
    t = doc_prueba.tables[1]
    assert len(t.rows) == 4 and t.cell(1, 0).text == "RF-001" and t.cell(3, 0).text == "RF-003"


def test_rellenar_linea_misma_y_siguiente(doc_prueba):
    rellenar_linea(doc_prueba, "Nombre del proyecto:", "AgroConecta")
    rellenar_linea(doc_prueba, "Limitaciones:", "Ninguna")
    textos = [p.text for p in doc_prueba.paragraphs]
    assert "Nombre del proyecto: AgroConecta" in textos and "Ninguna" in textos


def test_rellenar_linea_inexistente(doc_prueba):
    with pytest.raises(KeyError):
        rellenar_linea(doc_prueba, "No existe:", "x")


def test_clonar_bloque(doc_prueba):
    t2, t3 = doc_prueba.tables[2], doc_prueba.tables[3]
    nuevas = clonar_bloque(t2, t3)
    assert len(nuevas) == 2 and len(doc_prueba.tables) == 6
    assert doc_prueba.tables[4]._tbl is nuevas[0]._tbl
    assert doc_prueba.tables[5]._tbl is nuevas[1]._tbl


def _png_minimo(ruta):
    import struct
    import zlib

    def bloque(tipo, datos):
        return struct.pack(">I", len(datos)) + tipo + datos + struct.pack(">I", zlib.crc32(tipo + datos))

    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ruta.write_bytes(b"\x89PNG\r\n\x1a\n" + bloque(b"IHDR", ihdr)
                     + bloque(b"IDAT", zlib.compress(b"\x00\xff\xff\xff")) + bloque(b"IEND", b""))
    return ruta


def test_insertar_imagen_despues_de(doc_prueba, tmp_path):
    from docx_ops import insertar_imagen_despues_de

    png = _png_minimo(tmp_path / "x.png")
    insertar_imagen_despues_de(doc_prueba, "Limitaciones:", png, 10)
    textos = [p.text for p in doc_prueba.paragraphs]
    i = textos.index("Limitaciones:")
    assert doc_prueba.paragraphs[i + 1]._p.xpath(".//pic:pic")
    assert len(doc_prueba.inline_shapes) == 1


def test_insertar_imagen_parrafo_inexistente(doc_prueba, tmp_path):
    from docx_ops import insertar_imagen_despues_de

    with pytest.raises(KeyError):
        insertar_imagen_despues_de(doc_prueba, "No existe", _png_minimo(tmp_path / "x.png"), 10)


def test_clonar_bloque_omite_titulos(doc_prueba):
    t2, t3 = doc_prueba.tables[2], doc_prueba.tables[3]
    titulo = doc_prueba.add_heading("9.4 Flujo", level=2)
    t2._tbl.addnext(titulo._p)  # título entre las dos tablas del bloque
    clonar_bloque(t2, t3)
    assert [p.text for p in doc_prueba.paragraphs].count("9.4 Flujo") == 1
    assert [p.text for p in doc_prueba.paragraphs].count("entre tablas") == 2


def test_clonar_bloque_separa_con_parrafo(doc_prueba):
    # Word fusiona tablas contiguas: el clon debe quedar separado por un párrafo
    t3 = doc_prueba.tables[3]
    clonar_bloque(t3, t3)
    assert t3._tbl.getnext().tag.endswith("}p")
