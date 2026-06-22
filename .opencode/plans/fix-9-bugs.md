# Plan de Corrección — 9 Bugs Visuales Post-Refactors

**Fecha**: 2026-06-21
**Basado en**: AUDIT_VISUAL_REPORT.md + análisis de código fuente

---

## Arquitectura de Solución

```
Phase 1: i18n Foundation (C1 + M4)
  ├── Agregar sección "auth" a es.json / en.json / sv.json
  ├── Reemplazar strings hardcodeados en login.html + register.html
  ├── Migrar ngx-translate a API moderna (useDefaultLang → fallbackLang)
  └── Fix: t.lang → t.language_code en ProductCard + Home (core field-name bug)
        |
Phase 2: Dark Mode CSS Variables (C2 - root cause)
  ├── Agregar overrides de --color-* en html.dark-theme en styles.scss
  ├── Agregar variantes dark: al gradiente del hero
  └── Cambiar fill del wave SVG en dark mode
        |
Phase 3: Dark Mode Component-Specific (C3 + M5)
  ├── Checkout: 14 líneas con variantes dark: faltantes
  └── ProductCard: CONDITION_COLORS con dark: + sombra dark
        |
Phase 4: Language + Currency Switcher (C4)
  ├── Agregar @HostListener('document:click') para close-outside
  ├── Fix markForCheck() en setLang() + setCurrency()
  └── Subscribe a onLangChange / onCurrencyChange para OnPush refresh
        |
Phase 5: Data + Frontend Field Fixes (M1 + M2 + M3)
  ├── M1: getCategoryName() lee campo flat 'name' en vez de 'translations' array
  ├── M2: displayName fallback funciona correctamente tras fix de Phase 1 (t.lang → t.language_code)
  ├── M3: Limpiar productos test de BD o agregar filtro de exclusión
  └── Seed: Insertar traducciones reales ES para categorías
        |
Phase 6: Polish (m1, m2, m3)
  ├── m1: "Not Applicable" → "No especificado" (i18n key)
  ├── m2: Traducir valores de detalle producto (opcional, requiere migración de datos)
  └── m3: Placeholder images en hero cards decorativas
```

---

## Phase 1 — i18n Foundation

### C1: Login/Register completamente en inglés

**Root Cause**: No existe sección `auth` en los 3 locale files. Login/Register templates tienen strings hardcodeados en inglés sin usar `| translate`.

**Archivos a modificar**:
| Archivo | Acción |
|---------|--------|
| `src/assets/i18n/es.json` | Agregar sección `auth` con ~22 keys en español |
| `src/assets/i18n/en.json` | Agregar sección `auth` con ~22 keys en inglés |
| `src/assets/i18n/sv.json` | Agregar sección `auth` con ~22 keys en sueco |
| `src/app/features/auth/login/login.html` | Reemplazar 9 strings hardcodeados + 2 validaciones con `{{ 'auth.key' \| translate }}` y `[label]="'auth.key' \| translate"` |
| `src/app/features/auth/login/login.ts` | Line 50: cambiar `'Login failed'` por `'auth.loginFailed'` |
| `src/app/features/auth/register/register.html` | Reemplazar 13 strings hardcodeados + 4 validaciones |
| `src/app/features/auth/register/register.ts` | Line 50: `'Registration failed'` → `'auth.registrationFailed'` |

**Nuevas keys requeridas** (es.json):
```json
"auth": {
  "signIn": "Iniciar Sesión",
  "email": "Correo electrónico",
  "emailRequired": "El correo es obligatorio",
  "emailInvalid": "Ingresa un correo válido",
  "password": "Contraseña",
  "passwordRequired": "La contraseña es obligatoria",
  "passwordMinLength": "Al menos 8 caracteres",
  "signInButton": "Iniciar Sesión",
  "signInGoogle": "Iniciar sesión con Google",
  "noAccount": "¿No tienes cuenta?",
  "register": "Registrarse",
  "loginFailed": "Error al iniciar sesión",
  "createAccount": "Crear Cuenta",
  "name": "Nombre",
  "nameRequired": "El nombre es obligatorio",
  "confirmPassword": "Confirmar Contraseña",
  "confirmRequired": "Confirma tu contraseña",
  "passwordMismatch": "Las contraseñas no coinciden",
  "createAccountButton": "Crear Cuenta",
  "hasAccount": "¿Ya tienes cuenta?",
  "registrationFailed": "Error al registrarse"
}
```

