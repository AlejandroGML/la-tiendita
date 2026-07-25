# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: admin/admin.spec.ts >> Admin Panel >> non-admin cannot access admin routes
- Location: tests/admin/admin.spec.ts:105:7

# Error details

```
Error: expect(received).toContain(expected) // indexOf

Expected substring: "/login"
Received string:    "http://localhost:4200/admin"
```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - link "Saltar al contenido principal" [ref=e2] [cursor=pointer]:
    - /url: "#main-content"
  - generic [ref=e3]:
    - banner [ref=e5]:
      - generic [ref=e8]:
        - link "LT La Tiendita" [ref=e9] [cursor=pointer]:
          - /url: /
          - generic [ref=e10]: LT
          - generic [ref=e11]: La Tiendita
        - generic [ref=e15]:
          - generic [ref=e16]: 
          - combobox "Buscar productos..." [ref=e17]
        - navigation "Navegación principal" [ref=e18]:
          - link "Ayuda" [ref=e19] [cursor=pointer]:
            - /url: /ayuda
            - img [ref=e21]
            - generic [ref=e23]: Ayuda
          - generic "Favoritos" [ref=e26] [cursor=pointer]:
            - generic [ref=e27]: 
          - link "Carrito" [ref=e29] [cursor=pointer]:
            - /url: /carrito
            - img [ref=e31]
          - button "Admin" [ref=e37] [cursor=pointer]:
            - img [ref=e39]
            - generic [ref=e42]: Admin
            - img [ref=e44]
          - button "Cambiar idioma" [ref=e48] [cursor=pointer]:
            - img [ref=e50]
            - generic [ref=e53]: ES
          - button "Cambiar moneda" [ref=e56] [cursor=pointer]: SEK
          - button "Modo oscuro" [ref=e58] [cursor=pointer]:
            - img [ref=e59]
      - navigation "Categorías" [ref=e63]:
        - generic [ref=e66]:
          - button " Categorías " [ref=e69] [cursor=pointer]:
            - generic [ref=e70]: 
            - generic [ref=e71]: Categorías
            - generic [ref=e72]: 
          - generic [ref=e73]:
            - link "Ofertas" [ref=e74] [cursor=pointer]:
              - /url: /productos?oferta=true
              - img [ref=e76]
              - text: Ofertas
            - link "Nuevo" [ref=e78] [cursor=pointer]:
              - /url: /productos?sort=newest
              - img [ref=e80]
              - text: Nuevo
            - link "Más popular" [ref=e82] [cursor=pointer]:
              - /url: /productos?sort=popular
              - img [ref=e84]
              - text: Más popular
          - generic [ref=e87]:
            - img [ref=e89]
            - text: Compra segura
        - generic [ref=e93]:
          - button "Mujer" [ref=e94] [cursor=pointer]
          - button "Hombre" [ref=e95] [cursor=pointer]
          - button "Kids" [ref=e96] [cursor=pointer]
          - button "Unisex" [ref=e97] [cursor=pointer]
    - main [ref=e98]:
      - generic [ref=e100]:
        - complementary [ref=e101]:
          - generic [ref=e103]:
            - generic [ref=e104]: LT
            - generic [ref=e105]:
              - heading "La Tiendita" [level=2] [ref=e106]
              - text: Panel Admin
          - navigation [ref=e107]:
            - link " Dashboard" [ref=e108] [cursor=pointer]:
              - /url: /admin
              - generic [ref=e109]: 
              - generic [ref=e110]: Dashboard
            - link " Productos" [ref=e111] [cursor=pointer]:
              - /url: /admin/productos
              - generic [ref=e112]: 
              - generic [ref=e113]: Productos
            - link " Usuarios" [ref=e114] [cursor=pointer]:
              - /url: /admin/usuarios
              - generic [ref=e115]: 
              - generic [ref=e116]: Usuarios
            - link " Órdenes" [ref=e117] [cursor=pointer]:
              - /url: /admin/ordenes
              - generic [ref=e118]: 
              - generic [ref=e119]: Órdenes
            - link " Categorías" [ref=e120] [cursor=pointer]:
              - /url: /admin/categorias
              - generic [ref=e121]: 
              - generic [ref=e122]: Categorías
            - link " Promociones" [ref=e123] [cursor=pointer]:
              - /url: /admin/promociones
              - generic [ref=e124]: 
              - generic [ref=e125]: Promociones
          - link " Volver a la tienda" [ref=e127] [cursor=pointer]:
            - /url: /
            - generic [ref=e128]: 
            - text: Volver a la tienda
        - generic [ref=e129]:
          - generic [ref=e130]:
            - generic [ref=e132]: / dashboard
            - generic [ref=e133]:
              - generic [ref=e134]:
                - generic [ref=e135]: A
                - generic [ref=e136]:
                  - generic [ref=e137]: Admin
                  - generic [ref=e138]: admin@example.com
              - button [ref=e139] [cursor=pointer]:
                - generic [ref=e140]: 
          - main [ref=e141]:
            - generic [ref=e142]:
              - heading "Dashboard" [level=1] [ref=e143]
              - generic [ref=e144]:
                - generic [ref=e145]:
                  - generic [ref=e147]:
                    - generic [ref=e149]: 
                    - generic [ref=e150]:
                      - paragraph [ref=e151]: Productos Totales
                      - paragraph [ref=e152]: "299"
                  - generic [ref=e154]:
                    - generic [ref=e156]: 
                    - generic [ref=e157]:
                      - paragraph [ref=e158]: Usuarios Totales
                      - paragraph [ref=e159]: "260"
                  - generic [ref=e161]:
                    - generic [ref=e163]: 
                    - generic [ref=e164]:
                      - paragraph [ref=e165]: Órdenes Totales
                      - paragraph [ref=e166]: "0"
                  - generic [ref=e168]:
                    - generic [ref=e170]: 
                    - generic [ref=e171]:
                      - paragraph [ref=e172]: Ingresos Totales
                      - paragraph [ref=e173]: 0,00 SEK
                  - generic [ref=e175]:
                    - generic [ref=e177]: 
                    - generic [ref=e178]:
                      - paragraph [ref=e179]: Órdenes Pendientes
                      - paragraph [ref=e180]: "0"
                  - generic [ref=e182]:
                    - generic [ref=e184]: 
                    - generic [ref=e185]:
                      - paragraph [ref=e186]: Órdenes Confirmadas
                      - paragraph [ref=e187]: "0"
                  - generic [ref=e189]:
                    - generic [ref=e191]: 
                    - generic [ref=e192]:
                      - paragraph [ref=e193]: Órdenes Enviadas
                      - paragraph [ref=e194]: "0"
                  - generic [ref=e196]:
                    - generic [ref=e198]: 
                    - generic [ref=e199]:
                      - paragraph [ref=e200]: Órdenes Entregadas
                      - paragraph [ref=e201]: "0"
                  - generic [ref=e203]:
                    - generic [ref=e205]: 
                    - generic [ref=e206]:
                      - paragraph [ref=e207]: Reseñas Totales
                      - paragraph [ref=e208]: "0"
                  - generic [ref=e210]:
                    - generic [ref=e212]: 
                    - generic [ref=e213]:
                      - paragraph [ref=e214]: Valoración Promedio
                      - paragraph [ref=e215]: 0.0 ★
                  - generic [ref=e217]:
                    - generic [ref=e219]: 
                    - generic [ref=e220]:
                      - paragraph [ref=e221]: Promociones Activas
                      - paragraph [ref=e222]: "0"
                  - generic [ref=e224]:
                    - generic [ref=e226]: 
                    - generic [ref=e227]:
                      - paragraph [ref=e228]: Ingresos del Mes
                      - paragraph [ref=e229]: 0,00 SEK
                  - generic [ref=e231]:
                    - generic [ref=e233]: 
                    - generic [ref=e234]:
                      - paragraph [ref=e235]: Órdenes del Mes
                      - paragraph [ref=e236]: "0"
                - generic [ref=e237]:
                  - generic [ref=e238]:
                    - heading "Órdenes Recientes" [level=2] [ref=e240]
                    - table [ref=e243]:
                      - rowgroup [ref=e244]:
                        - row "Usuario Total Estado Fecha" [ref=e245]:
                          - columnheader "Usuario" [ref=e246]
                          - columnheader "Total" [ref=e247]
                          - columnheader "Estado" [ref=e248]
                          - columnheader "Fecha" [ref=e249]
                      - rowgroup [ref=e250]:
                        - row "No hay órdenes" [ref=e251]:
                          - cell "No hay órdenes" [ref=e252]
                  - generic [ref=e253]:
                    - heading "Usuarios Recientes" [level=2] [ref=e255]
                    - table [ref=e258]:
                      - rowgroup [ref=e259]:
                        - row "Nombre Email Rol Creado" [ref=e260]:
                          - columnheader "Nombre" [ref=e261]
                          - columnheader "Email" [ref=e262]
                          - columnheader "Rol" [ref=e263]
                          - columnheader "Creado" [ref=e264]
                      - rowgroup [ref=e265]:
                        - row "Logout Tester test-1784971774298-soequ@example.com Cliente Jul 25, 2026" [ref=e266]:
                          - cell "Logout Tester" [ref=e267]
                          - cell "test-1784971774298-soequ@example.com" [ref=e268]
                          - cell "Cliente" [ref=e269]:
                            - generic [ref=e270]: Cliente
                          - cell "Jul 25, 2026" [ref=e271]
                        - row "Login Tester test-1784971767798-bgptj@example.com Cliente Jul 25, 2026" [ref=e272]:
                          - cell "Login Tester" [ref=e273]
                          - cell "test-1784971767798-bgptj@example.com" [ref=e274]
                          - cell "Cliente" [ref=e275]:
                            - generic [ref=e276]: Cliente
                          - cell "Jul 25, 2026" [ref=e277]
                        - row "E2E Test User test-1784971764708-zuwtg@example.com Cliente Jul 25, 2026" [ref=e278]:
                          - cell "E2E Test User" [ref=e279]
                          - cell "test-1784971764708-zuwtg@example.com" [ref=e280]
                          - cell "Cliente" [ref=e281]:
                            - generic [ref=e282]: Cliente
                          - cell "Jul 25, 2026" [ref=e283]
                        - row "Logout Tester test-1784971718636-eiipj@example.com Cliente Jul 25, 2026" [ref=e284]:
                          - cell "Logout Tester" [ref=e285]
                          - cell "test-1784971718636-eiipj@example.com" [ref=e286]
                          - cell "Cliente" [ref=e287]:
                            - generic [ref=e288]: Cliente
                          - cell "Jul 25, 2026" [ref=e289]
                        - row "Login Tester test-1784971714440-u0mx6@example.com Cliente Jul 25, 2026" [ref=e290]:
                          - cell "Login Tester" [ref=e291]
                          - cell "test-1784971714440-u0mx6@example.com" [ref=e292]
                          - cell "Cliente" [ref=e293]:
                            - generic [ref=e294]: Cliente
                          - cell "Jul 25, 2026" [ref=e295]
    - generic [ref=e298]:
      - generic [ref=e299]:
        - generic [ref=e300]:
          - heading "La Tiendita" [level=3] [ref=e301]
          - paragraph [ref=e302]: Tu tienda de ropa segunda mano favorita. Calidad, estilo y sostenibilidad en cada prenda.
          - generic [ref=e303]:
            - generic "Facebook" [ref=e304] [cursor=pointer]:
              - generic [ref=e305]: 
            - generic "Instagram" [ref=e306] [cursor=pointer]:
              - generic [ref=e307]: 
            - generic "Twitter" [ref=e308] [cursor=pointer]:
              - generic [ref=e309]: 
        - generic [ref=e310]:
          - heading "Enlaces Rápidos" [level=4] [ref=e311]
          - list [ref=e312]:
            - listitem [ref=e313]:
              - link "Productos" [ref=e314] [cursor=pointer]:
                - /url: /productos
            - listitem [ref=e315]:
              - link "Carrito" [ref=e316] [cursor=pointer]:
                - /url: /carrito
            - listitem [ref=e317]:
              - link "Iniciar Sesión" [ref=e318] [cursor=pointer]:
                - /url: /login
        - generic [ref=e319]:
          - heading "Categorías" [level=4] [ref=e320]
          - list [ref=e321]:
            - listitem [ref=e322]:
              - link "Blazer" [ref=e323] [cursor=pointer]:
                - /url: /productos?category_id=140
            - listitem [ref=e324]:
              - link "Blusa" [ref=e325] [cursor=pointer]:
                - /url: /productos?category_id=141
            - listitem [ref=e326]:
              - link "Cárdigan" [ref=e327] [cursor=pointer]:
                - /url: /productos?category_id=142
        - generic [ref=e328]:
          - heading "Contacto" [level=4] [ref=e329]
          - list [ref=e330]:
            - listitem [ref=e331]:
              - generic [ref=e332]: 
              - generic [ref=e333]: hello@latiendita.cl
            - listitem [ref=e334]:
              - generic [ref=e335]: 
              - generic [ref=e336]: +56 9 1234 5678
            - listitem [ref=e337]:
              - generic [ref=e338]: 
              - generic [ref=e339]: Santiago, Chile
        - text:   
      - generic [ref=e340]:
        - generic [ref=e341]: © 2026 La Tiendita. Todos los derechos reservados.
        - generic [ref=e342]:
          - link "Privacidad" [ref=e343] [cursor=pointer]:
            - /url: /privacidad
          - link "Términos" [ref=e344] [cursor=pointer]:
            - /url: /terminos
    - generic:     
    - generic:
      - alertdialog
    - generic [ref=e346]:
      - paragraph [ref=e348]:
        - text: 🍪 Utilizamos cookies esenciales y funcionales para que la tienda funcione correctamente. También utilizamos cookies de análisis opcionales si nos das tu consentimiento.
        - link "Más información" [ref=e349] [cursor=pointer]:
          - /url: /privacidad
        - text: .
      - generic [ref=e350]:
        - button "Solo esenciales" [ref=e352] [cursor=pointer]:
          - generic [ref=e353]: Solo esenciales
        - button "Personalizar" [ref=e355] [cursor=pointer]:
          - generic [ref=e356]: Personalizar
        - button "Aceptar todo" [ref=e358] [cursor=pointer]:
          - generic [ref=e359]: Aceptar todo
