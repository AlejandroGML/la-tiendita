# Auditoría Visual Post-Refactors — TiendaVirtual

**Fecha**: 2026-06-21
**Frontend**: http://localhost:4200
**Backend**: http://localhost:8000
**Consola**: 0 errors, 2 warnings (deprecación `useDefaultLang` ngx-translate)

## Resumen Ejecutivo

| Categoría | Light Mode | Dark Mode | i18n |
|---|---|---|---|
| Home | ⚠️ Categorías en inglés, productos test | ❌ Hero verde claro no adapta | — |
| Catálogo | ⚠️ Solo productos placeholder | ✅ OK | — |
| Detalle producto | ✅ OK | ✅ OK | — |
| Carrito | ✅ OK | ✅ OK | — |
| Checkout | ✅ OK | ❌ Texto casi invisible | — |
| Login | ❌ **100% en inglés** | ❌ Igual + textos invisibles | — |
| Register | ❌ **100% en inglés** | ❌ Igual | — |
| Wishlist | (redirige a login) | — | — |
| Lang switcher | ❌ Menú persiste abierto, no cambia idioma | ❌ Igual | — |

**Total bugs visuales**: 9 (4 críticos, 5 medios)

---

## CRÍTICOS (bloquean producción)

### 🔴 C1. Login/Register completamente en inglés
- **Rutas**: `/login`, `/register`
- **Síntoma**: Todo el form está en inglés hardcodeado ("Sign In", "Email", "Password", "Create Account", "Name", "Confirm Password", "Email is required", etc.)
- **Causa probable**: Formularios con strings literales en vez de usar el pipe `translate`. Refactor post-frontend no migró estos componentes al sistema i18n.
- **Impacto**: 100% de los usuarios no-ingles ven un producto roto, y un usuario registrado en ES verá campos en otro idioma.
- **Capturas**: `audit-login-light.png`, `audit-register-light.png`

### 🔴 C2. Hero de Home no se adapta a dark mode
- **Síntoma**: El banner verde brillante del hero (degradado verde claro con texto blanco) se mantiene idéntico en dark mode. Lo mismo las cards decorativas (TOP VENTAS / NUEVO / OFERTA) con imagen placeholder.
- **Causa probable**: El gradiente verde está hardcodeado con clases que no incluyen variantes `dark:`.
- **Impacto**: Destruye la experiencia dark mode, además de tener problemas de contraste WCAG (texto blanco sobre verde claro en light mode también es bajo).
- **Captura**: `audit-home-dark3.png` (sección superior verde claro)

### 🔴 C3. Checkout dark mode ilegible
- **Síntoma**: En dark mode, los títulos de sección ("Dirección de Envío", "Resumen del Pedido") y labels ("Total") usan texto gris muy claro sobre fondo casi negro, casi invisibles. Botón "Confirmar Pedido" se ve desaturado. Inputs tienen fondo negro y texto blanco invisible.
- **Causa probable**: Componente checkout usa colores que no respetan las variantes `dark:` de Tailwind.
- **Impacto**: Checkout inutilizable en dark mode.
- **Captura**: `audit-checkout-dark.png`

### 🔴 C4. Selector de idioma roto (menú no cierra, cambio no funciona)
- **Síntoma**: Al hacer click en el botón de idioma (ES), se abre un dropdown con Español/English/Svenska. Pero (a) el menú no se cierra al hacer click fuera ni al elegir opción; (b) elegir English no cambia el idioma de la página.
- **Causa probable**: Falta handler de close-outside-click o el servicio de i18n no está suscrito al evento. El dropdown queda montado en el DOM permanentemente.
- **Impacto**: UX rota, el menú tapa la esquina superior derecha de todas las páginas.
- **Capturas**: `audit-productos-dark.png`, `audit-detalle-dark2.png`, `audit-checkout-dark.png` (menú visible en todas)

---

## MEDIOS

### 🟡 M1. Categorías en INGLÉS en home y footer
- **Síntoma**: El carrusel de categorías en home muestra nombres en inglés (accessories, bag, belt, blazer, blouse, boots, cardigan, coat, dress, hat, heels, jacket). El footer también muestra "Jackets, Dresses, Jeans, Sweaters" en inglés.
- **Causa probable**: El campo `name` en la BD de categorías está en inglés, y la UI muestra el campo raw sin traducir.
- **Impacto**: Inconsistencia grave — el resto de la UI está en español pero estos elementos en inglés.
- **Captura**: `audit-home-light.png`

### 🟡 M2. Productos destacados son fixtures de tests
- **Síntoma**: El grid de "Productos Destacados" muestra: "Empty Cond", "Partial Cond", "Multi Lang", "Swedish", "Material", "Positive", "Boundary F7ac8fa4 5", "Boundary F7ac8fa4 1", "Boundary F7ac8fa4 3", "Batch 86e18bf4 5", "Batch 86e18bf4 4", "Batch 86e18bf4 6".
- **Causa probable**: Los seeds/importers de tests metieron productos con nombres de fixtures (Boundary = propiedad `boundary` de los tests de Go; Batch = `batch_id`). El query "destacados" los está trayendo.
- **Impacto**: Es lo que ve el usuario cuando entra a la home. Hay que limpiar la BD o filtrar productos con esos nombres.
- **Captura**: `audit-home-light.png`

### 🟡 M3. Catálogo muestra solo productos placeholder
- **Síntoma**: Los 12 productos de la primera página del catálogo son los mismos fixtures de test. Solo 1 producto real (Odd Molly Top) está visible. La página dice "692 producto(s) encontrados" pero los 12 primeros son tests.
- **Causa probable**: Misma raíz que M2 — los productos de test son mayoría en la BD y aparecen primero por orden de creación.
- **Captura**: `audit-productos-light.png`