**Archivos de referencia**: `checkout.html` usa el patrón `{{ 'checkout.key' | translate }}` consistentemente — seguir ese patrón.

---

### M4: Warning ngx-translate deprecated

**Root Cause**: Configuración usa `defaultLanguage` y `useDefaultLang` (deprecados desde ngx-translate 14+).

**Archivos a modificar**:
| Archivo | Línea | Cambio |
|---------|-------|--------|
| `src/app/app-module.ts` | ~25 | `TranslateModule.forRoot({ defaultLanguage: 'es' })` → `TranslateModule.forRoot()` |
| `src/app/app.ts` | ~19 | `this.translate.setDefaultLang('es')` — esto ya es correcto, verificar que sea la única init |

**Nota**: El warning viene de la configuración del módulo. Basta con quitar `defaultLanguage` de `TranslateModule.forRoot()` — el servicio ya hace `setDefaultLang('es')` en `app.ts`.

---

### Fix Crítico de Campo (afecta C1, M1, M2)

**Root Cause**: La API de productos y categorías expone el campo de traducción como `language_code`, pero el frontend lo lee como `lang`. Todas las funciones `getDisplayName()` y `getCategoryName()` fallan silenciosamente.

**Archivos a modificar**:
| Archivo | Función | Cambio |
|---------|---------|--------|
| `src/app/shared/components/product-card/product-card.ts` | `displayName` getter (L74-88) | `t.lang` → `t.language_code` |
| `src/app/features/home/home.ts` | `getDisplayName()` (L81-84) | `t.lang` → `t.language_code` |
| `src/app/features/home/home.ts` | `getCategoryName()` (L76-79) | `t.lang` → `t.language_code` + usar campo flat `cat.name` |

---

## Phase 2 — Dark Mode CSS Variables (Root Cause para C2, C3, M5)

### C2: Hero de Home no se adapta a dark mode

**Root Cause**: El bloque `html.dark-theme` en `styles.scss` **NO sobreescribe** los design tokens `--color-bg`, `--color-text`, `--color-primary`, `--color-text-secondary`. Define variables nuevas (`--bg-primary`, `--text-primary`) que ningún template usa. El wave SVG tiene `fill="#FAF9F6"` hardcodeado.

**Archivos a modificar**:
| Archivo | Acción |
|---------|--------|
| `src/styles.scss` | Agregar overrides de design tokens en bloque `html.dark-theme` |
| `src/app/features/home/home.html` | Agregar `dark:` al gradiente del hero + wave SVG dinámico |

**Cambios específicos en `styles.scss`** (bloque `html.dark-theme` actual + nuevos overrides):
```scss
html.dark-theme {
  // Design tokens — SOBREESCRIBIR los existentes, no crear nuevos
  --color-bg: #0f172a;              // slate-900 (antes: #FAF9F6 crema)
  --color-text: #f1f5f9;            // slate-100 (antes: #1A1A2E navy)
  --color-text-secondary: #94a3b8;  // slate-400 (antes: #6B7280)
  --color-primary: #4ade80;         // green-400 (antes: #2D6A4F)
  
  // Mantener los existentes que ya están
  --bg-primary: #1e1e2e;
  --bg-secondary: #2a2a3c;
  --text-primary: #cdd6f4;
  --text-secondary: #a0a0b0;

  body {
    background-color: var(--color-bg);  // Usar el token, no #121212 hardcodeado
    color: var(--color-text);
  }
}
```

**Cambios en `home.html` — gradiente del hero** (línea 4):
```html
<!-- Antes -->
<div class="absolute inset-0 bg-gradient-to-br from-green-900 via-green-700 to-emerald-600">

<!-- Después -->
<div class="absolute inset-0 bg-gradient-to-br from-green-900 via-green-700 to-emerald-600
            dark:from-gray-950 dark:via-emerald-950 dark:to-teal-950">
```

**Wave SVG** (línea 76): cambiar `fill="#FAF9F6"` por un color que use CSS variable. Alternativa: usar `fill="currentColor"` + clase `text-[var(--color-bg)]`.

---

## Phase 3 — Dark Mode Component-Specific

### C3: Checkout dark mode ilegible

