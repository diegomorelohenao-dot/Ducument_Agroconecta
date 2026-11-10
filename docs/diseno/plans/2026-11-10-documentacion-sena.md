# Documentación SENA de AgroConecta — Plan de implementación

**Goal:** Producir las 4 plantillas SENA ADSO llenas para AgroConecta (entrega: 2026-12-04), consistentes entre sí y trazables a la especificación.

**Architecture:** El contenido vive en archivos YAML versionados (`docs/sena/contenido/`), uno por documento más un catálogo maestro de IDs compartido. Un generador en Python (python-docx) toma las plantillas originales sin modificarlas, llena sus tablas y líneas de subrayado según el YAML y guarda las copias en `docs/sena/entregables/`. Un validador comprueba la consistencia de IDs entre documentos, los residuos de la plantilla y los pendientes.

**Tech Stack:** Python 3.12, python-docx 1.1.2, PyYAML 6.0.2, pytest 8.3.3, PlantUML 1.2024.7 (Java 25, ya instalado).

**Spec:** `docs/diseno/specs/2026-11-10-agroconecta-design.md`

## Global Constraints

- Todo el contenido está en español. Fechas en formato `AAAA-MM-DD`.
- La fecha de entrega en todos los documentos es `2026-12-04`, versión `1.0`, estado `En revisión`. Historial: `0.1 · 2026-11-10 · Creación inicial a partir de la especificación de diseño` y `1.0 · 2026-12-04 · Versión para entrega`.
- Los IDs siguen los formatos de las plantillas: `OBJ-01`, `IND-01`, `STK-01`, `ACT-01`, `ALC-01`, `EXC-01`, `RSK-01`, `EP-001`, `FEAT-001`, `RF-001`, `RNF-001`, `RN-001`, `HU-001`, `CU-001`. La regla RN-0X de la especificación se escribe aquí como `RN-00X`.
- **No se inventan datos.** Las estadísticas, fuentes, cifras del sector, líneas base y nombres de personas que la especificación no contiene se escriben como `[PENDIENTE: <qué falta>]`, y cada uno queda registrado en el anexo de pendientes.
- Las plantillas originales nunca se modifican. Solo se escribe en `docs/sena/entregables/`.
- Las tablas de referencia de la plantilla (principios, definiciones, escalas, convenciones, cuadros "Instrucción/Ejemplo/Advertencia/Criterio de calidad") se dejan intactas.
- Las listas de verificación (columna "Cumple"), los registros de aprobación o aceptación y las firmas quedan sin llenar: son para el equipo y el instructor.
- Python se ejecuta con `python -X utf8` y desde el venv `herramientas/sena/.venv`.
- Se declara el uso de IA (regla 13.3 de la plantilla de Gestión) en el registro de decisiones `DEC-06`.

## Review Focus

1. **Desplazamiento de índices de tabla:** clonar una ficha inserta tablas y corre los índices siguientes. Comportamiento esperado: todas las tablas se resuelven por índice original **antes** de aplicar cualquier operación. Prueba: `test_clonado_no_corre_indices` (Tarea 2).
2. **Residuos de la plantilla en tablas llenas:** opciones como `A/M/B`, `Sí / No`, `Alta / Media / Baja`, `RF-___`, `____` o la fila de ejemplo `novia` (Formulación T22). Esperado: el validador los marca como error. Prueba: `test_detecta_residuos_de_plantilla` (Tarea 3).
3. **Pérdida de formato al escribir celdas:** la fuente, el tamaño y la negrita de la plantilla deben conservarse. Esperado: la celda escrita mantiene las propiedades del primer run original. Prueba: `test_escribir_celda_conserva_formato` (Tarea 1).
4. **IDs inconsistentes entre documentos:** por ejemplo, un `HU-031` en el Backlog que no existe, o un `RF-012` con otro nombre en Requisitos. Esperado: todo ID citado existe en el catálogo, y los nombres de RF/HU/CU salen del catálogo, no se reescriben a mano. Pruebas: `test_ids_citados_existen` y `test_nombres_salen_del_catalogo` (Tarea 3).
5. **Cambio de estructura de la plantilla:** si alguien reemplaza un `.docx` por otra versión, los índices dejan de coincidir. Esperado: error explícito `PlantillaCambiadaError` que nombra el índice y el encabezado esperado, nunca un llenado silencioso de la tabla equivocada. Prueba: `test_tabla_con_encabezado_distinto_falla` (Tarea 1).

---

## Estructura de archivos

```
docs/sena/
├── plantillas/                 # las 4 .docx originales (se mueven desde la raíz)
├── contenido/
│   ├── comun.yaml              # identificación: centro, regional, ficha, equipo, instructor
│   ├── catalogo.yaml           # catálogo maestro de IDs (fuente única de nombres)
│   ├── formulacion.yaml
│   ├── gestion.yaml
│   ├── requisitos.yaml
│   └── backlog.yaml
├── diagramas/casos_de_uso.puml (+ .png generado)
├── entregables/                # AgroConecta_<Documento>.docx generados
└── PENDIENTES.md               # generado por el validador
herramientas/sena/
├── requirements.txt
├── docx_ops.py                 # operaciones sobre python-docx
├── plantilla_yaml.py           # carga YAML, sustituye {{...}}, resuelve referencias al catálogo
├── generar.py                  # CLI: genera uno o todos los documentos
├── validar.py                  # CLI: validaciones V1–V5 y PENDIENTES.md
└── tests/
```

## Esquema de los YAML de documento (lo usan las Tareas 2 y 4–7)

```yaml
plantilla: Formulacion_y_Constitucion_Proyecto_Software_ADSO_SENA.docx
salida: AgroConecta_Formulacion_y_Constitucion.docx
lineas:                       # líneas de subrayado "Etiqueta: ______"
  - etiqueta: "Nombre del proyecto:"
    valor: "AgroConecta"
tablas:
  - indice: 13                # índice en la plantilla ORIGINAL
    encabezado: ["ID", "Módulo"]   # prefijos de las primeras celdas de la fila 0
    campos: {"Centro de formación": "{{comun.centro}}"}   # tabla Campo/Valor: llena la última celda
    filas: [["ALC-01", "..."]]     # reemplaza todas las filas de datos
    agregar: [["...", "..."]]      # agrega filas después de las existentes
    nuevo_encabezado: ["Recurso / acción", "Productor", "Comprador", "Administrador", "Regla"]
grupos:                       # fichas que se repiten: se clona el bloque desde la primera hasta la última tabla
  - tablas: [25, 26, 27]
    instancias:
      - {25: {campos: {...}}, 26: {filas: [...]}, 27: {filas: [...]}}
      - {...}
```

