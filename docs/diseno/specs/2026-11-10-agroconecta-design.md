# AgroConecta — Especificación de diseño

- **Fecha:** 2026-11-10
- **Estado:** Aprobado en conversación; pendiente de revisión escrita
- **Equipo:** 4 personas (proyecto formativo SENA – ADSO)

---

## 1. Propósito y entendimiento acordado

### 1.1 Problema y objetivo

Los pequeños productores agrícolas de Colombia venden a través de intermediarios que capturan buena parte del margen. **AgroConecta** es un marketplace que conecta directamente a productores con compradores (consumidores finales y negocios) e incluye pedidos y pago en línea dentro de la plataforma.

### 1.2 Entregables y plazos

| Entregable | Fecha | Contenido |
|---|---|---|
| Documentación SENA | Primera semana de diciembre de 2026 | Las 4 plantillas llenas: Formulación y Constitución, Gestión de Interesados y del Proyecto, Alcance y Especificación de Requisitos, Backlog/Historias/Casos de Uso |
| Software (MVP) | Junio de 2027 | Plataforma descrita en esta especificación, desplegada y funcionando en modo sandbox |

Esta especificación define **el producto**. De ella salen el contenido de las plantillas y la base del código. Llenar las plantillas y construir el software se planifican por separado.

### 1.3 Decisiones del usuario

- Compradores de dos tipos: **consumidor final** y **negocio** (restaurantes, tiendas, fruvers).
- Cobertura: **toda Colombia**.
- Pedidos dentro de la plataforma con **pago en línea**.
- La plataforma **recauda**, retiene una **comisión** y **liquida** al productor cuando el pedido se entrega. La pasarela opera en **modo sandbox**.
- Plataforma **web responsive instalable (PWA)**.
- Stack libre; elegido: **React + NestJS + PostgreSQL** con **Clean Architecture**.

### 1.4 Supuestos confirmados por el usuario

1. La plataforma **no gestiona transporte**. El productor ofrece entrega a domicilio (con zona y costo), recogida por el comprador, o ambas. El productor marca "enviado", el comprador confirma "recibido" y eso libera el pago.
2. Un **administrador** verifica a los productores antes de que puedan vender, resuelve disputas y gestiona liquidaciones.
3. La búsqueda es por producto, categoría y departamento/municipio. **Sin mapa ni geolocalización** en el MVP.
4. El comprador **califica** al productor después de recibir el pedido.
5. **Facturación electrónica DIAN fuera de alcance.** Se entrega un comprobante del pedido.
6. El productor fija precio por unidad (kg, bulto, docena, etc.) y puede definir **precios por volumen**.

### 1.5 Criterios de éxito

- **Diciembre:** las 4 plantillas llenas, consistentes entre sí y trazables (objetivos → requisitos → historias → casos de uso).
- **Junio:** se puede recorrer de punta a punta este flujo: un productor se registra, es verificado y publica productos → un comprador hace un pedido y lo paga en sandbox → el pedido se entrega y se confirma → la comisión y el saldo del productor quedan registrados → el productor solicita una liquidación y el administrador la marca como pagada.

---

## 2. Stack tecnológico

| Capa | Tecnología |
|---|---|
| Frontend | React + Vite + TypeScript, Tailwind CSS, PWA (service worker + manifest) |
| Backend | NestJS + TypeScript, API REST |
| Base de datos | PostgreSQL + Prisma ORM |
| Pagos | Wompi (sandbox): tarjeta, PSE, Nequi; confirmación por webhook |
| Pruebas | Jest (unitarias e integración), Playwright (E2E) |
| CI | GitHub Actions: lint + pruebas + build en cada pull request |
| Despliegue | Frontend en Vercel; API y base de datos en Railway o Render |

Alternativas descartadas: monolito Next.js (frontera front/back difusa, difícil de documentar y repartir entre el equipo) y BaaS con Supabase/Firebase (la lógica de dinero quedaría repartida en funciones sueltas, sin backend propio).

---

## 3. Arquitectura del backend (Clean Architecture)

### 3.1 Capas por módulo