**Root Cause**: Cero variantes `dark:` en todo `checkout.html`. SCSS vacío (sin conflictos).

**Archivo a modificar**: `src/app/features/checkout/checkout.html`

**Cambios específicos** (14 líneas):

| Elemento | Cambio |
|----------|--------|
| h1 "Finalizar Compra" | `text-gray-900` → `text-gray-900 dark:text-gray-100` |
| Div overlay | `bg-white` → `bg-white dark:bg-gray-800` |
| Texto overlay | `text-gray-700` → `text-gray-700 dark:text-gray-300` |
| Error message | `text-red-600` → `text-red-600 dark:text-red-400` |
| Card envío | `bg-white` → `bg-white dark:bg-gray-800` |
| h2 "Dirección de Envío" | Agregar `text-gray-900 dark:text-gray-100` |
| Card resumen | `bg-white` → `bg-white dark:bg-gray-800` |
| h2 "Resumen del Pedido" | Agregar `text-gray-900 dark:text-gray-100` |
| Divisor items | `divide-gray-200` → `divide-gray-200 dark:divide-gray-700` |
| Nombre producto | `text-gray-900` → `text-gray-900 dark:text-gray-100` |
| "Cantidad: X" | `text-gray-500` → `text-gray-500 dark:text-gray-400` |
| "Total" label | Agregar `text-gray-900 dark:text-gray-100` |
| Monto total | Agregar `text-gray-900 dark:text-gray-100` |

---

### M5: Cards de productos fondos claros en dark mode

**Root Cause**: `CONDITION_COLORS` en `condition-badge.component.ts` no tiene variantes `dark:`. Sombra de `product-card.scss` invisible en dark mode.

**Archivos a modificar**:
| Archivo | Acción |
|---------|--------|
| `src/app/shared/components/product-card/condition-badge.component.ts` | Agregar `dark:bg-*-900/40 dark:text-*-200 dark:border-*-700` a cada entrada de `CONDITION_COLORS` |
| `src/app/shared/components/product-card/product-card.scss` | Agregar media query o clase para sombra clara en dark mode |

**CONDITION_COLORS fix**:
```typescript
const CONDITION_COLORS: Record<string, string> = {
  new: 'bg-green-100 dark:bg-green-900/40 text-green-800 dark:text-green-200 border-green-300 dark:border-green-700',
  like_new: 'bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-200 border-blue-300 dark:border-blue-700',
  good: 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-800 dark:text-yellow-200 border-yellow-300 dark:border-yellow-700',
  fair: 'bg-orange-100 dark:bg-orange-900/40 text-orange-800 dark:text-orange-200 border-orange-300 dark:border-orange-700',
  fallback: 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 border-gray-300 dark:border-gray-600',
};
```

**Sombra fix en product-card.scss**:
```scss
.product-card-enhanced {
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
    
    :host-context(.dark-theme) & {
      box-shadow: 0 12px 32px rgba(255, 255, 255, 0.06);
    }
  }
}
```

---

## Phase 4 — Language + Currency Switcher

### C4: Selector de idioma roto

**Root Cause**: 
1. **No close-outside**: Solo usa eventos `mouseenter`/`mouseleave`, sin `@HostListener('document:click')`.
2. **No markForCheck()**: `setLang()` llama a `translate.use(lang)` (asíncrono) pero no refresca el componente OnPush. El badge queda mostrando "ES" aunque el idioma haya cambiado.
3. **Mismo bug en currency-switcher**.

**Archivos a modificar**:
| Archivo | Acción |
|---------|--------|
| `src/app/layout/header/components/language-switcher.component.ts` | Agregar `@HostListener('document:click')` + `markForCheck()` en `setLang()` + suscribir a `onLangChange` |
| `src/app/layout/header/components/currency-switcher.component.ts` | Mismos fixes (close-outside + markForCheck + onCurrencyChange) |

**Cambios en language-switcher.component.ts**:
```typescript
// 1. Inyectar ElementRef
private readonly elementRef = inject(ElementRef);

// 2. Click-outside handler
@HostListener('document:click', ['$event'])
onDocumentClick(event: MouseEvent): void {
  const target = event.target as HTMLElement;
  if (!this.elementRef.nativeElement.contains(target)) {
    this.langOpen = false;
    this.cdr.markForCheck();
  }
}

// 3. Fix setLang
protected setLang(lang: string): void {
  this.translate.use(lang);
  this.langOpen = false;
  this.cdr.markForCheck();
}

// 4. Suscribir a onLangChange para OnPush refresh
private langSub?: Subscription;

ngOnInit(): void {
  this.langSub = this.translate.onLangChange.subscribe(() => {
    this.cdr.markForCheck();
  });
}

ngOnDestroy(): void {
  this.langSub?.unsubscribe();
  // ... cleanup timeout existente
}
```

