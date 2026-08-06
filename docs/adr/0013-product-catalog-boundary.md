# ADR-0013

## Título

`Product` es un catálogo de productos SaaS, no un producto SaaS en sí mismo.

## Estado

Aceptado

## Fecha

2026-08-03

---

## Contexto

CH-TECH V2 introduce la entidad `Product` (ver DATA_MODEL.md) para mostrar los productos SaaS propios de la empresa en la landing. Existe un riesgo de diseño real: que `Product` empiece como un simple registro de catálogo (nombre, descripción, estado, URL) y termine absorbiendo, con el tiempo, funcionalidad propia de cada producto — tenants, planes, facturación, usuarios finales — dentro de la misma base de datos y el mismo backend que sirve el sitio corporativo de CH-TECH.

ADR-0003 ya estableció que CH-TECH únicamente tiene autenticación administrativa y que "los futuros productos SaaS tendrán su propio sistema de autenticación". Esa decisión ya apunta en la dirección correcta, pero no fue escrita pensando en una entidad `Product` explícita — conviene confirmarla ahora, en el momento en que esa entidad se agrega al dominio, para que no quede ambigua a medida que existan productos SaaS reales.

---

## Decisión

`Product` en CH-TECH es exclusivamente un registro de catálogo: qué productos existen, en qué estado (`WAITLIST` / `BETA` / `LIVE`), y dónde vivir para usarlos. No almacena tenants, usuarios finales, planes ni facturación.

Cada producto SaaS real tiene su propio repositorio, su propia base de datos, su propio dominio y su propio sistema de autenticación — independiente del backend de CH-TECH. El backend de CH-TECH nunca es la base de datos operativa de un producto SaaS; solo lo referencia desde `Product.url`.

Esta ADR reafirma el alcance de ADR-0003 para el contexto específico de `Product` y queda como referencia obligatoria antes de agregar cualquier campo a `Product` que implique estado operativo de un producto (usuarios, planes, uso) en vez de estado de catálogo (visibilidad, descripción).

---

## Alternativas

- **Modelar tenants y planes dentro de CH-TECH desde ahora, previendo crecimiento.** Se descarta por abstracción prematura: no existe todavía un producto SaaS real que lo necesite, y el costo de extraerlo después (cuando sí exista) es menor que el costo de mantener esa complejidad sin uso ahora.

---

## Consecuencias

### Positivas

- El dominio de CH-TECH permanece simple: sigue siendo "sitio de empresa con catálogo de contenido", no un backend multi-tenant.
- Cada producto SaaS puede elegir su propio stack sin quedar atado a las decisiones de ADR-0005 (SQLAlchemy/Alembic/Pydantic) ni a la escala de la instancia EC2 de ADR-0011.

### Negativas

- El primer producto SaaS real requerirá su propia infraestructura desde el día uno; no hay reuso directo del backend de CH-TECH más allá del catálogo.

---

## Referencias

ADR-0003, ADR-0005, ADR-0011, DATA_MODEL.md (entidad Product)