```
src/modules/<modulo>/
├── domain/          entidades, value objects, reglas de negocio, interfaces de repositorio
├── application/     casos de uso, DTOs, puertos
├── infrastructure/  repositorios Prisma, adaptador Wompi, almacenamiento de imágenes
└── presentation/    controladores REST, validación de entrada, guards
```

**Reglas de dependencia:**

- Las dependencias apuntan hacia adentro: `presentation` → `application` → `domain`; `infrastructure` implementa los puertos de `application`/`domain`.
- `domain` es TypeScript puro: no importa NestJS, Prisma ni ninguna librería externa.
- Cada caso de uso es una clase con un único método `ejecutar()`.
- La pasarela se accede mediante el puerto `PasarelaPagos`; `WompiAdapter` es la implementación. En las pruebas se usa un doble falso.
- NestJS (inyección de dependencias, decoradores) se usa solo en `infrastructure` y `presentation`.

### 3.2 Módulos

| # | Módulo | Responsabilidad |
|---|---|---|
| 1 | Identidad | Registro, login (JWT + refresh token), roles, eliminación de cuenta |
| 2 | Productores | Perfil de productor, verificación por el administrador, opciones de entrega |
| 3 | Catálogo | Productos, categorías, unidades, precios por volumen, imágenes, búsqueda |
| 4 | Pedidos | Carrito, creación de pedidos, máquina de estados |
| 5 | Pagos | Cobro Wompi, webhook, retención, comisión, saldo, liquidaciones, reembolsos |
| 6 | Reputación | Calificaciones de productores |
| 7 | Administración | Verificación, disputas, configuración (comisión, mínimo de retiro), reportes |

**Comunicación entre módulos:** mediante eventos de dominio internos (por ejemplo, `PagoAprobado`, `PedidoEntregado`, `PedidoReembolsado`), no con llamadas directas entre módulos.

### 3.3 Frontend

Organizado por funcionalidad (`src/features/catalogo`, `src/features/pedidos`, …), con un cliente HTTP tipado para la API. Vistas por rol: productor, comprador y administrador.

---

## 4. Flujo del pedido y del dinero

### 4.1 División del carrito

Un pedido pertenece a **un solo productor**. Al pagar un carrito con productos de N productores se crean N pedidos y **un único cobro** en Wompi (entidad `Pago` que cubre los N pedidos).

### 4.2 Máquina de estados del pedido

| Desde | Evento | Hacia |
|---|---|---|
| PENDIENTE_PAGO | Webhook Wompi: transacción APROBADA | PAGADO |
| PENDIENTE_PAGO | Webhook APROBADA pero sin stock suficiente (RN-04) | REEMBOLSADO |
| PENDIENTE_PAGO | Webhook: transacción rechazada, o 30 min sin pago | CANCELADO |
| PAGADO | El productor acepta | ACEPTADO |
| PAGADO | El productor rechaza, o 48 h sin respuesta | REEMBOLSADO |
| ACEPTADO | El productor marca despachado / listo para recoger | ENVIADO |
| ENVIADO | El comprador confirma recepción | ENTREGADO |
| ENVIADO | 7 días sin confirmación ni disputa | ENTREGADO (automático) |
| ENVIADO | El comprador abre disputa | EN_DISPUTA |
| EN_DISPUTA | El administrador resuelve a favor del productor | ENTREGADO |
| EN_DISPUTA | El administrador resuelve a favor del comprador | REEMBOLSADO |

Cualquier otra transición es inválida y la entidad `Pedido` la rechaza con `TransicionInvalidaError`. CANCELADO, ENTREGADO y REEMBOLSADO son estados finales.

### 4.3 Reglas de negocio