Cada entrada de `tablas` usa exactamente una de `campos`, `filas` o `agregar` (más `nuevo_encabezado` opcional). Las cadenas pueden usar `{{comun.<clave>}}`, `{{rf.RF-012}}` (devuelve "RF-012 — <nombre>"), `{{hu.HU-012}}` y `{{cu.CU-001}}`, que se resuelven desde `comun.yaml` y `catalogo.yaml`. Una fila que contenga **solo** el marcador `"{{todas: requisitos}}"` (o `historias`, `rnf`, `reglas`, `casos_uso`) se expande con una fila por cada elemento del catálogo según la plantilla de fila `columnas:` que acompaña la entrada (ver Tarea 2).

---

## Catálogo maestro (lo crea la Tarea 3; los nombres son definitivos)

**Objetivos** — General: *Desarrollar, a junio de 2027, una plataforma web instalable (PWA) que permita a pequeños productores agrícolas de Colombia vender directamente a consumidores y negocios, con pedidos y pago en línea, para reducir su dependencia de intermediarios.*

| ID | Objetivo específico |
|---|---|
| OBJ-01 | Documentar formulación, gestión, requisitos y backlog del producto a 2026-12-04 |
| OBJ-02 | Implementar el registro, la verificación de productores y el catálogo de productos con búsqueda por ubicación |
| OBJ-03 | Implementar pedidos con pago en línea (sandbox), retención del dinero, comisión y liquidación al productor |
| OBJ-04 | Implementar el seguimiento del pedido, las disputas y las calificaciones |
| OBJ-05 | Verificar el MVP con pruebas automatizadas y desplegarlo a 2027-06-11 |

| ID | Indicador | Objetivo | Meta |
|---|---|---|---|
| IND-01 | Documentos SENA entregados | OBJ-01 | 4 de 4 a 2026-12-04 |
| IND-02 | RF del MVP implementados y aceptados | OBJ-02, OBJ-03, OBJ-04 | 100 % (30 de 30) |
| IND-03 | Reglas de negocio con prueba unitaria automatizada | OBJ-03 | 15 de 15 |
| IND-04 | Camino principal E2E pasando en CI sobre la rama principal | OBJ-05 | 100 % de las ejecuciones en la semana de entrega |

| ID | Interesado | | ID | Actor | Tipo |
|---|---|---|---|---|---|
| STK-01 | Pequeños productores agrícolas | | ACT-01 | Productor | Humano |
| STK-02 | Compradores consumidores | | ACT-02 | Comprador consumidor | Humano |
| STK-03 | Compradores negocio (restaurantes, tiendas, fruvers) | | ACT-03 | Comprador negocio | Humano |
| STK-04 | Administrador de la plataforma | | ACT-04 | Administrador | Humano |
| STK-05 | Instructor(es) SENA | | ACT-05 | Visitante (sin sesión) | Humano |
| STK-06 | Equipo de desarrollo | | ACT-06 | Wompi (pasarela de pagos) | Sistema |
| STK-07 | Wompi (proveedor externo) | | ACT-07 | Planificador de tareas | Sistema |

**Épicas** = módulos de la especificación (§3.2): EP-001 Identidad y cuenta · EP-002 Productores · EP-003 Catálogo · EP-004 Pedidos · EP-005 Pagos · EP-006 Reputación · EP-007 Administración.

**Funcionalidades:** FEAT-001 Registro y acceso (EP-001) · FEAT-002 Cuenta y notificaciones (EP-001) · FEAT-003 Perfil y entrega del productor (EP-002) · FEAT-004 Verificación de productores (EP-002) · FEAT-005 Publicación de productos (EP-003) · FEAT-006 Búsqueda y detalle (EP-003) · FEAT-007 Carrito y creación de pedidos (EP-004) · FEAT-008 Ciclo de vida del pedido (EP-004) · FEAT-009 Cobro en línea (EP-005) · FEAT-010 Saldo y liquidaciones (EP-005) · FEAT-011 Reembolsos (EP-005) · FEAT-012 Calificaciones (EP-006) · FEAT-013 Disputas (EP-007) · FEAT-014 Operación administrativa (EP-007).

**Requisitos funcionales** (todos `MVP`; prioridad `Must` salvo RF-029 `Should`). La historia `HU-0NN` corresponde 1:1 al `RF-0NN` y tiene el mismo nombre.

| ID | Nombre | FEAT | Actores | RN |
|---|---|---|---|---|
| RF-001 | Registrar usuario con rol y consentimiento de datos | 001 | ACT-01, 02, 03, 05 | — |
| RF-002 | Iniciar y renovar sesión | 001 | ACT-01–04 | — |
| RF-003 | Eliminar cuenta | 002 | ACT-01–03 | — |
| RF-004 | Gestionar perfil de productor | 003 | ACT-01 | RN-001 |
| RF-005 | Configurar opciones de entrega | 003 | ACT-01 | RN-008 |
| RF-006 | Verificar productor | 004 | ACT-04 | RN-001 |
| RF-007 | Gestionar productos | 005 | ACT-01 | RN-001 |
| RF-008 | Definir precios por volumen | 005 | ACT-01 | RN-003 |
| RF-009 | Buscar productos por texto, categoría y ubicación | 006 | ACT-02, 03, 05 | — |
| RF-010 | Ver detalle de producto y productor | 006 | ACT-02, 03, 05 | — |
| RF-011 | Gestionar carrito | 007 | ACT-02, 03 | — |
| RF-012 | Generar pedidos desde el carrito | 007 | ACT-02, 03 | RN-002, 003, 007, 008, 012 |
| RF-013 | Aceptar o rechazar pedido | 008 | ACT-01 | RN-011 |
| RF-014 | Marcar pedido como enviado | 008 | ACT-01 | — |
| RF-015 | Confirmar recepción del pedido | 008 | ACT-02, 03 | RN-005 |
| RF-016 | Consultar pedidos e historial | 008 | ACT-01–04 | — |
| RF-017 | Aplicar plazos automáticos del pedido | 008 | ACT-07 | RN-011 |
| RF-018 | Iniciar pago en línea | 009 | ACT-02, 03, 06 | RN-012 |
| RF-019 | Procesar notificación de pago (webhook) | 009 | ACT-06 | RN-004, 005, 013 |
| RF-020 | Calcular comisión y acreditar saldo | 010 | ACT-07 | RN-005, 006, 009, 012 |
| RF-021 | Consultar saldo y movimientos | 010 | ACT-01 | RN-009 |
| RF-022 | Solicitar liquidación de saldo | 010 | ACT-01 | RN-010 |
| RF-023 | Ejecutar reembolso | 011 | ACT-04, 06, 07 | RN-004, 011 |
| RF-024 | Calificar productor | 012 | ACT-02, 03 | RN-014 |
| RF-025 | Abrir disputa | 013 | ACT-02, 03 | RN-015 |
| RF-026 | Resolver disputa | 013 | ACT-04 | RN-011 |
| RF-027 | Marcar liquidación como pagada | 014 | ACT-04 | RN-010 |
| RF-028 | Configurar comisión y mínimo de retiro | 014 | ACT-04 | RN-007 |
| RF-029 | Consultar reportes de pedidos y comisiones | 014 | ACT-04 | — |
| RF-030 | Enviar notificaciones en la app y por correo | 002 | ACT-07 | — |