```

# Test source

```ts
  9   |   test.beforeEach(async ({ page, request }) => {
  10  |     await page.goto('/', { waitUntil: 'commit' });
  11  |     await login(request, page, ADMIN_EMAIL, ADMIN_PASSWORD);
  12  |   });
  13  | 
  14  |   test.afterEach(async ({ page }) => {
  15  |     await clearTokens(page);
  16  |   });
  17  | 
  18  |   test('admin dashboard shows stats cards', async ({ page }) => {
  19  |     await page.goto('/admin');
  20  |     await page.waitForLoadState('networkidle');
  21  | 
  22  |     // Should see either stats or an error (if no admin access/permissions)
  23  |     const statsOrError = page.locator(S.adminDashboard).or(page.locator(S.adminDashboardError));
  24  |     await expect(statsOrError).toBeVisible({ timeout: 10_000 });
  25  | 
  26  |     // If stats loaded, verify at least one stat card
  27  |     const statsVisible = await page.locator(S.adminDashboard).isVisible();
  28  |     if (statsVisible) {
  29  |       const statCards = page.locator('.stat-card');
  30  |       const count = await statCards.count();
  31  |       expect(count).toBeGreaterThanOrEqual(1);
  32  |     }
  33  |   });
  34  | 
  35  |   test('admin products page shows table or empty state', async ({ page }) => {
  36  |     await page.goto('/admin/productos');
  37  |     await page.waitForLoadState('networkidle');
  38  | 
  39  |     // Either products table, empty state, or error
  40  |     const content = page
  41  |       .locator(S.adminProductsTable)
  42  |       .or(page.locator(S.adminNoProducts))
  43  |       .or(page.locator(S.adminProductsError));
  44  |     await expect(content).toBeVisible({ timeout: 10_000 });
  45  |   });
  46  | 
  47  |   test('new product button navigates to form', async ({ page }) => {
  48  |     await page.goto('/admin/productos');
  49  |     await page.waitForLoadState('networkidle');
  50  |     await page.waitForTimeout(2_000);
  51  | 
  52  |     const newBtn = page.locator(S.adminNewProductButton);
  53  |     const isBtnVisible = await newBtn.isVisible().catch(() => false);
  54  | 
  55  |     if (!isBtnVisible) {
  56  |       // Page might show error or loading — skip gracefully
  57  |       test.skip(true, 'Admin products page not fully loaded');
  58  |       return;
  59  |     }
  60  | 
  61  |     await newBtn.click();
  62  |     // Should navigate to /admin/productos/nuevo
  63  |     await expect(page).toHaveURL(/\/admin\/productos\/nuevo/);
  64  |   });
  65  | 
  66  |   test('admin orders page is accessible', async ({ page }) => {
  67  |     await page.goto('/admin/ordenes');
  68  |     await page.waitForLoadState('networkidle');
  69  | 
  70  |     // Page should render without crashing
  71  |     await expect(page.locator('h1')).toBeVisible({ timeout: 10_000 });
  72  |   });
  73  | 
  74  |   test('admin users page is accessible', async ({ page }) => {
  75  |     await page.goto('/admin/usuarios');
  76  |     await page.waitForLoadState('networkidle');
  77  | 
  78  |     // Page should render without crashing
  79  |     await expect(page.locator('h1')).toBeVisible({ timeout: 10_000 });
  80  |   });
  81  | 
  82  |   test('admin dashboard retry works after error', async ({ page }) => {
  83  |     // First intercept to fail
  84  |     await page.route('**/api/v1/admin/stats**', (route) => {
  85  |       route.fulfill({ status: 500, body: JSON.stringify({ error: 'Boom' }) });
  86  |     });
  87  | 
  88  |     await page.goto('/admin');
  89  |     await page.waitForTimeout(3_000);
  90  | 
  91  |     await expect(page.locator(S.adminDashboardError)).toBeVisible({ timeout: 5_000 });
  92  | 
  93  |     // Now let the retry succeed
  94  |     await page.unroute('**/api/v1/admin/stats');
  95  |     await page.route('**/api/v1/admin/stats**', (route) => route.continue());
  96  | 
  97  |     await page.locator(S.adminDashboardRetry).click();
  98  |     await page.waitForTimeout(3_000);
  99  | 
  100 |     // Should recover
  101 |     const statsOrError = page.locator(S.adminDashboard).or(page.locator(S.adminDashboardError));
  102 |     await expect(statsOrError).toBeVisible({ timeout: 5_000 });
  103 |   });
  104 | 
  105 |   test('non-admin cannot access admin routes', async ({ page }) => {
  106 |     await clearTokens(page);
  107 |     await page.goto('/admin');
  108 |     await page.waitForTimeout(5_000);
> 109 |     expect(page.url()).toContain('/login');
      |                        ^ Error: expect(received).toContain(expected) // indexOf
  110 |   });
  111 | });
  112 | 
```