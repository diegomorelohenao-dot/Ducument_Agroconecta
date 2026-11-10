# Documentación SENA de AgroConecta

Los 4 documentos de `entregables/` se **generan**. No se editan a mano en Word, salvo las firmas y las listas de verificación.

| Carpeta | Contenido |
|---|---|
| `plantillas/` | Plantillas institucionales originales (no se modifican) |
| `contenido/` | Texto de cada documento en YAML. `catalogo.yaml` es la fuente única de IDs y nombres (RF, HU, RN, CU…); `comun.yaml` tiene los datos de identificación |
| `diagramas/` | Diagrama de casos de uso (`.puml` fuente y `.png`) |
| `entregables/` | Documentos generados para entregar |
| `PENDIENTES.md` | Lo que el equipo debe completar antes del 2026-12-04 |

## Cambiar algo

1. Edite el YAML en `contenido/`. Para renombrar un requisito o una historia, cámbielo **solo** en `catalogo.yaml`.
2. Regenere y valide desde `herramientas/sena/`:

   ```bash
   .venv/Scripts/python -X utf8 generar.py todos
   .venv/Scripts/python -X utf8 validar.py      # 0 errores = IDs consistentes y sin restos de la plantilla
   .venv/Scripts/python -X utf8 -m pytest -q
   ```

3. Al abrir cada documento, Word ofrece actualizar los campos: acepte para que la tabla de contenido quede con las páginas correctas.

Primera vez: `python -m venv .venv && .venv/Scripts/pip install -r requirements.txt` (dentro de `herramientas/sena/`).
Para redibujar el diagrama: `java -jar plantuml.jar -tpng ../../docs/sena/diagramas/casos_de_uso.puml` (PlantUML 1.2024.7 desde Maven Central).

## Antes de entregar

- Complete todo lo de `PENDIENTES.md`: nombres del equipo, evidencias de campo, horas por semana y enlaces.
- Llene a mano en Word las listas de verificación (columna «Cumple»), los registros de aprobación y las firmas.
- Revise el contenido: es un borrador generado con ayuda de IA (decisión DEC-06 en Gestión) y el equipo es responsable de él.