RF-020 lo dispara el evento `PedidoEntregado`, así que su actor es el sistema (ACT-07). RF-029 en el MVP muestra los totales de pedidos por estado y las comisiones por mes.

**Reglas de negocio:** RN-001 … RN-015 = RN-01 … RN-15 de la especificación §4.3, con el mismo texto.

**Requisitos no funcionales:**

| ID | Categoría | Requisito |
|---|---|---|
| RNF-001 | Seguridad | Contraseñas almacenadas con bcrypt |
| RNF-002 | Seguridad | Token de acceso de 15 min más refresh token |
| RNF-003 | Seguridad | 5 intentos fallidos de login bloquean la cuenta 15 min *(valor propuesto)* |
| RNF-004 | Seguridad | Autorización por rol y por propiedad del recurso en todos los endpoints |
| RNF-005 | Seguridad | Validación de entrada en todos los endpoints; entrada inválida → 400 |
| RNF-006 | Integridad | Las 4 operaciones de dinero de la especificación §8 son atómicas |
| RNF-007 | Fiabilidad | Webhook idempotente con firma verificada |
| RNF-008 | Fiabilidad | Job de plazos cada 5 min, idempotente |
| RNF-009 | Portabilidad / usabilidad | PWA instalable, usable desde 360 px de ancho |
| RNF-010 | Cumplimiento | Ley 1581 de 2012: consentimiento explícito y eliminación de cuenta |
| RNF-011 | Mantenibilidad | Clean Architecture: `domain` sin dependencias externas |
| RNF-012 | Calidad | CI con lint, pruebas y build en cada PR; E2E del camino principal |
| RNF-013 | Rendimiento | Búsqueda de catálogo con p95 ≤ 1 s con 1.000 productos *(valor propuesto)* |
| RNF-014 | Interoperabilidad | Errores `{ codigo, mensaje, detalles? }` con los códigos HTTP de la especificación §8 |

**Casos de uso:** CU-001 Realizar pedido y pago (ACT-02/03; HU-011, 012, 018, 019) · CU-002 Gestionar ciclo del pedido (ACT-01; HU-013, 014, 015, 017, 020) · CU-003 Resolver disputa (ACT-04; HU-025, 026, 023) · CU-004 Liquidar saldo (ACT-01; HU-021, 022, 027).

**Alcance:** ALC-01 … ALC-07 = EP-001 … EP-007. **Exclusiones** (especificación §7.2): EXC-01 Notificaciones push · EXC-02 Chat productor–comprador · EXC-03 Mapa y geolocalización · EXC-04 Facturación electrónica DIAN · EXC-05 Pago contraentrega · EXC-06 Logística/transporte · EXC-07 App nativa · EXC-08 Operación con dinero real.

**Riesgos:**

| ID | Riesgo | P | I |
|---|---|---|---|
| RSK-01 | Dificultades al integrar la pasarela Wompi (firma, webhooks, sandbox) | 3 | 4 |
| RSK-02 | Crecimiento del alcance más allá del MVP | 3 | 4 |
| RSK-03 | Curva de aprendizaje de NestJS y Clean Architecture | 4 | 3 |
| RSK-04 | Baja disponibilidad de integrantes en algunos periodos | 3 | 3 |
| RSK-05 | No contar con productores reales para validar el problema | 3 | 3 |
| RSK-06 | Límites de los planes gratuitos de hosting | 2 | 3 |

Escala 1–5. Nivel = P × I.

**Equipo** (los nombres van en `comun.yaml`): EQ-01 Líder y backend · EQ-02 Backend (pagos) y QA · EQ-03 Frontend y UX/UI · EQ-04 Frontend y análisis/Product Owner.

**Cronograma:** Scrum con sprints de 2 semanas.

| Sprint | Fechas | Historias |
|---|---|---|
| S01 | 2027-01-11 → 01-22 | base del proyecto, CI, HU-001, 002 |
| S02 | 01-25 → 02-05 | HU-003, 004, 005, 006 |
| S03 | 02-08 → 02-19 | HU-007, 008 |
| S04 | 02-22 → 03-05 | HU-009, 010, 011 |
| S05 | 03-08 → 03-19 | HU-012, 018 |
| S06 | 03-22 → 04-02 | HU-019, 013, 023 |
| S07 | 04-05 → 04-16 | HU-014, 015, 016, 020, 021 |
| S08 | 04-19 → 04-30 | HU-017, 022, 027 |
| S09 | 05-03 → 05-14 | HU-024, 025, 026 |
| S10 | 05-17 → 05-28 | HU-028, 029, 030, PWA |
| S11 | 05-31 → 06-11 | E2E, despliegue, estabilización, entrega |

**Hitos:** H-01 Documentación SENA entregada (2026-12-04) · H-02 Identidad y productores (2027-02-05) · H-03 Catálogo y búsqueda (2027-03-05) · H-04 Pedidos y pagos (2027-04-16) · H-05 MVP completo (2027-05-28) · H-06 Entrega final (2027-06-11).

---

### Tarea 1: Base del proyecto y operaciones sobre docx

**Files:**
- Move: los 4 `*.docx` de la raíz → `docs/sena/plantillas/`
- Create: `herramientas/sena/requirements.txt`, `herramientas/sena/docx_ops.py`, `.gitignore`
- Test: `herramientas/sena/tests/test_docx_ops.py`, `herramientas/sena/tests/conftest.py`

**Interfaces:**
- Produces (en `docx_ops.py`):
  - `class PlantillaCambiadaError(Exception)`
  - `tabla(doc: Document, indice: int, encabezado: list[str]) -> Table`: lanza `PlantillaCambiadaError(f"T{indice}: se esperaba {encabezado}, hay {real}")` si alguna celda de la fila 0 no empieza por el prefijo esperado (comparación sin tildes ni mayúsculas).
  - `escribir_celda(celda: _Cell, texto: str) -> None`: conserva el estilo del párrafo y las propiedades (`rPr`) del primer run; cada `\n` crea un párrafo nuevo con ese mismo formato.
  - `llenar_campos(t: Table, campos: dict[str, str]) -> None`: busca la fila cuya primera celda empieza por la clave (normalizada) y escribe en la última celda. Clave inexistente → `KeyError` con el nombre de la clave.
  - `reemplazar_filas(t: Table, filas: list[list[str]], nuevo_encabezado: list[str] | None = None) -> None`: usa la fila 1 como prototipo (deepcopy de `w:tr`), elimina las filas 1..n y agrega una por cada fila. Si el número de columnas es distinto → `ValueError`.
  - `agregar_filas(t: Table, filas: list[list[str]]) -> None`: prototipo = última fila.
  - `rellenar_linea(doc: Document, etiqueta: str, valor: str) -> None`: si el párrafo empieza por `etiqueta` y contiene `___`, queda como `"<etiqueta> <valor>"`. Si el párrafo de la etiqueta no tiene subrayado, se reemplaza el primer párrafo siguiente que sea solo `_`. Si no encuentra nada → `KeyError`.
  - `clonar_bloque(primera: Table, ultima: Table) -> list[Table]`: deepcopy de todos los elementos del body desde `primera` hasta `ultima` (inclusive), insertados justo después de `ultima`. Devuelve las tablas clonadas en orden.