### 🟡 M4. Warning ngx-translate deprecado
- **Síntoma**: 2 warnings en consola sobre `useDefaultLang` y `defaultLanguage` deprecados, debe usarse `fallbackLang`.
- **Causa**: Configuración de ngx-translate con opciones deprecadas.
- **Impacto**: No bloquea, pero ensucia la consola y avisa que en próxima versión se romperá.
- **Fix**: Una línea en el módulo de i18n.

### 🟡 M5. Cards de productos dark mode tienen fondo claro
- **Síntoma**: En el grid de productos destacados (home dark), las cards mantienen fondo claro (gris claro) en lugar de fondo oscuro. Lo mismo con el grid del catálogo.
- **Causa probable**: `bg-white` o `bg-gray-50` sin variante `dark:bg-gray-800` en el ProductCard component.
- **Impacto**: Visual inconsistente con el resto de la página en dark mode.
- **Captura**: `audit-home-dark3.png` (sección "Productos Destacados")

---

## MENORES

### 🟢 m1. Categoría "Not Applicable" en filtros y cards
- **Síntoma**: Algunas cards y opciones muestran "Not Applicable" como marca o tipo. Es porque el campo está vacío en la BD.
- **Impacto**: Cosmético. Refactor de i18n debería traducir "Not Applicable" a "No especificado" o similar.

### 🟢 m2. Datos de detalle producto en inglés
- **Síntoma**: En el detalle, los labels de Material, Colores, Patrón, Corte, Tendencia, Temporada, Género, Uso están en español (✅), pero los valores como "100% cotton", "Floral print", "Loose", "No trend", "Summer", "Ladies", "Reuse" están en inglés.
- **Causa**: La BD tiene esos datos en inglés. No es bug de UI, pero podría traducirse en frontend.

### 🟢 m3. Cards de "TOP VENTAS/NUEVO/OFERTA" con imagen rota
- **Síntoma**: El hero muestra 3 cards decorativas con badge (TOP VENTAS, NUEVO, OFERTA) y un placeholder de imagen rota (ícono de imagen tachada).
- **Impacto**: Cosmético, son decorativas.

---

## Estado del Funcional Core

| Funcionalidad | Estado |
|---|---|
| Header | ✅ Funciona, dropdown categorías, búsqueda, navegación |
| Footer | ✅ Funciona, categorías hardcodeadas en inglés (M1) |
| Filtros | ✅ 11 filtros visibles y funcionales en `/productos` |
| Paginación | ✅ Funciona, 5 páginas, 12 items/pág |
| Producto card → detalle | ✅ Navega correctamente |
| Carrito agregar/eliminar | ✅ Funciona, datos de producto se muestran correctamente |
| Checkout flow | ✅ Estructura OK, dark mode roto (C3) |
| Auth flow | ❌ Login/Register en inglés (C1) |
| Wishlist | ❌ Redirige a login cuando no hay sesión (esperado, pero login roto) |
| Dark mode toggle | ⚠️ Funciona, pero rompe varias páginas (C2, C3, M5) |
| Cambio de idioma | ❌ No funciona (C4) |
| Cambio de moneda | ⚠️ No testeado (botón "kr" presente, no se cambió) |

---

## Recomendaciones (ordenadas por impacto)

1. **[CRIT]** Arreglar i18n de Login/Register — extraer strings a archivos de traducción
2. **[CRIT]** Adaptar Hero al dark mode — agregar variantes `dark:` al gradiente
3. **[CRIT]** Arreglar contraste de Checkout en dark mode
4. **[CRIT]** Arreglar dropdown de idioma (close-outside-click + handler de cambio)
5. **[MED]** Limpiar BD de productos test/placeholder (seeds), o filtrarlos en queries de "destacados"
6. **[MED]** Traducir nombres de categorías de la BD o usar campo localized
7. **[MED]** Actualizar ngx-translate a API moderna (quitar `useDefaultLang`/`defaultLanguage`)
8. **[MED]** Agregar variantes `dark:` a ProductCard backgrounds

## Archivos Relacionados
- `frontend/src/app/pages/login/` — login.component.html/ts/scss
- `frontend/src/app/pages/register/` — register.component.html/ts/scss
- `frontend/src/app/pages/checkout/` — checkout.component.html/ts/scss
- `frontend/src/app/pages/home/` — home.component.html/ts (hero, categorías)
- `frontend/src/app/shared/components/language-switcher/` — language-switcher.component
- `frontend/src/app/shared/components/theme-toggle/` — theme-toggle.component
- `frontend/src/app/shared/components/product-card/` — product-card.component
- `frontend/src/app/core/i18n/` — configuración ngx-translate
- `frontend/src/app/core/services/theme.service.ts` — toggle dark mode
- `backend/app/models/category.py` — modelo de categoría
- `backend/app/models/product.py` — modelo de producto
- `backend/seeders/`, `backend/scripts/seed_*.py` — posible fuente de productos test

## Capturas Generadas
- `audit-home-light.png` / `audit-home-dark.png` / `audit-home-dark3.png`
- `audit-productos-light.png` / `audit-productos-dark.png` / `audit-productos-en.png`
- `audit-detalle.png` / `audit-detalle-dark2.png`
- `audit-cart-empty.png` / `audit-cart-dark.png`
- `audit-login-light.png`
- `audit-register-light.png`
- `audit-wishlist.png` (redirige a login)
- `audit-checkout.png` / `audit-checkout-dark.png`
- `audit-lang-menu.png` (dropdown idioma)