Mismos cambios en `currency-switcher.component.ts` (inyectar `ElementRef`, agregar `@HostListener('document:click')`, `cdr.markForCheck()` en `setCurrency()`, suscribir a `onCurrencyChange`).

---

## Phase 5 — Data + Frontend Field Fixes

### M1: Categorías en inglés

**Root Cause (doble)**:
1. La API `/api/categories?lang=es` devuelve `{ id, slug, name }` con `name` ya pre-traducido (campo flat). Pero `getCategoryName()` busca `cat.translations` (array) que no existe en la respuesta flat.
2. El seed script inserta el nombre en inglés para ambos `en` y `es`.

**Archivos a modificar**:
| Archivo | Acción |
|---------|--------|
| `src/app/features/home/home.ts:76-79` | `getCategoryName()`: usar `cat.name` directamente en vez de buscar en `cat.translations` |
| `backend/scripts/seed_dataset.py:152-153` | Insertar traducciones reales ES para categorías |
| `backend/scripts/seed_parquet.py:99-100` | Igual — traducciones reales ES |

**Fix en home.ts**:
```typescript
// Antes:
getCategoryName(cat: any): string {
  const t = cat?.translations?.find((t: any) => t.lang === 'es');
  return t?.name ?? '';
}

// Después:
getCategoryName(cat: any): string {
  return cat?.name ?? '';  // La API ya devuelve 'name' pre-traducido según ?lang=
}
```

**Fix en seed scripts**: Agregar un diccionario de traducciones ES reales (ej. `"jacket"` → `"Chaqueta"`, `"dress"` → `"Vestido"`, etc.) y usarlo al insertar `CategoryTranslation`.

---

### M2 + M3: Productos test/placeholder en home y catálogo

**Root Cause (doble)**:
1. Los tests de backend (`test_seed_integrity.py`) insertan ~60 productos con slugs tipo `boundary-{uid}`, `empty-cond-{uid}`, `batch-{uid}-N` **sin limpiar después**. Estos persisten en la BD.
2. El fallback `displayName` funcionaba con slugs (stripea UUID → capitaliza), y el bug `t.lang` vs `t.language_code` hacía que nunca se usaran las traducciones reales.

**Nota**: El bug `t.lang` → `t.language_code` se arregla en Phase 1. Al hacerlo, los productos SIN traducción ES caerán al fallback EN, y si no tienen traducción EN, al slug formateado. Los productos test seguirán apareciendo.

**Archivos a modificar**:
| Archivo | Acción |
|---------|--------|
| `backend/tests/test_seed_integrity.py` | Agregar cleanup al final de cada test (DELETE de productos insertados) |
| (Opcional) script de limpieza | DELETE FROM products WHERE slug LIKE 'boundary-%' OR slug LIKE 'empty-cond-%' OR slug LIKE 'positive-%' OR slug LIKE 'partial-cond-%' OR slug LIKE 'material-%' OR slug LIKE 'swedish-%' OR slug LIKE 'multi-lang-%' OR slug LIKE 'batch-%' |

---

## Phase 6 — Polish (Menores)

### m1: "Not Applicable" → "No especificado"

- Agregar key `common.notApplicable` en es.json con valor `"No especificado"`, en.json con `"Not specified"`, en sv.json con `"Ej specificerat"`
- En `ProductCardComponent`, cuando el campo esté vacío, usar `{{ 'common.notApplicable' | translate }}` en vez del string literal

### m2: Datos de detalle en inglés

**Opcional** — los valores como "100% cotton", "Floral print", etc. vienen de la BD. Traducirlos requeriría un mapper de valores en frontend o migración de datos. Baja prioridad.

### m3: Hero cards con imagen placeholder

Cosmético — las 3 cards decorativas del hero muestran ícono de imagen rota. Reemplazar el `src` con imágenes reales o íconos inline. Alternativa: eliminarlas o usar un SVG placeholder decorativo.