- [ ] **Paso 1: Preparar el entorno**

`requirements.txt`: `python-docx==1.1.2`, `PyYAML==6.0.2`, `pytest==8.3.3`. `.gitignore`: `herramientas/sena/.venv/`, `__pycache__/`, `docs/sena/entregables/~$*`.

Ejecutar: `python -m venv herramientas/sena/.venv && herramientas/sena/.venv/Scripts/pip install -r herramientas/sena/requirements.txt`
Resultado esperado: `Successfully installed python-docx-1.1.2 …`

- [ ] **Paso 2: Mover las plantillas** con `mkdir -p docs/sena/plantillas && mv *.docx docs/sena/plantillas/`. Resultado esperado: `ls docs/sena/plantillas` lista los 4 archivos.

- [ ] **Paso 3: Escribir las pruebas que deben fallar**

`conftest.py` define la fixture `doc_prueba`. Crea con python-docx un documento con: un párrafo `"Nombre del proyecto: ________"`; un párrafo `"Limitaciones:"` seguido de `"__________"`; tabla T0 2×2 `[["Campo","Información"],["Ficha",""]]` con el run de la celda (1,1) en negrita y 9 pt; tabla T1 3×3 `[["ID","Nombre","Estado"],["RF-001","","Propuesto"],["RF-002","",""]]`; y tablas T2 y T3 con un párrafo entre ellas.

```python
def test_tabla_con_encabezado_distinto_falla(doc_prueba):
    with pytest.raises(PlantillaCambiadaError, match="T1"):
        tabla(doc_prueba, 1, ["Código"])

def test_tabla_acepta_prefijo_sin_tildes(doc_prueba):
    assert tabla(doc_prueba, 0, ["campo", "informacion"]) is doc_prueba.tables[0]

def test_escribir_celda_conserva_formato(doc_prueba):
    celda = doc_prueba.tables[0].cell(1, 1)
    escribir_celda(celda, "3045678\nsegunda")
    r = celda.paragraphs[0].runs[0]
    assert (r.text, r.bold, r.font.size.pt) == ("3045678", True, 9)
    assert celda.paragraphs[1].runs[0].bold is True

def test_llenar_campos(doc_prueba):
    llenar_campos(doc_prueba.tables[0], {"Ficha": "3045678"})
    assert doc_prueba.tables[0].cell(1, 1).text == "3045678"

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
    assert len(doc_prueba.tables[1].rows) == 4 and doc_prueba.tables[1].cell(1, 0).text == "RF-001"

def test_rellenar_linea_misma_y_siguiente(doc_prueba):
    rellenar_linea(doc_prueba, "Nombre del proyecto:", "AgroConecta")
    rellenar_linea(doc_prueba, "Limitaciones:", "Ninguna")
    textos = [p.text for p in doc_prueba.paragraphs]
    assert "Nombre del proyecto: AgroConecta" in textos and "Ninguna" in textos

def test_clonar_bloque(doc_prueba):
    t2, t3 = doc_prueba.tables[2], doc_prueba.tables[3]
    nuevas = clonar_bloque(t2, t3)
    assert len(nuevas) == 2 and len(doc_prueba.tables) == 6
    assert doc_prueba.tables[4]._tbl is nuevas[0]._tbl
```

- [ ] **Paso 4: Verificar que fallan.** Ejecutar `cd herramientas/sena && .venv/Scripts/python -X utf8 -m pytest tests/test_docx_ops.py -q`. Resultado esperado: `ImportError` / falla de colección.

- [ ] **Paso 5: Implementar `docx_ops.py`** con las firmas de Interfaces. La normalización quita tildes con `unicodedata.normalize("NFKD")`, pasa a minúsculas y colapsa espacios.

- [ ] **Paso 6: Verificar que pasan.** Mismo comando. Resultado esperado: `10 passed`.

- [ ] **Paso 7: Commit**

```bash
git add .gitignore docs/sena/plantillas herramientas/sena
git commit -m "feat(sena): plantillas originales y operaciones sobre docx"
```

---

### Tarea 2: Generador

**Files:**
- Create: `herramientas/sena/plantilla_yaml.py`, `herramientas/sena/generar.py`
- Test: `herramientas/sena/tests/test_generar.py`

**Interfaces:**
- Consumes: todo `docx_ops` (Tarea 1).
- Produces:
  - `plantilla_yaml.cargar_contexto(dir_contenido: Path) -> dict` con las claves `comun` y `catalogo`.
  - `plantilla_yaml.resolver(valor: Any, ctx: dict) -> Any`: recursivo sobre dict/list/str. Sustituye `{{comun.x}}`, `{{rf.ID}}`, `{{hu.ID}}`, `{{cu.ID}}` (→ `"ID — nombre"`). Un marcador desconocido → `KeyError` con el marcador.
  - `plantilla_yaml.expandir_todas(entrada: dict, ctx: dict) -> list[list[str]]`: si `filas == ["{{todas: <coleccion>}}"]`, genera una fila por cada elemento de `catalogo[<coleccion>]` (en orden de ID) formateando cada cadena de `entrada["columnas"]` con `str.format(id=..., **item)`.
  - `generar.generar_documento(yaml_doc: Path, dir_plantillas: Path, dir_salida: Path, ctx: dict) -> Path`
  - CLI: `python -X utf8 generar.py [formulacion|gestion|requisitos|backlog|todos]`

- [ ] **Paso 1: Escribir las pruebas que deben fallar.** Usan la fixture `doc_prueba` guardada como plantilla en `tmp_path` y un YAML mínimo escrito en la prueba.

```python
def test_genera_y_no_toca_plantilla(tmp_path, plantilla_prueba, ctx_prueba): ...
    # el hash de la plantilla es el mismo antes y después; la salida existe

def test_resolver_marcadores(ctx_prueba):
    assert resolver("{{rf.RF-001}} / {{comun.ficha}}", ctx_prueba) == "RF-001 — Registrar usuario / 3045678"

def test_marcador_desconocido_falla(ctx_prueba):
    with pytest.raises(KeyError, match="comun.nada"):
        resolver("{{comun.nada}}", ctx_prueba)

def test_expandir_todas(ctx_prueba):
    filas = expandir_todas({"filas": ["{{todas: requisitos}}"], "columnas": ["{id}", "{nombre}"]}, ctx_prueba)
    assert filas[0] == ["RF-001", "Registrar usuario"]

def test_clonado_no_corre_indices(tmp_path, plantilla_prueba, ctx_prueba):
    # YAML: grupo [2,3] con 2 instancias Y una entrada de tablas con indice 3 llenada DESPUÉS en el YAML;
    # se comprueba que la entrada de índice 3 llenó la tabla original, no un clon
```