| Código | Regla |
|---|---|
| RN-01 | Solo los productores con estado VERIFICADO pueden publicar o activar productos. |
| RN-02 | Un pedido contiene productos de un único productor. |
| RN-03 | El precio unitario de cada ítem se congela al crear el pedido. Si la cantidad alcanza un umbral de `PrecioVolumen`, se aplica el precio del umbral más alto alcanzado. |
| RN-04 | El stock se descuenta al pasar a PAGADO y se restituye si un pedido que estuvo PAGADO termina en REEMBOLSADO. El stock no se reserva al crear el pedido: si al llegar el pago aprobado ya no alcanza, ese pedido pasa directamente a REEMBOLSADO (sin descontar stock) y los demás pedidos del mismo cobro siguen su curso. |
| RN-05 | El dinero de un pedido pagado queda **retenido** hasta que el pedido pasa a ENTREGADO. |
| RN-06 | Al pasar a ENTREGADO: `comision = round(subtotal × porcentaje_comision)`; se acredita al productor `subtotal − comision + costo_envio`. |
| RN-07 | El porcentaje de comisión lo configura el administrador (por defecto 8 %). Cada pedido guarda el porcentaje vigente cuando se creó. |
| RN-08 | El costo de envío lo define el productor según su zona/modalidad, se cobra con el pedido y no paga comisión. La recogida tiene costo 0. |
| RN-09 | El saldo disponible del productor es la suma de sus `MovimientoSaldo`; nunca se guarda como un valor editable. |
| RN-10 | El productor puede solicitar una liquidación por un monto ≤ saldo disponible y ≥ mínimo configurado. La solicitud crea un movimiento RETIRO; el administrador la marca PAGADA después de transferir por fuera. |
| RN-11 | El reembolso es siempre total (subtotal + envío) y se ejecuta mediante la pasarela (simulado en sandbox). |
| RN-12 | Los montos se manejan en pesos colombianos (COP) como enteros. Nunca se usan números flotantes para dinero. |
| RN-13 | El webhook es idempotente (se registra el id de cada evento procesado) y se verifica su firma antes de procesarlo. |
| RN-14 | Solo se puede calificar un pedido ENTREGADO, una vez, y solo lo puede hacer su comprador (1–5 estrellas y comentario opcional). |
| RN-15 | Solo se puede abrir disputa sobre un pedido en estado ENVIADO, y solo lo puede hacer su comprador. |

---

## 5. Modelo de datos

| Entidad | Campos principales | Relaciones |
|---|---|---|
| Usuario | correo (único), hash de contraseña, rol, estado, fecha de aceptación de tratamiento de datos | 1:1 PerfilProductor o PerfilComprador |
| PerfilProductor | nombre de la finca, documento, municipio, estado de verificación (PENDIENTE/VERIFICADO/RECHAZADO), ofrece domicilio, zona y costo de envío, ofrece recogida, dirección de recogida | 1:N Producto |
| PerfilComprador | tipo (CONSUMIDOR/NEGOCIO), razón social y NIT (si es negocio), direcciones | 1:N Pedido |
| Categoria | nombre | 1:N Producto |
| Producto | nombre, descripción, unidad, precio, stock, imágenes, activo | N:1 PerfilProductor, N:1 Categoria, 1:N PrecioVolumen |
| PrecioVolumen | cantidad mínima, precio unitario | N:1 Producto |
| Pedido | estado, modalidad de entrega, dirección, subtotal, costo de envío, porcentaje de comisión, comisión, marcas de tiempo por estado | N:1 comprador, N:1 productor, N:1 Pago, 1:N ItemPedido |
| ItemPedido | cantidad, precio unitario congelado | N:1 Pedido, N:1 Producto |
| Pago | referencia Wompi, monto total, estado | 1:N Pedido |
| EventoWebhook | id del evento (único), tipo, fecha de procesamiento | — |
| MovimientoSaldo | tipo (CREDITO_PEDIDO/RETIRO), monto, fecha | N:1 productor; referencia a Pedido o Liquidacion |
| Liquidacion | monto, estado (SOLICITADA/PAGADA), fechas | N:1 productor |
| Disputa | motivo, evidencia (imágenes), resolución, resuelta por | 1:1 Pedido |
| Calificacion | estrellas (1–5), comentario | 1:1 Pedido |
| Departamento / Municipio | código DANE, nombre | precargados |
| Configuracion | porcentaje de comisión, mínimo de retiro | registro único |

---

## 6. Roles y permisos

| Acción | Productor | Comprador | Admin |
|---|---|---|---|
| Publicar y editar sus productos | ✅ (solo si está verificado) | — | — |
| Buscar productos y comprar | — | ✅ | — |
| Aceptar, rechazar y despachar pedidos | ✅ (solo los suyos) | — | — |
| Confirmar recepción, abrir disputa, calificar | — | ✅ (solo los suyos) | — |
| Ver saldo y solicitar liquidación | ✅ (solo el suyo) | — | — |
| Verificar productores, resolver disputas, marcar liquidaciones como pagadas, configurar comisión | — | — | ✅ |