---

## Resumen de Archivos por Fase

### Phase 1 (i18n foundation) — 6 archivos
- `src/assets/i18n/es.json` (+22 keys `auth`)
- `src/assets/i18n/en.json` (+22 keys `auth`)
- `src/assets/i18n/sv.json` (+22 keys `auth`)
- `src/app/features/auth/login/login.html` (9 strings → translate)
- `src/app/features/auth/register/register.html` (13 strings → translate)
- `src/app/app-module.ts` (quitar `defaultLanguage`)

### Phase 1.5 (field-name bugfix) — 2 archivos
- `src/app/shared/components/product-card/product-card.ts` (`t.lang` → `t.language_code`)
- `src/app/features/home/home.ts` (`t.lang` → `t.language_code`, + flat `cat.name`)

### Phase 2 (dark mode CSS) — 2 archivos
- `src/styles.scss` (overrides de `--color-*` en `html.dark-theme`)
- `src/app/features/home/home.html` (gradiente `dark:` + wave SVG)

### Phase 3 (dark mode components) — 3 archivos
- `src/app/features/checkout/checkout.html` (14 líneas con `dark:`)
- `src/app/shared/components/product-card/condition-badge.component.ts` (CONDITION_COLORS)
- `src/app/shared/components/product-card/product-card.scss` (sombra dark)

### Phase 4 (switcher bugs) — 2 archivos
- `src/app/layout/header/components/language-switcher.component.ts` (~20 líneas)
- `src/app/layout/header/components/currency-switcher.component.ts` (~20 líneas)

### Phase 5 (data + field fixes) — 3 archivos
- `backend/scripts/seed_dataset.py` (traducciones ES reales)
- `backend/scripts/seed_parquet.py` (traducciones ES reales)
- `backend/tests/test_seed_integrity.py` (cleanup teardown)

### Phase 6 (polish) — 3 archivos
- `src/assets/i18n/es.json` (+`common.notApplicable`)
- `src/assets/i18n/en.json` (+`common.notApplicable`)
- `src/assets/i18n/sv.json` (+`common.notApplicable`)

**Total**: ~20 archivos modificados, ~150 líneas de cambios netos (~70 adiciones en i18n files, ~80 en código).

---

## Orden de Ejecución Recomendado

```
1. Phase 1  — i18n foundation (C1 + M4)
2. Phase 5  — Field name bugfix (t.lang → t.language_code) + seed fix
3. Phase 2  — Dark mode CSS variables (root cause para C2, C3, M5)
4. Phase 3  — Dark mode component-specific (C3 checkout + M5 product-card)
5. Phase 4  — Language + currency switcher (C4)
6. Phase 6  — Polish (m1, m2, m3)

Verificación entre fases:
  - pnpm run build (sin errores TypeScript)
  - Playwright smoke tests en las 8 rutas
  - Verificar consola: 0 errors, 0 warnings
```

---

## Dependencias entre Bugs

```
C1 (login/register i18n) ─┐
                          ├──> Ambos requieren Phase 1 (i18n keys)
M4 (ngx-translate warn)  ─┘

   Fix campo t.lang ──────┬──> Requerido por M1 (categorías) y M2 (productos test)

C2 (hero dark) ──────────┬──> Ambos requieren Phase 2 (CSS variables)
C3 (checkout dark) ──────┤
M5 (product-card dark) ──┘

C4 (lang switcher) ───── standalone, no depende de otros fixes
   (currency switcher) ── mismo archivo, mismo patrón

M1 (categorías inglés) ── depende de fix t.lang + campo flat
M2 (productos test) ───── depende de fix t.lang + BD cleanup
M3 (catálogo tests) ──── mismo root que M2
```

---

## Riesgos y Mitigaciones

| Riesgo | Mitigación |
|--------|-----------|
| `--color-*` CSS variables usadas en componentes que aún no auditamos | Revisar `grep -r "var(--color-" src/` antes de aplicar Phase 2 |
| ngx-translate carga asíncrona — flicker al aplicar idioma | El patrón `| translate` + `setDefaultLang('es')` ya maneja esto en el resto de la app |
| Cleanup de BD rompe tests existentes | Hacer teardown por test, no limpieza masiva |
| Cambios en seed scripts rompen CI | Verificar que el seed pipeline siga funcionando tras cambios de traducción |