`ctx_prueba` es un dict con `comun: {ficha: "3045678"}` y `catalogo: {requisitos: {"RF-001": {nombre: "Registrar usuario"}}}`.

- [ ] **Paso 2: Verificar que fallan** con `.venv/Scripts/python -X utf8 -m pytest tests/test_generar.py -q`. Resultado esperado: FAIL (módulos inexistentes).

- [ ] **Paso 3: Implementar.** Orden obligatorio en `generar_documento`: (1) cargar la plantilla; (2) resolver **todas** las referencias `Table` de `tablas` y `grupos` por índice original y validar sus encabezados; (3) clonar los bloques de los grupos (instancia 1 = la tabla original; instancias 2…n = clones); (4) aplicar `campos`/`filas`/`agregar`; (5) aplicar `lineas`; (6) guardar en `dir_salida/salida`. En los grupos, la clave `encabezado` de cada tabla se toma de una lista `encabezados` paralela a `tablas`.

- [ ] **Paso 4: Verificar que pasan.** Resultado esperado: `5 passed` (más los 10 de la Tarea 1).

- [ ] **Paso 5: Commit** `git commit -m "feat(sena): generador de documentos desde YAML"`

---

### Tarea 3: Catálogo maestro y validador

**Files:**
- Create: `docs/sena/contenido/catalogo.yaml`, `docs/sena/contenido/comun.yaml`, `herramientas/sena/validar.py`
- Test: `herramientas/sena/tests/test_validar.py`, `herramientas/sena/tests/test_catalogo_real.py`

**Interfaces:**
- Produces:
  - Claves de `catalogo.yaml`: `objetivo_general` (str); `objetivos`, `interesados`, `epicas`, `exclusiones` (ID → str); `indicadores` (ID → {nombre, objetivo, meta}); `actores` (ID → {nombre, tipo}); `funcionalidades` (ID → {nombre, epica}); `requisitos` (ID → {nombre, epica, feat, actores: [..], rn: [..], prioridad, version}); `rnf` (ID → {categoria, requisito}); `reglas` (ID → {nombre, texto}); `historias` (ID → {nombre, rf}); `casos_uso` (ID → {nombre, actor, hu: [..]}); `alcance` (ID → {nombre, epica}); `riesgos` (ID → {riesgo, p, i}); `equipo` (EQ → rol); `sprints` (S01 → {inicio, fin, historias}); `hitos` (H-0N → {nombre, fecha}). Contenido = sección "Catálogo maestro" de este plan.
  - `comun.yaml`: `proyecto: AgroConecta`, `programa: Tecnología en Análisis y Desarrollo de Software – ADSO`, `centro`, `regional`, `ficha`, `instructor`, `integrantes` (EQ-01…EQ-04 → nombre). Lo que no se sabe va como `"[PENDIENTE: nombre del centro]"`, etc.
  - `validar.py`:
    - `ids_citados(texto: str) -> set[str]` con la regex `\b(OBJ|IND|STK|ACT|ALC|EXC|RSK)-\d{2}\b|\b(EP|FEAT|RF|RNF|RN|HU|CU)-\d{3}\b`
    - `v1_ids_existen(contenidos: dict[str, Any], catalogo: dict) -> list[str]` (errores)
    - `v2_consistencia_catalogo(catalogo) -> list[str]`: cada HU-n tiene `rf` = RF-n con el mismo nombre; cada RF tiene una épica y una FEAT existentes; cada RN-001…015 lo cita al menos un RF; cada CU cita HU existentes; cada FEAT tiene una épica existente.
    - `v3_residuos(docx: Path, indices_llenados: set[int]) -> list[str]`: en las tablas llenadas, ninguna celda puede contener `___`, `A/M/B`, `Sí / No`, `Alta / Media / B`, `Propuesto / ` ni `novia`.
    - `v4_pendientes(dir_contenido) -> dict[str, list[str]]` y escritura de `docs/sena/PENDIENTES.md`.
    - `v5_criterios_por_historia(backlog_yaml: dict) -> list[str]`: cada HU necesita ≥ 2 filas en la tabla de criterios (índice 18), y al menos una debe tener tipo `Error`.
    - CLI: `python -X utf8 validar.py`. Imprime los errores y sale con código 1 si hay alguno.

- [ ] **Paso 1: Escribir las pruebas del validador** con un mini catálogo construido en la prueba:

```python
def test_ids_citados():
    assert ids_citados("ver RF-012, RN-006 y OBJ-03; no RF-12") == {"RF-012", "RN-006", "OBJ-03"}

def test_ids_citados_existen():
    assert v1_ids_existen({"x.yaml": {"a": ["HU-031"]}}, mini) == ["x.yaml: HU-031 no existe en el catálogo"]

def test_nombres_salen_del_catalogo():  # HU con nombre distinto al de su RF → error
def test_rn_sin_requisito():            # RN-015 sin ningún RF que la cite → error
def test_detecta_residuos_de_plantilla(tmp_path):  # docx con celda "A/M/B" en tabla llenada → error; en tabla no llenada → ok
def test_v5_exige_caso_de_error():
```

- [ ] **Paso 2: Verificar que fallan.** Resultado esperado: `ImportError`.

- [ ] **Paso 3: Implementar `validar.py`.** `indices_llenados` se obtiene de los YAML (`tablas[].indice` y `grupos[].tablas`).

- [ ] **Paso 4: Verificar que pasan.** Resultado esperado: `6 passed`.

- [ ] **Paso 5: Escribir `catalogo.yaml` y `comun.yaml`**, más `test_catalogo_real.py`:

```python
def test_catalogo_real_consistente():
    cat = yaml.safe_load(open(CONTENIDO / "catalogo.yaml", encoding="utf-8"))
    assert v2_consistencia_catalogo(cat) == []
    assert len(cat["requisitos"]) == 30 and len(cat["historias"]) == 30
    assert len(cat["reglas"]) == 15 and len(cat["rnf"]) == 14 and len(cat["casos_uso"]) == 4
    assert sum(len(s["historias"]) for s in cat["sprints"].values() if s["historias"]) == 30
```

(En `sprints`, `historias` lista solo IDs HU; las tareas técnicas de S01, S10 y S11 van en un campo `extra`.)

- [ ] **Paso 6: Verificar que pasa.** Resultado esperado: `1 passed`.

- [ ] **Paso 7: Commit** `git commit -m "feat(sena): catálogo maestro y validador"`

---

### Tareas 4–7: Contenido de cada documento

Las cuatro siguen el mismo ciclo:

1. Escribir `tests/test_<doc>.py`: genera el documento y comprueba las celdas que se indican en cada tarea.
2. Ejecutarlo y confirmar que falla (el YAML no existe).
3. Escribir `docs/sena/contenido/<doc>.yaml`.
4. Ejecutar `generar.py <doc>`, la prueba y `validar.py`. Resultado esperado: prueba en verde y validador sin errores.
5. Abrir el `.docx` generado en Word y revisarlo visualmente (tablas, formato, que no queden filas de ejemplo).
6. Commit del YAML, la prueba y el `.docx` generado.

En cada tabla: **"→"** indica de dónde sale el contenido. "Catálogo" = `catalogo.yaml`; "§" = sección de la especificación. Toda tabla no listada se deja intacta (ver Global Constraints).

Tablas comunes a los cuatro documentos: la portada/identificación (T0, `campos` desde `comun.yaml`); el control documental (`campos`: versión, fecha, estado, propietario = `{{comun.integrantes.EQ-04}}`); el historial (`filas`: las 2 filas de Global Constraints); el registro de aprobaciones (`filas`: los roles de la plantilla con nombre `[PENDIENTE: nombre]` y decisión/fecha vacías).

### Tarea 4: Formulación y Constitución (`formulacion.yaml`)

**Files:** Create `docs/sena/contenido/formulacion.yaml`, `herramientas/sena/tests/test_formulacion.py`; genera `docs/sena/entregables/AgroConecta_Formulacion_y_Constitucion.docx`.

| T | Contenido |
|---|---|
| 0, 1, 2, 3 | Tablas comunes (en este documento T0 es Centro/Regional/…; T1 es el control documental) |
| líneas | "Nombre del proyecto:" → AgroConecta · "Descripción en una frase:" → *Marketplace web que conecta a pequeños productores agrícolas de Colombia con consumidores y negocios para vender sin intermediarios, con pedidos y pago en línea.* · "Objetivo general:" → `catalogo.objetivo_general` · "Limitaciones o excepciones" → *Las decisiones que cambien el alcance del MVP, las fechas de entrega o el stack requieren acuerdo del equipo y visto bueno del instructor.* |
| 6 | Información general (campos) → nombre, descripción, plataforma Web PWA, fechas 2026-11-10 → 2027-06-11, equipo de 4 |
| 7 | Clasificación → Plataforma: Web (PWA); el resto, de §1–2 |
| 8 | Contexto → descripción cualitativa del problema de intermediación (§1.1). Cifras del sector → `[PENDIENTE: dato y fuente]` |
| 9 | Evidencias EVI-01 Entrevista a productores, EVI-02 Precios mayoristas SIPSA (DANE), EVI-03 Revisión de canales de venta actuales. Todas con fuente y hallazgo `[PENDIENTE]` |
| 11 | Enunciado del problema → §1.1 |
| 12 | Árbol: EFE-01 Menor ingreso del productor · EFE-02 Mayor precio para el comprador · EFE-03 Compradores sin conocer el origen · PRO-01 Los pequeños productores dependen de intermediarios para vender · CAU-01 No hay un canal directo con compradores · CAU-02 Desconfianza en pagos entre desconocidos · CAU-03 Los compradores no encuentran productores por zona |
| 13 | Validación del problema → Sí + observación breve en cada pregunta |
| 16 | Justificación (col. 3) → argumentos desde §1, sin cifras |
| 17 | ALT-01 Mantener la situación actual · ALT-02 Vender por redes sociales/WhatsApp · ALT-03 Marketplace genérico existente · ALT-04 AgroConecta (**Seleccionada**). Ventajas/desventajas desde §1.3, §2 y §4 |
| 19, 20 | OBJ-01…05 del catálogo, con entregable, indicador y criterio de logro; SMART con columnas llenas |
| 22 | BEN-01 Mayor margen para el productor (Directo) · BEN-02 Precio más justo y origen conocido para el comprador (Directo) · BEN-03 Compra segura con dinero retenido hasta la entrega (Directo). Reemplaza la fila de ejemplo |
| 23 | Propuesta de valor (1 fila) |
| 24 | IND-01…04 del catálogo; línea base `[PENDIENTE]` donde aplique (IND-01…04 parten de 0) |
| 26 | ALC-01…07 = épicas; usuarios = actores; prioridad Alta; versión MVP |
| 27 | EXC-01…08 con justificación y fase futura "Posterior al MVP" |
| 28 | Los 4 flujos críticos = CU-001…004 |
| 30 | ENTG-01…04 = los 4 documentos (2026-12-04) · ENTG-05 Software MVP desplegado (2027-06-11) · ENTG-06 Informe de pruebas (2027-06-11) · ENTG-07 Manual de usuario (2027-06-11) |
| 31 | HIT = hitos H-01…H-06 del catálogo |
| 32 | Patrocinador: Instructor SENA `{{comun.instructor}}` · Cliente / Product Owner: EQ-04, que representa a los productores · Líder: EQ-01 |
| 33 | Equipo EQ-01…04, disponibilidad `[PENDIENTE: horas/semana]` |
| 34, 35 | Recursos (talento: 4 personas; infraestructura: Vercel/Railway planes gratuitos; Wompi sandbox; costo $0) y viabilidad (Técnica/Económica/Operativa/Legal: Viable o Condicionada con RSK) |
| 36 | Esfuerzo: Formulación y análisis 4 sem · Diseño 2 sem · Construcción 20 sem (S01–S10) · Pruebas y despliegue 2 sem (S11) · Cierre 1 sem. Horas = semanas × 4 × `[PENDIENTE: h/semana]` |
| 38 | RES-01 Temporal: fechas fijas · RES-02 Económica: costo $0 · RES-03 Técnica: pasarela solo en sandbox · RES-04 Recurso: 4 personas |
| 39 | SUP-01…06 = los 6 supuestos de §1.4 |
| 40 | DEP-01 Wompi sandbox (Servicio) · DEP-02 Hosting gratuito (Servicio) · DEP-03 DIVIPOLA DANE (Dato) |
| 43, 44 | RSK-01…06 del catálogo; tratamiento con estrategia Mitigar (Evitar para RSK-02) |
| 51 | Coherencia: PRO-01/CAU-01…03 → OBJ → IND → ALC → RSK |
| 52 | REF-01 Especificación de diseño (repo) · REF-02 Ley 1581 de 2012 · REF-03 Documentación de Wompi · REF-04 DIVIPOLA (DANE) |
| 53 | PEN = todos los `[PENDIENTE]` del documento |

- [ ] **Paso 1: Prueba que debe fallar**

```python
def test_formulacion():
    d = generar_y_abrir("formulacion")
    assert "AgroConecta" in textos_parrafos(d)
    assert [d.tables[19].cell(i, 0).text for i in range(1, 6)] == ["OBJ-01", "OBJ-02", "OBJ-03", "OBJ-04", "OBJ-05"]
    assert "novia" not in tabla_texto(d.tables[22])
    assert d.tables[17].cell(4, 4).text.startswith("Seleccionada")
    assert [d.tables[43].cell(i, 0).text for i in range(1, 7)] == [f"RSK-0{n}" for n in range(1, 7)]
```