La búsqueda y el detalle del catálogo son públicos (sin iniciar sesión); para comprar hay que iniciar sesión.

---

## 7. Alcance

### 7.1 MVP (junio de 2027)

- Los 7 módulos con el comportamiento de las secciones 3 a 6.
- Notificaciones dentro de la app y por correo para los cambios de estado del pedido, la verificación y las liquidaciones.
- PWA instalable y responsive.
- Pasarela Wompi en modo sandbox.

### 7.2 Fuera del MVP

Notificaciones push, chat entre productor y comprador, mapa y geolocalización, facturación electrónica DIAN, pago contraentrega, logística o transporte, app nativa, operación con dinero real.

---

## 8. Manejo de errores

- El dominio lanza errores de negocio tipados (`TransicionInvalidaError`, `StockInsuficienteError`, `ProductorNoVerificadoError`, etc.).
- Un filtro de excepciones en `presentation` los traduce a HTTP: 404 cuando no existe, 403 por permisos, 409 por conflictos de estado, 422 cuando se viola una regla de negocio y 400 cuando la entrada es inválida.
- Todas las respuestas de error tienen la forma `{ codigo, mensaje, detalles? }`. El frontend muestra `mensaje`.
- Las operaciones de dinero son atómicas, cada una en una sola transacción de base de datos:
  - Pago aprobado → pedidos a PAGADO + descuento de stock + registro del evento del webhook.
  - Pedido ENTREGADO → cálculo de comisión + MovimientoSaldo CREDITO_PEDIDO.
  - Reembolso → estado REEMBOLSADO + restitución de stock.
  - Solicitud de liquidación → Liquidacion + MovimientoSaldo RETIRO.
- Los plazos automáticos (30 min, 48 h, 7 días) los aplica un job programado cada 5 minutos, y es idempotente.

---

## 9. Seguridad y cumplimiento

- JWT de acceso de corta duración (15 min) más refresh token. Contraseñas con bcrypt.
- Autorización por rol y por propiedad del recurso en guards.
- Validación de entrada en todos los endpoints. Límite de intentos en el login.
- Verificación de la firma del webhook de Wompi.
- Ley 1581 de 2012 (habeas data): consentimiento explícito al registrarse y opción de eliminar la cuenta.

---

## 10. Estrategia de pruebas

| Nivel | Alcance | Herramienta |
|---|---|---|
| Unitarias (la mayoría) | Entidades y casos de uso sin base de datos: máquina de estados, comisión, precios por volumen, división del carrito, reglas RN-01 a RN-15 | Jest |
| Integración | Repositorios Prisma contra PostgreSQL de prueba; flujo del webhook (incluida la idempotencia) | Jest + PostgreSQL de prueba |
| End-to-end | Camino principal del criterio de éxito de junio | Playwright |

CI con GitHub Actions: lint, pruebas y build en cada pull request.

---

## 11. Relación con las plantillas SENA

| Plantilla | Contenido que sale de esta especificación |
|---|---|
| Formulación y Constitución | Problema (intermediación), objetivos, criterios de éxito (§1.5), plazos y equipo |
| Gestión de Interesados y del Proyecto | Interesados: productores, consumidores, negocios, administrador, equipo, instructor SENA. Cronograma diciembre 2026 → junio 2027. Riesgos: integración con la pasarela, alcance, curva de aprendizaje del stack |
| Alcance y Especificación de Requisitos | RF por módulo (§3.2), RNF (§9, PWA, pruebas), reglas de negocio RN-01 a RN-15 (§4.3), matriz de roles (§6), datos (§5), integración con Wompi, MVP vs. posteriores (§7) |
| Backlog, Historias y Casos de Uso | Épicas = los 7 módulos. Historias con criterios Given/When/Then. Casos de uso de los procesos complejos: **CU Realizar pedido y pago**, **CU Gestionar ciclo del pedido**, **CU Resolver disputa**, **CU Liquidar saldo** |
