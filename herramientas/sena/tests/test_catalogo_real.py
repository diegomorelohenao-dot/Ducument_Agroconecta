from generar import CONTENIDO
from plantilla_yaml import cargar_yaml
from validar import v2_consistencia_catalogo


def test_catalogo_real_consistente():
    cat = cargar_yaml(CONTENIDO / "catalogo.yaml")
    assert v2_consistencia_catalogo(cat) == []
    assert len(cat["requisitos"]) == 30 and len(cat["historias"]) == 30
    assert len(cat["reglas"]) == 15 and len(cat["rnf"]) == 14 and len(cat["casos_uso"]) == 4
    assert len(cat["epicas"]) == 7 and len(cat["funcionalidades"]) == 14
    hus = [h for s in cat["sprints"].values() for h in s["historias"]]
    assert sorted(hus) == sorted(cat["historias"])


CLAVES = {
    "reglas": {"nombre", "texto"}, "rnf": {"categoria", "requisito"},
    "historias": {"nombre", "rf", "enunciado"}, "riesgos": {"riesgo", "p", "i"},
    "requisitos": {"nombre", "epica", "feat", "actores", "rn", "prioridad", "version"},
    "indicadores": {"nombre", "objetivo", "meta"}, "actores": {"nombre", "tipo"},
    "funcionalidades": {"nombre", "epica"}, "casos_uso": {"nombre", "actor", "hu"},
    "alcance": {"nombre", "epica"}, "sprints": {"inicio", "fin", "historias", "extra"},
    "hitos": {"nombre", "fecha"},
}


def test_sin_claves_inesperadas():
    # una coma sin comillas dentro de {...} en YAML crea una clave nueva y corta el texto
    cat = cargar_yaml(CONTENIDO / "catalogo.yaml")
    extras = {(col, i): set(v) - claves for col, claves in CLAVES.items()
              for i, v in cat[col].items() if set(v) - claves}
    assert extras == {}


def test_comun_tiene_campos_basicos():
    comun = cargar_yaml(CONTENIDO / "comun.yaml")
    assert comun["proyecto"] == "AgroConecta"
    assert set(comun["integrantes"]) == {"EQ-01", "EQ-02", "EQ-03", "EQ-04"}