(`generar_y_abrir`, `textos_parrafos` y `tabla_texto` son ayudantes que se agregan en `conftest.py`.)

- [ ] **Pasos 2–6:** el ciclo común. Commit: `docs(sena): formulación y constitución de AgroConecta`

### Tarea 5: Gestión de Interesados y del Proyecto (`gestion.yaml`)

**Files:** Create `docs/sena/contenido/gestion.yaml`, `herramientas/sena/tests/test_gestion.py`; genera `AgroConecta_Gestion_de_Interesados_y_del_Proyecto.docx`.

| T | Contenido |
|---|---|
| 0, 2, 3, 4 | Tablas comunes |
| 10, 12 | STK-01…07: tipo, rol, necesidad, interés/influencia (productores A/A, consumidores A/M, negocios A/M, admin M/A, instructor M/A, equipo A/A, Wompi B/M); expectativas y posición |
| 13 | RSK-STK-01 Instructor pide cambios tardíos de alcance · RSK-STK-02 Productores no disponibles para validar (= RSK-05) |
| 14 | COM-01 Equipo: avance diario (Daily) · COM-02 Instructor: avance por hito · COM-03 Productores: validación del problema y prototipo, por hito |
| 15 | Validación por entregable: función = EQ-04 (PO) / instructor; técnica = EQ-01 |
| 16 | EQ-01…04 con los roles del catálogo |
| 17 | RACI: se mantienen las columnas de la plantilla. EQ-01 = Líder + Backend, EQ-02 = Backend + QA, EQ-03 = Frontend + UX/UI, EQ-04 = Analista. Se llenan las letras de las actividades de la plantilla |
| 21 | Metodología: Scrum, sprints de 2 semanas; justificación: equipo de 4, entregas incrementales, backlog priorizado |
| 22 | Flujo de trabajo: acción y responsable por estado |
| 23 | Roadmap H-01…H-06 con fechas de inicio/fin |
| 24 | Sprints S01…S11 con objetivo, historias, entregable, fechas y riesgo principal |
| 25 | BLQ-01 Credenciales sandbox de Wompi (externa) |
| 26 | ACP-01 Entregar los 4 documentos (2026-12-04) |
| 30 | DEC-01 Stack React+NestJS+PostgreSQL · DEC-02 Clean Architecture · DEC-03 Wompi · DEC-04 Recaudo con comisión · DEC-05 PWA en lugar de app nativa · DEC-06 Uso de IA para estructurar la especificación y los borradores de documentación, revisado y aprobado por el equipo |
| 31–34 | RSK-01…06 con categoría; seguimiento: 1 fila inicial por riesgo (2026-12-04) |
| 35 | OP-01 Validar con una asociación de productores local `[PENDIENTE: cuál]` |
| 38 | ENTG-01…07 (los mismos de Formulación) |
| 40 | Reporte de estado a 2026-12-04: Alcance Verde, Cronograma Verde, Riesgos Amarillo (RSK-01, RSK-03) |
| 42 | Contribución individual: 1 fila por integrante, periodo nov–dic 2026, actividades `[PENDIENTE]` |
| 43 | Indicadores de gestión: metas llenas |

- [ ] **Paso 1: Prueba que debe fallar** — comprueba los IDs STK-01…07 en T10, EQ-01…04 en T16, S01 y S11 en T24 con las fechas `2027-01-11` y `2027-06-11`, y que el texto de DEC-06 contiene "IA".
- [ ] **Pasos 2–6:** ciclo común. Commit: `docs(sena): gestión de interesados y del proyecto`

### Tarea 6: Alcance y Especificación de Requisitos (`requisitos.yaml`)

**Files:** Create `docs/sena/contenido/requisitos.yaml`, `herramientas/sena/tests/test_requisitos.py`; genera `AgroConecta_Alcance_y_Especificacion_de_Requisitos.docx`.

| T | Contenido |
|---|---|
| 0, 2, 3, 4 | Tablas comunes |
| 8 | `agregar`: Productor verificado, Pedido, Saldo retenido, Saldo disponible, Liquidación, Comisión, Disputa, Webhook, Sandbox, PWA |
| 11 | Contexto → §1.1 |
| 13, 15, 16 | ALC (catálogo), EXC (catálogo), matriz MVP/posterior |
| 14 | Alcance del proyecto ("Incluye") por categoría: Análisis = los 4 documentos; Construcción = MVP; Pruebas = unitarias, de integración y E2E; Despliegue = Vercel/Railway |
| 17 | RSD = RES, SUP y DEP de Formulación |
| 18 | CA-ALC-01…03 = criterios de éxito de §1.5 |
| 19 | `{{todas: requisitos}}` → ID, nombre, módulo (épica), actor, prioridad, estado `Aprobado`, versión |
| 20 (grupo) | Fichas de RF-012, RF-019 y RF-020, con flujo, reglas, excepciones y criterios desde §4 |
| 22 | Escenarios Dado/Cuando/Entonces: RF-012 (éxito; carrito con 2 productores → 2 pedidos), RF-019 (aprobado; evento duplicado → sin efecto; firma inválida → rechazado), RF-020 (comisión 8 % sobre un subtotal de 50 000 → comisión 4 000, crédito 46 000 + envío), RF-022 (monto mayor al saldo → rechazado) |
| 23 | `{{todas: rnf}}` |
| 24 (grupo) | Fichas de RNF-007 y RNF-013 |
| 27 | `{{todas: reglas}}`, con los RF que la citan (calculado: `rf_que_citan`) |
| 28 (grupo) | Fichas de RN-006 y RN-004 |
| 30 | ACT-01…07 |
| 31 | `nuevo_encabezado` [Recurso / acción, Productor, Comprador, Administrador, Regla o restricción]; filas = matriz de §6 (Visitante en la columna de regla: "Búsqueda y detalle sin sesión") |
| 32, 33, 34 | DAT por entidad de §5 (sensibilidad: Usuario/Perfiles = Personal; Pago/Movimientos = Confidencial; Producto = Público); calidad; privacidad (Ley 1581) |
| 35, 36 (grupo para 36) | INT-01 Wompi (API REST + webhook) · INT-02 Servicio de correo SMTP · INT-03 DIVIPOLA DANE (archivo, carga inicial); ficha de INT-01 |
| 38 | `{{todas: requisitos}}` con MoSCoW = prioridad del catálogo |
| 39 | Roadmap: MVP (2027-06-11, RF-001…030) · Posterior (EXC-01…08) |
| 43 | `{{todas: requisitos}}` → RF, origen (OBJ/STK), RN, HU (+ CU si aplica), Diseño `Pendiente (UX/UI)`, componente `<epica>/application`, prueba `Pendiente (plan de pruebas)` |

Para `rf_que_citan` y la columna CU de la T43, `expandir_todas` pone a disposición dos campos calculados: `rf_que_citan` (para las reglas) y `cu` (para los requisitos, desde `casos_uso[].hu`). Se agregan a `plantilla_yaml.py` junto con la prueba `test_campos_calculados`.

- [ ] **Paso 1: Prueba que debe fallar**

```python
def test_requisitos():
    d = generar_y_abrir("requisitos")
    assert len(d.tables[19].rows) == 31 and d.tables[19].cell(12, 1).text == "Generar pedidos desde el carrito"
    reglas = tabla_por_encabezado(d, ["ID", "Nombre", "Regla", "Fuente"])
    assert len(reglas.rows) == 16 and "RF-020" in reglas.cell(6, 5).text  # fila de RN-006
    assert tabla_por_encabezado(d, ["Recurso / acción"]).cell(0, 1).text == "Productor"
    escenarios = tabla_texto(tabla_por_encabezado(d, ["ID requisito", "Escenario"]))
    assert "4.000" in escenarios
```

(La T19 va antes del primer grupo, así que su índice no cambia. Las tablas que van después de un grupo clonado se buscan con el ayudante `tabla_por_encabezado(d, prefijos)`, que se agrega a `conftest.py`: devuelve la primera tabla cuya fila 0 coincide con los prefijos. Los montos se escriben con punto de miles: `4.000`.)

- [ ] **Pasos 2–6:** ciclo común. Commit: `docs(sena): alcance y especificación de requisitos`

### Tarea 7: Backlog, Historias y Casos de Uso (`backlog.yaml`) + diagrama

**Files:** Create `docs/sena/contenido/backlog.yaml`, `docs/sena/diagramas/casos_de_uso.puml`, `herramientas/sena/tests/test_backlog.py`; genera `docs/sena/diagramas/casos_de_uso.png` y `AgroConecta_Backlog_Historias_y_Casos_de_Uso.docx`.

| T | Contenido |
|---|---|
| 0, 2, 3, 4 | Tablas comunes |
| 8 | `agregar`: los mismos términos de dominio de Requisitos |
| 10 | EP-001…007 con objetivo, STK, IND y estado `Aprobada` |
| 11 | FEAT-001…014 con épica, valor, RF y prioridad |
| 13 | Backlog maestro: 30 HU en el orden de los sprints; valor; prioridad = la del RF; estimación inicial en puntos Fibonacci (marcada "inicial, se re-estima en planning") |
| 15 (grupo) | Fichas de HU-012 y HU-019 |
| 18 | ≥ 2 criterios por HU (al menos uno de tipo `Error`); caso de prueba `CP-HU-0NN-0M` |
| 19 | Escenarios Dado/Cuando/Entonces para HU-012, 013, 015, 019, 020, 022, 025 y 026 (2 cada una) |
| 24 | CU-001…004 del catálogo |
| 25, 26, 27 (grupo) | Ficha + flujo principal + alternativos de cada CU, desde la máquina de estados de §4.2 y RN-001…015. CU-001 incluye la alternativa "pago aprobado sin stock → REEMBOLSADO" |
| 30 | DIA-CU-01 Diagrama general de casos de uso, PlantUML 1.2024.7, `docs/sena/diagramas/casos_de_uso.png`, CU-001…004 |
| 31 | Refinamiento: preguntas abiertas reales (h/semana del equipo, comisión definitiva, mínimo de retiro) |
| 34 | Roadmap = hitos H-02…H-06 con épicas e historias clave |
| 35 | Plan del sprint S01 (HU-001, HU-002 y tareas técnicas) |
| 36 | BLQ-001 Credenciales sandbox de Wompi |
| 38 | `{{todas: historias}}` → HU, RF, RN, actor, UI `Pendiente`, componente `<epica>`, CP |
| 39 | Cobertura: Resultado `Cumple` en cada fila, con la evidencia "validar.py V1/V2/V5" |
| 41 | Metas de indicadores |

- [ ] **Paso 1: Prueba que debe fallar** — comprueba: 30 filas HU en T13; 4 fichas CU (`tabla_por_encabezado` cuenta las tablas cuya celda (1,1) empieza por `CU-00`); que `validar.v5_criterios_por_historia` devuelva `[]`; y que exista `casos_de_uso.png`.
- [ ] **Paso 2:** confirmar que falla.
- [ ] **Paso 3: Escribir `casos_de_uso.puml`** con los actores ACT-01…07 y los CU-001…004, más los casos de uso incluidos derivados de las HU de cada CU. Renderizar con:
  `curl -L -o herramientas/sena/plantuml.jar https://repo1.maven.org/maven2/net/sourceforge/plantuml/plantuml/1.2024.7/plantuml-1.2024.7.jar && java -jar herramientas/sena/plantuml.jar -tpng docs/sena/diagramas/casos_de_uso.puml`
  Agregar `herramientas/sena/plantuml.jar` a `.gitignore`. Resultado esperado: el `.png` existe.
- [ ] **Paso 4: Insertar la imagen** en el `.docx` debajo del encabezado "10.1 Diagrama de contexto de casos de uso". Para eso se agrega al esquema YAML la clave `imagenes: [{despues_de: "10.1 Diagrama de contexto", ruta: ..., ancho_cm: 16}]` y a `docx_ops` la función `insertar_imagen_despues_de(doc, encabezado: str, ruta: Path, ancho_cm: float)`, con la prueba `test_insertar_imagen` en `test_docx_ops.py`.
- [ ] **Pasos 5–7:** YAML, generar, validar, revisión visual y commit: `docs(sena): backlog, historias y casos de uso`

---

### Tarea 8: Cierre y pendientes

**Files:** Modify `docs/sena/PENDIENTES.md` (generado); Create `docs/sena/README.md`

- [ ] **Paso 1:** `cd herramientas/sena && .venv/Scripts/python -X utf8 generar.py todos && .venv/Scripts/python -X utf8 validar.py && .venv/Scripts/python -X utf8 -m pytest -q`. Resultado esperado: 4 `.docx` generados, `validar.py` sin errores (solo el conteo de pendientes) y todas las pruebas en verde.
- [ ] **Paso 2:** abrir los 4 `.docx` en Word, actualizar la tabla de contenido (clic derecho → Actualizar campos) y revisar la paginación. Anotar cualquier problema visual como corrección en el YAML.
- [ ] **Paso 3:** escribir `docs/sena/README.md` (10–15 líneas): cómo editar un YAML, regenerar y validar; que `PENDIENTES.md` lista lo que el equipo debe completar a mano antes del 2026-12-04 (nombres, ficha, evidencias de campo, horas por semana, listas de verificación y firmas).
- [ ] **Paso 4:** commit `docs(sena): entregables generados y lista de pendientes`.
