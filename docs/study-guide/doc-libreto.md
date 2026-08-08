✓ Libreto generado: 13 capítulos, 6174 palabras, 45855 chars
# La Tiendita — Arquitectura y Guía de Estudio — Libreto

Guía de estudio v2 de La Tiendita: e-commerce second-hand fullstack con backend hexagonal Litestar/Python, frontend Angular veintidos SPA, pagos multi-provider (Stripe + Swish), email transaccional Resend y OAuth2 con Google.

Plataforma e-commerce fullstack para ropa de segunda mano, dirigida al mercado sueco: backend async Python con arquitectura hexagonal (Litestar 2.x), frontend Angular veintidos SPA con PrimeNG y Tailwind, PostgreSQL 16, Redis siete (cache + cola ARQ), pagos multi-provider (Stripe card/Klarna + Swish), email transaccional con Resend, y login social con Google OAuth2. tres mil setecientos ochenta nodos en el grafo de código limpio, trescientos diecinueve tests backend, tres idiomas (es/en/sv).

## Capítulo 1: Contexto

La Tiendita nace como proyecto de portafolio profesional con ambición de producción. El objetivo: demostrar end-to-end ownership sobre un sistema completo — desde la arquitectura hexagonal en el backend hasta la UX multi-idioma en el frontend, pasando por decisiones de infraestructura, pagos, testing y compliance regulatorio (GDPR).

¿Por qué? Elegí construir esto como proyecto fullstack en vez de contribuir a open source. Un proyecto propio permite mostrar decisiones de arquitectura con fundamento real: por qué Litestar y no FastAPI, cómo el repository pattern encapsula SQLAlchemy, cómo un sistema de pagos multi-provider se abstrae tras una interfaz, o qué pasa cuando un carrito de invitado se mergea con uno de usuario autenticado.

Pasemos a métricas del sistema (grafo de código — graphify, ocho agosto dos mil veintiséis).

El grafo de código se genera con graphify usando un corpus whitelisted: solo backend/ + frontend/ (docs, screenshots, vendors minificados quedan fuera — ver sección Análisis del Grafo).

Nodos del grafo: valor: tres mil setecientos ochenta. Edges (relaciones): valor: ocho mil quinientos siete. Comunidades detectadas: valor: doscientos sesenta y cuatro. Archivos de código: valor: trescientos setenta y tres (ciento noventa y nueve Python, aproximadamente ciento treinta TypeScript, resto HTML/CSS/JSON). Tests backend: valor: trescientos diecinueve recolectados, más de doscientos sesenta y tres pasando (veintitres fallan por BD sin seed). Idiomas UI: valor: tres (es/en/sv). Migraciones Alembic: valor: diecinueve.

Ahora, inventario de capas (backend).

app/controllers/: archivos: quince; responsabilidad: HTTP, validación Pydantic, guards JWT/admin/rate-limit. app/services/: archivos: dieciocho; responsabilidad: Lógica de negocio — cero SQL crudo. app/repositories/: archivos: dieciséis; responsabilidad: Acceso a datos — patrón repositorio. app/models/: archivos: catorce; responsabilidad: ORM SQLAlchemy 2.x async. app/schemas/: archivos: —; responsabilidad: DTOs Pydantic v2. app/payments/: archivos: cuatro; responsabilidad: Multi-provider: interfaz + Stripe + Swish + registry. app/core/: archivos: —; responsabilidad: Config, cache, event bus, email, ARQ. app/queries/: archivos: —; responsabilidad: SQL crudo para lecturas complejas (CQRS). migrations/: archivos: diecinueve; responsabilidad: Alembic — se aplican automáticamente al iniciar.

---

## Capítulo 2: Arquitectura General

El diagrama de arquitectura muestra los siguientes componentes: Cliente. Nginx. Controllers. Services. Repositories. PostgreSQL dieciséis. Redis siete. ARQ Worker. Payments. Event Bus. Se muestran ocho conexiones entre estos componentes, representando el flujo de datos de la arquitectura.

Hablemos de cliente.

El frontend es una Angular veintidos SPA con standalone components, signals para estado reactivo, y RxJS para flujos asíncronos. Soporta tres idiomas (español, inglés, sueco) vía ngx-translate con cambio en caliente (sin recargar).

once módulos de features con lazy loading:

Home: ruta: la ruta raíz; descripción: Hero, categorías, nuevos arrivals, sale, newsletter. Auth: ruta: la ruta de login, la ruta de registro; descripción: JWT + 2FA TOTP, Google OAuth2, registro con consentimiento. Products: ruta: la ruta de productos; descripción: Catálogo con FTS + filtros multi-criterio. Product Detail: ruta: la ruta de detalle de producto; descripción: Galería, variantes, reviews, wishlist. Cart: ruta: la ruta del carrito; descripción: Guest merge, stock check, shipping. Checkout: ruta: la ruta de pago; descripción: Selector de tres métodos de pago, QR Swish, stock reservation. Profile: ruta: la ruta de perfil; descripción: Órdenes, wishlist, datos, 2FA, GDPR export. Admin: ruta: la ruta admin, con comodín; descripción: Dashboard, CRUD productos/usuarios/categorías/órdenes/promos. Legal: ruta: la ruta de privacidad, la ruta de términos; descripción: GDPR, cookies, términos. Sale: ruta: la ruta de ofertas; descripción: Productos en oferta. New Arrivals: ruta: la ruta de novedades; descripción: Últimos productos.

Veamos ahora nginx.

Reverse proxy en producción: sirve la SPA compilada desde la ruta raíz y redirige la api al backend Litestar. Puerto 80, sin exposición directa de servicios internos. Terminación TLS centralizada.

En cuanto a api gateway.

quince controllers Litestar mapean rutas REST a servicios. Cada controller:

 Recibe request con schemas Pydantic v2 validados automáticamente, Aplica guards (JWT, admin, optional auth, rate-limit) antes de entrar al handler, Delega lógica al service correspondiente y Retorna Response tipada con serialización automática.

Se ilustra la implementación con ProductController, list_products.

Consejo: Litestar resuelve automáticamente los parámetros de función como dependencias inyectadas. async def list_products(self, product_service: ProductService) — Litestar instancia o reusa ProductService según su scope configurado (singleton por defecto). Cero boilerplate de DI.

Pasemos a servicios.

dieciocho servicios de negocio — cada uno con una responsabilidad única. Regla de oro del proyecto: los services NO contienen SQL crudo (verificado con grep en el repo: cero select()/update() de SQLAlchemy en app/services/). Toda la data access vive en repositorios.

Servicios clave (grado real del grafo, agosto dos mil veintiséis):

product_service.py: responsabilidad: Catálogo, CRUD, filtros, caché; conexiones en grafo: setenta y siete. promotion_service.py: responsabilidad: Promociones con cap de uso; conexiones en grafo: setenta y nueve. order_service.py: responsabilidad: Checkout, stock, estados; conexiones en grafo: sesenta y seis. auth_service.py: responsabilidad: Registro, login, refresh, 2FA, OAuth2; conexiones en grafo: cincuenta y dos. admin_user_service.py: responsabilidad: Gestión de usuarios admin; conexiones en grafo: cuarenta. variant_service.py: responsabilidad: Variantes y stock; conexiones en grafo: cincuenta y uno. email_service.py: responsabilidad: Transaccionales (Resend/SMTP/log); conexiones en grafo: —. newsletter_service.py: responsabilidad: Suscripción/desuscripción; conexiones en grafo: —.

¿Por qué? La separación service→repository→model no es decorativa: permite testear los services con mocks de repos (sin BD), centraliza queries complejas, y si mañana migro de PostgreSQL a otra cosa, solo cambian los repositorios. El refactor de agosto dos mil veintiséis llevó esto al límite: se migraron los últimos diez queries SQL crudos (seis selects + cuatro updates) de los services a métodos de repositorio con semántica atómica-condicional (ver sección Refactor).

Ahora, repositorios.

dieciséis repositorios heredando de BaseRepository (CRUD genérico: get_by_id, find_one, find_all, get_paginated, add, delete, count, exists). Cada dominio tiene el suyo:

UserRepository: métodos de dominio destacados: get_by_email, get_with_role, get_role, update_role, get_all_with_order_counts. ProductRepository: métodos de dominio destacados: Filtros complejos, búsqueda FTS. OrderRepository: métodos de dominio destacados: get_with_items, count_by_user, transition_status, unassign_user. CartRepository: métodos de dominio destacados: get_items, upsert_item, clear_scope, merge_guest_cart. VariantRepository: métodos de dominio destacados: get_by_sku, deduct_stock (atómico-condicional). PromotionRepository: métodos de dominio destacados: get_active, increment_usage (cap-safe), update_fields. ReviewRepository: métodos de dominio destacados: get_by_product, get_aggregate, user_has_purchased, delete_by_user. NewsletterSubscriberRepository: métodos de dominio destacados: get_unsubscribed_by_email, get_active_by_email. AuditRepository: métodos de dominio destacados: add, delete_by_actor. RefreshTokenRepository: métodos de dominio destacados: find_by_user, delete_user_tokens, delete_expired.

Se ilustra la implementación con BaseRepository, __init__, find_one, add, None.

Hablemos de persistencia.

 PostgreSQL dieciséis: datos relacionales + full-text search (tsvector con triggers automáticos). Alembic maneja diecinueve migraciones que se aplican al iniciar la app (nunca manualmente en deploy). y Redis siete: cache-aside con TTL configurable por recurso (productos: cinco min, categorías: treinta min) + LRU eviction. También es broker de ARQ para background jobs..

Información: La invalidación de caché se dispara por event bus: cuando un producto se actualiza, product_service emite ProductUpdated, el handler de caché escucha e invalida las keys relevantes. Sin dependencias circulares.

Veamos ahora event bus.

Infraestructura de publicador/suscriptor en memoria para cross-cutting concerns:

El diagrama de flujo muestra cómo se conectan los componentes: EventBus notifica hacia CacheInvalidationHandler. EventBus notifica hacia AuditLogHandler. EventBus notifica hacia EmailHandler.

El bus es síncrono y en memoria (no Redis pub/sub). Decisión deliberada: para el volumen actual, añadir un message broker introduce complejidad sin beneficio. Si escala, migrar a Redis Streams o NATS es trivial porque los handlers ya están desacoplados.

El EmailHandler abre su propia sesión de BD (vía session factory global) para que el envío de emails esté desacoplado del request que lo disparó — los fallos de email se loguean pero nunca bloquean la transacción principal.

En cuanto a background jobs.

ARQ (Async Redis Queue) ejecuta tareas asíncronas fuera del ciclo request-response:

 Procesamiento de imágenes (redimensionar, convertir a WebP), Envío de emails transaccionales (reset password, confirmación orden, welcome) y Cleanup de tokens expirados.

¿Por qué? ARQ sobre Celery: este proyecto es async-first (Litestar + SQLAlchemy async). Celery requiere un thread pool separado para bridge sync/async. ARQ corre nativamente en el event loop de asyncio, solo necesita Redis (sin RabbitMQ), y el código de worker usa los mismos patrones async que la API. Para este tamaño de deploy, simplicidad gana.

Pasemos a event bus y cache (detalle).

El patrón cache-aside con invalidación por eventos:

TTLs actuales: productos list 60s, producto detail 300s, categorías 600s, promociones activas 120s.

---

## Capítulo 3: Sistema de Pagos Multi-Provider

La joya de la v2. En vez de acoplar el checkout a un solo proveedor, app/payments/ define una interfaz PaymentProvider y dos implementaciones intercambiables vía registry.

Ahora, arquitectura.

Se ilustra la implementación con PaymentProvider, create_payment, get_status, handle_callback, refund.

Se ilustra la implementación con get_provider, PaymentProvider.

El grafo de código confirma el polimorfismo correcto:

Hablemos de stripe (card + klarna).

 Card: Stripe hosted Checkout (PaymentIntent gestionado por Stripe, formulario PCI-compliant). y Klarna: NO requiere provider separado — es payment_method_types=["card", "klarna"] en la misma Checkout Session de Stripe. Una línea de configuración..

Webhook en la ruta payments, stripe, webhook — JWT-exempt (Stripe firma los payloads, no necesita JWT). Verifica firma con stripe.Webhook.construct_event().

Veamos ahora swish (mock).

 Swish es una API sueca propia (developer.swish.nu) — Stripe NO la soporta. Por eso es un provider aparte., Por defecto corre en SWISH_MODE=mock: el checkout devuelve un QR fake y POST la ruta payments, swish, mock-confirm confirma la orden localmente. Sin cuenta de comerciante ni certificados mTLS. y Para live: SWISH_MODE=live + certificados mTLS + registro de comerciante. La interfaz no cambia — solo cambia la implementación interna..

Se ilustra la implementación con create_payment, dict.

En cuanto a modelo de datos de pagos.

Migración diecisiete: el modelo Order pasó de stripe_session_id (monolítico) a:

payment_provider: tipo: str; descripción: stripe \. payment_reference: tipo: str; descripción: ID del proveedor (session_id, payment_request). payment_details: tipo: JSONB; descripción: Payload flexible del proveedor.

Esto permite que OrderService.checkout() llame a get_provider(payment_method) y no sepa NADA de Stripe ni Swish:

Pasemos a flujo de pago end-to-end (swish mock).

El siguiente diagrama de secuencia describe el flujo entre: Usuario, Angular, PaymentsController, OrderService, SwishProvider, PostgreSQL. Usuario Selecciona "Swish" en checkout hacia Angular Angular POST la ruta checkout {payment_method: "swish"} hacia PaymentsController PaymentsController checkout() hacia OrderService OrderService crear Order (PENDING) hacia OrderService OrderService create_payment() hacia SwishProvider SwishProvider {qr_code, payment_reference} hacia OrderService OrderService {qr_code, order_id} hacia Angular Angular Muestra QR + instrucciones hacia Usuario Usuario POST la ruta payments, swish, mock-confirm hacia PaymentsController PaymentsController handle_callback() hacia SwishProvider SwishProvider order.status → PAID/CONFIRMED hacia PostgreSQL SwishProvider doscientos OK hacia Angular Angular carrito vaciado + redirección a éxito hacia Angular

Verificado E2E en navegador (Playwright): producto → carrito → checkout → Swish QR → mock-confirm → orden PAID/CONFIRMED, stock decrementado, carrito vaciado.

Advertencia: Card/Klarna requieren STRIPE_SECRET_KEY + STRIPE_WEBHOOK_SECRET reales (test mode). Sin keys, el checkout llega al StripeProvider y falla con error claro (quinientos dos). Para desarrollo local sin cuenta Stripe, usa Swish mock — el flujo completo funciona end-to-end sin registrarse en ningún lado.

---

## Capítulo 4: Email Transaccional (Resend)

Todos los emails salen por un único punto de despacho: send_email() en app/utils/email.py. El modo se configura con EMAIL_MODE:

log: comportamiento: Imprime el email en consola; uso: Desarrollo. smtp: comportamiento: Relay SMTP clásico; uso: Alternativa. resend: comportamiento: Resend API (api.resend.com/emails); uso: Producción.

Se ilustra la implementación con _send_resend, None.

Emails transaccionales (todos con templates Jinja2 + i18n es/en/sv):

Welcome: evento disparador: WelcomeEmailEvent (registro); template: emails/welcome.html. Confirmación de orden: evento disparador: OrderConfirmationEvent (pago finalizado); template: emails/order_confirmation.html. Envío de orden: evento disparador: OrderShippedEvent (admin marca shipped); template: emails/order_shipped.html. Reset de password: evento disparador: PasswordResetEvent; template: emails/password_reset.html.

Consejo: El EmailHandler escucha los eventos con su propia sesión de BD — los fallos de email se loguean pero NUNCA rompen el checkout ni la transacción principal. Los templates se renderizan con Jinja2 desde app/templates/ y los mensajes i18n se cargan de app/i18n/{lang}.json según el idioma preferido del usuario.

---

## Capítulo 5: Autenticación y OAuth2

Ahora, flujo estándar: jwt + 2fa.

El siguiente diagrama de secuencia describe el flujo entre: Usuario, Angular SPA, AuthController, AuthService, PostgreSQL. Usuario POST la ruta de login {email, password} hacia Angular SPA Angular SPA Request hacia AuthController AuthController authenticate(email, password) hacia AuthService AuthService SELECT user + bcrypt verify hacia PostgreSQL Si se cumple la condición de que totp enabled (solo admin), AuthService requires_2fa: true hacia AuthController AuthController cuatrocientos uno + 2FA required hacia Angular SPA Angular SPA Mostrar input TOTP hacia Usuario Usuario Ingresar código seis dígitos hacia Angular SPA Angular SPA POST la ruta login, 2fa {code} hacia AuthController AuthController verify_totp(code) hacia AuthService y aquí termina esta parte del flujo. AuthService generate access_token + refresh_token hacia AuthService AuthService tokens hacia AuthController AuthController doscientos {access_token, refresh_token} hacia Angular SPA Angular SPA localStorage.setItem + currentUser signal hacia Angular SPA

 Rotación de tokens: access quince min, refresh siete días. El interceptor HTTP renueva automáticamente ante cuatrocientos uno (con coalescing: una sola petición de refresh en vuelo)., 2FA TOTP solo admin (PyOTP, RFC seis mil doscientos treinta y ocho — compatible Google Authenticator). y Rate limiting por endpoint (veinte req/60s por defecto)..

Hablemos de google oauth2 (login social) — nuevo en v2.

Implementación completa con httpx-oauth (dependencia httpx-oauth>=0.16). El modelo User ya tenía los campos desde el diseño inicial; ahora se usan de verdad:

Flujo completo:

El siguiente diagrama de secuencia describe el flujo entre: Usuario, Angular, AuthController, AuthService, Google. Usuario Click "Iniciar sesión con Google" hacia Angular Angular GET la ruta auth, oauth, google hacia AuthController AuthController trescientos dos redirect → consent screen de Google hacia Angular Angular consentimiento hacia Google Google redirect a la ruta auth, google, callback?code=... hacia Angular Angular GET la ruta auth, oauth, google, callback?code=... hacia AuthController AuthController oauth_callback(code) hacia AuthService AuthService exchange code → access_token (httpx-oauth) hacia Google AuthService userinfo (id, email, name, picture) hacia Google Si se cumple la condición de que usuario con oauth_id existe, AuthService login directo hacia D AuthService VINCULA: oauth_provider/oauth_id en la cuenta existente hacia D AuthService Crea usuario (is_verified=True, oauth fields, avatar) hacia D y aquí termina esta parte del flujo. AuthService {access_token, refresh_token, user} hacia Angular Angular guarda tokens + redirige por rol hacia Angular

Puntos clave:

 GET la ruta oauth, google redirige a Google (con state random para CSRF). Sin GOOGLE_CLIENT_ID → 501., GET la ruta oauth, google, callback intercambia el code — find-or-create con tres ramas: oauth_id match → login; email match → vincular cuenta password existente; ninguno → crear usuario nuevo., Usuarios OAuth nacen con is_verified=True (Google verifica el email)., Redirect URI: GOOGLE_OAUTH_REDIRECT_URI (default el enlace mencionado). y Frontend: AuthService.initiateGoogleLogin() (window.location) + exchangeGoogleCode(code) + componente GoogleCallback que captura el ?code=. Botón de Google activado en el login con i18n en tres idiomas..

Advertencia: La vinculación por email es un vector de account-takeover si se hace mal: si un atacante registra una cuenta con tu email ANTES de que hagas OAuth, la vincularía. Mitigación parcial: solo vincula si la cuenta NO tiene password_hash propio O si el email está verificado. Evaluar flujo de "confirmar propiedad del email" antes de habilitar en producción real.

Veamos ahora decisiones de seguridad.

 bcrypt para passwords (veinticinco años probado; argon2 es teóricamente superior pero requiere libs nativas que complican el deploy)., python-jose para JWT (forward-compatible con OIDC — elegido ANTES del OAuth justamente por eso)., Webhooks de Stripe con verificación de firma obligatoria., JWT-exempt solo en rutas que lo justifican: la ruta payments, * (firma del proveedor) y la ruta stripe, webhook. y Audit log con actor/acción/entidad para cada mutación administrativa..

---

## Capítulo 6: Flujos Clave End-to-End

En cuanto a checkout con stock reservation (multi-provider).

El siguiente diagrama de secuencia describe el flujo entre: Usuario, Angular, CheckoutController, OrderService, VariantRepository, PaymentProvider, Redis. Usuario Click "Pagar" + método (card/klarna/swish) hacia Angular Angular POST la ruta checkout {cart_id, payment_method, shipping} hacia CheckoutController CheckoutController checkout() hacia OrderService OrderService pre-validar stock (todos los items ANTES de mutar) hacia VariantRepository OrderService begin_nested() (savepoint) hacia OrderService OrderService deduct_stock() atómico-condicional por item hacia VariantRepository OrderService get_provider(method) → create_payment() hacia PaymentProvider OrderService {order_id, qr_code | redirect_url} hacia Angular Nota del diagrama: over O: si algo falla → rollback del savepoint. Angular pago en proveedor (Stripe Checkout | Swish app) hacia PaymentProvider PaymentProvider callback/webhook hacia CheckoutController CheckoutController confirm_order() hacia OrderService OrderService status → PAID/CONFIRMED, carrito vaciado hacia OrderService

Dos detalles de corrección críticos:

 primero, Pre-validación + savepoint: primero se valida TODO el stock (sin mutar), luego se envuelven TODAS las mutaciones en begin_nested() — si cualquier deducción falla, todo el savepoint se revierte atómicamente. No hay estado intermedio.. segundo, Updates atómicos-condicionales (TOCTOU-safe): la deducción de stock NO es "leer, restar, escribir" (race condition). Es un solo UPDATE con condición:.

Se ilustra la implementación con deduct_stock, bool.

Si dos checkouts concurrentes piden el mismo variant, solo uno gana — el otro recibe False y revierte. Sin locks manuales, sin sobreventa.

Pasemos a promotions con cap de uso (toctou-safe).

El incremento de current_uses de una promoción usa el MISMO patrón:

Se ilustra la implementación con increment_usage, bool.

Concurrent checkouts no pueden sobrepasar el cap de usos de una promo — el UPDATE falla (cero rows) cuando el cap se agota.

Ahora, admin: transición de estados de orden (anti-toctou).

Se ilustra la implementación con transition_status, bool.

El WHERE status = current evita que dos admins transicionen la misma orden sobre estado stale. Si el rowcount es cero → InvalidTransitionError.

Hablemos de guest cart merge.

El siguiente diagrama de secuencia describe el flujo entre: Guest (localStorage), Angular, AuthService, CartService, PostgreSQL. Guest (localStorage) localStorage cart_id = "abc-ciento veintitres" hacia Guest (localStorage) Guest (localStorage) Iniciar sesión hacia Angular Angular POST la ruta de login (o OAuth) hacia AuthService AuthService JWT + user_id hacia Angular Angular POST la ruta cart, merge {guest_cart_id: "abc-ciento veintitres"} hacia CartService CartService Buscar guest cart hacia PostgreSQL CartService Buscar user cart (o crear) hacia PostgreSQL Repitiendo el siguiente paso mientras cada item del guest cart, CartService Si mismo variant_id → sumar cantidades hacia CartService CartService Si no existe → mover al user cart hacia CartService y aquí termina esta parte del flujo. CartService Eliminar guest cart hacia PostgreSQL CartService user_cart actualizado hacia Angular Angular actualizar cart signal hacia Angular

---

## Capítulo 7: Arquitectura del Frontend

Veamos ahora estructura de features.

En cuanto a state management.

La app usa dos estrategias según el caso:

Angular Signals: uso: Estado local + compartido simple; ejemplo: currentUser(), cartCount(), theme(). RxJS BehaviorSubject: uso: Flujos asíncronos multi-consumidor; ejemplo: CategoryService.categories$, CartService.cart$.

Pasemos a authservice del frontend (login + oauth).

El componente GoogleCallback (ruta auth/google/callback) lee el ?code= del query param, llama a exchangeGoogleCode, inicia SessionExpirationService y redirige por rol (admin → la ruta de administración, customer → la ruta raíz). Maneja errores con mensajes i18n.

Ahora, guards e interceptors.

El refresh tiene coalescing: si ya hay un refresh en vuelo, los nuevos cuatrocientos uno esperan el MISMO observable compartido — una sola llamada HTTP, todos los subscribers reciben el mismo token nuevo.

Hablemos de multi-idioma (i18n).

Tres archivos JSON con claves estructuradas (es/en/sv). ngx-translate carga el archivo correspondiente según navigator.language o preferencia guardada. El language switcher en el header persiste en localStorage. Regla: todo string visible al usuario debe venir de traducciones.

---

## Capítulo 8: Refactor Repository Pattern (agosto dos mil veintiséis)

Veamos ahora el problema detectado.

El análisis del grafo (graphify + LLM) detectó queries SQL crudas en la capa de servicios — deuda residual del refactor anterior:

En cuanto a la solución.

Se migraron TODOS a métodos de repositorio con semántica de dominio (no execute(select(...)) genérico):

select(NewsletterSubscriber).where(unsubscribed_at): → método de repositorio: NewsletterSubscriberRepository.get_unsubscribed_by_email; semántica: Re-activación. select(NewsletterSubscriber).where(unsubscribed_at IS NULL): → método de repositorio: NewsletterSubscriberRepository.get_active_by_email; semántica: Unsubscribe/check. select(User.role): → método de repositorio: UserRepository.get_role; semántica: Audit trail. update(User)...returning: → método de repositorio: UserRepository.update_role; semántica: UPDATE…RETURNING. select(AuditLog): → método de repositorio: AuditRepository.delete_by_actor; semántica: Teardown. select(CartItem/Review/Wishlist/RefreshToken/PasswordReset): → método de repositorio: clear_scope + delete_by_user + delete_user_tokens; semántica: Teardown cascade. update(Order).values(user_id=None): → método de repositorio: OrderRepository.unassign_user; semántica: Preserva historial. update(Promotion) parcial: → método de repositorio: PromotionRepository.update_fields; semántica: Update de campos. update(Promotion).current_uses+uno: → método de repositorio: PromotionRepository.increment_usage; semántica: Cap-safe. update(ProductVariant).stock-qty: → método de repositorio: VariantRepository.deduct_stock; semántica: Atómico-condicional. update(Order).where(status=current): → método de repositorio: OrderRepository.transition_status; semántica: Anti-TOCTOU.

Pasemos a el resultado medido.

El grafo lo confirma cuantitativamente (antes → después):

Edges service→repository: antes: doscientos seis; después: trescientos dieciséis; delta: +ciento diez (+cincuenta y tres%). Edges service→model: antes: trescientos ochenta y tres; después: trescientos noventa y ocho; delta: +quince (estable). Ratio repo:model del acoplamiento: antes: 0.54; después: 0.79; delta: +cuarenta y seis%. OrderRepository degree: antes: setenta y dos; después: ochenta y uno; delta: +nueve. CartRepository degree: antes: setenta y uno; después: ochenta y cinco; delta: +catorce. SQL crudo en services: antes: diez; después: cero; delta: ✅.

El acoplamiento de los servicios se MOVIÓ hacia los repositorios — exactamente lo que la arquitectura hexagonal prescribe.

Error común: GOTCHA del refactor: transition_status NO debe hacer flush() internamente. El patrón correcto es repo → bool, service → raise si False → flush después. Si el repo flushea antes del raise, un test que verifica "no flush tras rowcount=cero" falla y, peor, semánticamente el flush con estado inválido puede ocultar errores.

---

## Capítulo 9: Análisis del Grafo de Código

Ahora, corpus limpio (lección aprendida).

El grafo se regenera con whitelist estricta en .graphifyignore: solo backend/ + frontend/. La primera versión contaminada incluía docs/ (study-guide con vendors .min.js de mermaid/gsap/katex) y ciento seis screenshots PNG — resultó en doce mil cuatrocientos ochenta y tres nodos falsos dominados por símbolos minificados (_(), push(), a5e()). El corpus limpio tiene tres mil setecientos ochenta nodos reales.

Error común: GOTCHA de graphify: las negaciones del .graphifyignore deben ser unanchored (!backend, NO !la ruta backend). El parser hace pattern[uno:] y un la ruta raíz posterior re-ancla el patrón, que solo matchea el dir exacto y nunca su contenido. Con fnmatch cruzando la ruta raíz, la ruta raíz* se traga todo a cualquier profundidad.

Hablemos de god nodes (los pesos pesados reales).

Product: degree: ciento cincuenta y uno; rol: Modelo central del catálogo. Order: degree: ciento veinticuatro; rol: Núcleo de ventas. User: degree: ciento diez; rol: Identidad. ProductTranslation: degree: ochenta y ocho; rol: i18n del catálogo. CartRepository: degree: ochenta y seis; rol: Acceso a datos del carrito. OrderRepository: degree: ochenta y uno; rol: Datos de pedidos. PromotionService: degree: setenta y nueve; rol: Lógica de negocio. ProductService: degree: setenta y siete; rol: Catálogo.

Veamos ahora comunidades más grandes.

Category and Product Controllers: nodos: ciento tres. Product Service: nodos: noventa y dos. Cart Repository: nodos: ochenta y ocho. Email Event Handler: nodos: setenta y siete. Product Variant Repositories: nodos: sesenta y uno. Order Payment Models: nodos: cincuenta y nueve. Stripe/Swish Payment Provider: nodos: veintiocho/doce.

En cuanto a lectura arquitectónica del grafo.

 cero dependencias cross-layer frontend↔backend — comunican solo por HTTP. Desacople perfecto., La capa de pagos está aislada: cuatro comunidades dedicadas (Stripe Provider, Swish Provider, Payment Webhooks, Order Payment Models)., Los "import cycles" reportados son todos 1-file (falsos positivos del AST por imports tardíos dentro de funciones — patrón conocido, no deuda real). y order_service.py toca trece comunidades distintas — es el hub de integración del checkout. Vigilar si crece más..

---

## Capítulo 10: Decisiones Técnicas y Tradeoffs

Cada decisión de arquitectura, framework y librería tiene una razón concreta. Ordenadas por categoría, con el qué, el por qué, y qué se rechazó.

Pasemos a arquitectura.

¿Por qué arquitectura hexagonal (ports & adapters)?

¿Por qué? Separar el dominio (services) de la infraestructura (controllers, repositories, BD) permite tres cosas críticas: (uno) los services se testean sin BD ni HTTP — solo mocks de repositorios, (dos) cambiar PostgreSQL por otra cosa toca solo repositories y models, y (tres) las reglas de negocio viven en UN lugar. El refactor de agosto dos mil veintiséis llevó el patrón al límite: cero SQL en services, updates atómicos-condicionales en repos.

¿Por qué repository pattern y no ORM directo en services?

Se ilustra la implementación con ProductService, get_products.

Se ilustra la implementación con ProductService, get_products.

¿Por qué? El repository pattern crea una frontera clara: los services no saben SQL ni SQLAlchemy — solo hablan con interfaces de repositorio. Permite mockear repos en tests unitarios sin BD, centralizar queries complejas (CQRS), y migrar de BD sin tocar servicios. La versión moderna incluye métodos con semántica atómica-condicional (deduct_stock, increment_usage, transition_status) que hacen imposible la sobreventa o el doble-uso de promos por race conditions.

¿Por qué event bus en memoria y no message broker?

¿Por qué? El event bus resuelve cross-cutting concerns (audit log, cache invalidation, emails) sin acoplar servicios. Un broker añadiría latencia de red, reconexión, ordering guarantees — complejidad sin beneficio a este volumen. El bus síncrono ejecuta handlers en el mismo request (correcto para audit que DEBE pasar antes del commit). Si escala, migrar a Redis Streams es trivial.

¿Por qué cache-aside y no write-through o write-back?

¿Por qué? Cache-aside es el más simple y resiliente: si Redis cae, la app sigue funcionando (lee de BD, solo más lento). Write-through acopla escrituras a la disponibilidad de Redis; write-back puede perder datos si Redis muere antes del flush. Para un e-commerce donde la consistencia de inventario es crítica, cache-aside + invalidación por event bus da el balance correcto.

¿Por qué JWT y no server sessions?

Escalado horizontal: jwt: Stateless — cualquier instancia valida; server sessions: Requiere sesión compartida (Redis/DB). Mobile/OAuth: jwt: Nativo — token en header; server sessions: Cookies con CORS complejas en mobile. Invalidación: jwt: Refresh rotation + blacklist; server sessions: Borrar sesión en store. Tamaño: jwt: aproximadamente quinientos bytes self-contained; server sessions: Session ID + lookup en cada request.

¿Por qué? JWT permite escalar horizontalmente sin estado compartido. Las sessions requieren un store compartido consultado en CADA request. Para un deploy que puede crecer a múltiples instancias, JWT elimina un punto de falla. El tradeoff (invalidación) se maneja con refresh rotation de siete días.

Ahora, stack de backend.

¿Por qué Litestar y no FastAPI?

Dependency Injection: litestar: Nativo con scopes (singleton, request, connection); fastapi (rechazado): Requiere python-dependency-injector externo. Guards de auth: litestar: Declarativos tipados como decoradores; fastapi (rechazado): Dependencias como callables manuales. Event system: litestar: Señales incorporadas; fastapi (rechazado): No nativo. OpenAPI: litestar: Generación desde tipos Python; fastapi (rechazado): Automática pero menos flexible. Maturidad: litestar: Más nuevo, menos comunidad; fastapi (rechazado): Estándar de facto.

Consejo: La pregunta real en entrevista es "¿por qué elegiste una alternativa menos popular?". Respuesta: Litestar resuelve los problemas CONCRETOS — DI scoped, guards declarativos, señales para el event bus. FastAPI es excelente, pero Litestar eliminó tres dependencias externas y aproximadamente doscientas líneas de boilerplate. Tradeoff aceptado: menos talent pool.

¿Por qué SQLAlchemy 2.x async y no SQLModel o Tortoise?

¿Por qué? SQLAlchemy 2.x es el ORM más maduro (más de quince años), async nativo desde 2.0, ecosistema enorme (Alembic, FTS), y permite mezclar ORM y SQL crudo según convenga (esencial para CQRS — ver app/queries/). SQLModel acopla modelo de BD a schema de API — viola la separación de capas. Tortoise tiene ecosistema más pequeño. SQLAlchemy gana por madurez, flexibilidad y ecosystem.

¿Por qué Pydantic v2 para DTOs?

¿Por qué? Pydantic v2 (Rust) valida y serializa de cinco a diez veces más rápido que v1. Litestar lo usa para validación automática de requests y generación de OpenAPI. Alternativas: dataclasses no validan en runtime, marshmallow es más lento y menos integrado con type checkers. Pydantic v2 es el estándar de facto.

¿Por qué PostgreSQL dieciséis y no MySQL o SQLite?

Full-Text Search: postgresql dieciséis: tsvector nativo con ranking; mysql ocho: Limitado; sqlite: FTS5 básico. JSON columns: postgresql dieciséis: JSONB indexable; mysql ocho: JSON sin indexación eficiente; sqlite: JSON1 extensión. Tipos avanzados: postgresql dieciséis: UUID, ARRAY, Range; mysql ocho: Limitado; sqlite: Limitado. Concurrency: postgresql dieciséis: MVCC; mysql ocho: MVCC con gotchas; sqlite: Single-writer lock.

¿Por qué Redis siete (cache + queue) y no Memcached + RabbitMQ?

¿Por qué? Redis hace dos trabajos: cache-aside con TTL y broker de ARQ. Memcached + RabbitMQ = un servicio más que operar. Redis siete tiene data structures ricas, persistencia opcional, LRU eviction nativo. Un servicio que hace dos cosas > dos servicios especializados a este tamaño.

¿Por qué el sistema de pagos es multi-provider y no Stripe-only?

¿Por qué? El mercado sueco paga con Swish (el setenta%+ de pagos P2P en Suecia es Swish). Stripe NO soporta Swish — es una API sueca propia con certificados mTLS. En vez de hardcodear dos integraciones en el checkout, se abstrajo detrás de PaymentProvider: el checkout llama get_provider(method) y no sabe nada de Stripe ni Swish. Klarna entra gratis (es un flag en Stripe Checkout). Cuando el usuario tenga cuenta Swish real, solo se cambia SWISH_MODE=live — la interfaz no cambia. Esto es el Open/Closed Principle aplicado: abierto a extensión, cerrado a modificación.

¿Por qué Resend para email transaccional y no SMTP directo o SendGrid?

Setup: resend: API key + uno endpoint; smtp propio: Configurar relay, SPF/DKIM; sendgrid: API key. Deliverability: resend: Alta (infra moderna); smtp propio: Depende de tu IP/reputación; sendgrid: Alta. Free tier: resend: cien emails/día; smtp propio: —; sendgrid: cien/día. Modernidad: resend: API JSON + webhooks; smtp propio: Protocolo mil novecientos ochenta y dos; sendgrid: Legacy-first.

¿Por qué? Resend es la opción moderna de la industria: API REST JSON, SDKs, free tier generoso, deliverability gestionada (no pelear con reputación de IP). El código quedó aislado detrás de send_email() con EMAIL_MODE — probar en dev con log, producción con resend, sin tocar los services. Se rechazó SMTP directo porque la deliverability de Gmail/Hotmail depende de reputación de IP que no controlas en un VPS barato.

¿Por qué httpx-oauth para Google OAuth y no authlib?

¿Por qué? httpx-oauth ya estaba en las dependencias (es async-native como todo el stack: httpx, no requests), cubre el flujo get_authorization_url + get_access_token + get_id_email en tres llamadas, y pesa menos que authlib (que trae clientes para más de veinte proveedores que no usamos). YAGNI: si mañana se agrega GitHub o Facebook, httpx-oauth tiene clientes listos con la MISMA interfaz.

Hablemos de stack de frontend.

¿Por qué Angular veintidos y no React o Vue?

Opinión de estructura: angular veintidos: Opinable — modular por diseño; react diecinueve: Libre — requiere decisiones; vue tres: Semi-opinable. TypeScript: angular veintidos: Nativo, first-class; react diecinueve: Opcional (JSX mezcla); vue tres: Soporte pero opcional. Forms complejos: angular veintidos: Reactive Forms + validación; react diecinueve: Librerías externas; vue tres: VueUse menos maduro. Enterprise-scale: angular veintidos: DI, módulos lazy, guards nativos; react diecinueve: Arquitectura manual; vue tres: Similar a React. Signals: angular veintidos: Nativas desde v17; react diecinueve: useEffect/useMemo; vue tres: ref/reactive.

¿Por qué PrimeNG y no Angular Material?

Tablas con sort/filter/pagination: primeng: p-table nativo; angular material: MatTableDataSource + config manual. Multi-select con chips: primeng: p-multiSelect listo; angular material: No existe. File upload con preview: primeng: p-fileUpload; angular material: No existe. Iconos (más de dos mil quinientos): primeng: PrimeIcons; angular material: Material Icons limitado. Dark mode: primeng: Toggle nativo; angular material: Tema custom.

Error común: No confundir "más popular" con "mejor para tu caso". Material es sobresaliente para dashboards; una tienda necesita multi-select para filtros, file upload y dos mil quinientos iconos de moda/pagos. Decisión técnica, no estética.

¿Por qué Signals + RxJS y no NgRx?

¿Por qué? NgRx añade cuatro conceptos (actions, reducers, selectors, effects) y boilerplate. El estado de La Tiendita es mayoritariamente local por feature: carrito en CartService, auth en AuthService. Signals + BehaviorSubject cubren el cien% sin overhead. YAGNI — migrar a NgRx es incremental si el estado se complica.

¿Por qué ngx-translate y no i18n nativo?

¿Por qué? El i18n nativo de Angular compila UN build POR idioma — tres builds para es/en/sv. ngx-translate carga JSON en runtime, permitiendo cambiar idioma sin recargar. Para un e-commerce con language switcher (crítico en mercado sueco), el cambio en caliente es no-negociable.

¿Por qué Tailwind v3 + PrimeUI y no SCSS puro?

¿Por qué? Tailwind da utility classes sin escribir CSS custom; PrimeUI tematiza PrimeNG. Juntos: Tailwind estructura, PrimeUI da el design system. SCSS custom = semanas de trabajo. Para un portfolio donde el foco es arquitectura y UX, esta combinación es la más productiva.

Veamos ahora infraestructura.

¿Por qué Docker multi-stage?

¿Por qué? Multi-stage separa el contexto de build del runtime. Imagen de producción aproximadamente ciento cincuenta MB vs aproximadamente ochocientos MB. Menos superficie de ataque, deploys más rápidos. Python: python:3.14-slim runtime; Angular: build con node, sirve con nginx:alpine (aproximadamente treinta MB).

¿Por qué Nginx como reverse proxy?

¿Por qué? Nginx da: (uno) TLS centralizado, (dos) estáticos de la SPA sin pasar por Python, (tres) rate limiting a nivel edge, (cuatro) rotar instancias sin que el cliente note. Exponer uvicorn directo es anti-patrón.

¿Por qué GitHub Actions?

¿Por qué? Nativo del repo (cero infra), marketplace de actions, minutos gratis para open source. Jenkins = mantener servidor. GitLab CI = migrar de GitHub. Menor fricción.

En cuanto a anti-patrones evitados.

¿Por qué NO microservicios?

Cuidado: Para un proyecto de un desarrollador, microservicios serían over-engineering: más de ocho servicios que desplegar, latencia de red, consistencia distribuida (sagas, outbox), observabilidad compleja. La arquitectura hexagonal modular permite extraer un microservicio cuando un módulo lo justifique por carga. Monolith first, extraer después.

¿Por qué NO GraphQL?

¿Por qué? GraphQL brilla con múltiples clientes con necesidades distintas. Con un solo cliente (Angular SPA) y endpoints bien definidos, REST es más simple: caché HTTP nativo, status codes, tooling maduro. Si mañana hay mobile nativo, GraphQL sería el camino.

¿Por qué NO event sourcing?

¿Por qué? Event sourcing da auditoría perfecta pero añade event store, proyecciones, snapshots, eventual consistency. El audit log tradicional (tabla actor/acción/entidad) cubre compliance a fracción del costo. Event sourcing se justifica en sistemas financieros hiper-regulados, no en un e-commerce de portfolio.

---

## Capítulo 11: Infraestructura

Pasemos a docker compose (dev).

Se ilustra la implementación con services, postgres, redis, api, frontend.

Ahora, producción.

docker-compose.prod.yml agrega nginx sirviendo la SPA compilada, uvicorn sin --reload, worker ARQ separado, volúmenes persistentes.

Se ilustra la implementación con services, nginx, volumes.

Hablemos de variables de entorno clave (.env).

DATABASE_URL: rol: Conexión PostgreSQL async; estado default: requerida. REDIS_URL: rol: Cache + cola ARQ; estado default: redis:la ruta localhost:seis mil trescientos setenta y nueve/cero. SECRET_KEY: rol: Firma JWT; estado default: requerida. EMAIL_MODE: rol: log \; estado default: smtp \. RESEND_API_KEY: rol: Email Resend; estado default: vacía (dev = log). GOOGLE_CLIENT_ID/SECRET: rol: OAuth2; estado default: vacías (dev = quinientos uno). GOOGLE_OAUTH_REDIRECT_URI: rol: Callback OAuth; estado default: el enlace mencionado. STRIPE_SECRET_KEY/WEBHOOK_SECRET: rol: Stripe; estado default: vacías (usa Swish mock). SWISH_MODE: rol: mock \; estado default: live. FRONTEND_URL: rol: URL del frontend; estado default: el enlace mencionado.

---

## Capítulo 12: Testing

Veamos ahora estrategia por capa.

Backend unit: framework: pytest + pytest-asyncio (modo STRICT); estado: trescientos diecinueve recolectados, más de doscientos sesenta y tres pass. Backend integration: framework: pytest contra PostgreSQL real; estado: test_*_integration.py — más de ocho pass con BD. Frontend unit: framework: vitest (@angular/build:unit-test); estado: veintinueve specs. E2E: framework: Playwright (desktop/tablet/mobile); estado: flujo completo verificado.

Advertencia: veintitres tests fallan cuando la BD no tiene seed (catalog/FTS/seed/promotions). No es deuda de código — es infraestructura: python scripts/seed_real.py (trescientos productos reales con traducciones) arregla el entorno.

En cuanto a patrones de testing usados.

Se ilustra la implementación con test_oauth_callback_creates_user, fake_get_access_token.

Consejo: Los tests de integración usan la BD real (PostgreSQL en docker) — docker compose up -d db redis y correr python -m pytest tests/test_admin_integration.py tests/test_orders_integration.py. Los tests de unit NO requieren BD (repos mockeados).

Pasemos a lecciones aprendidas del testing.

 Los tres JSON i18n tenían una coma faltante → toda la app mostraba keys crudas. Hoy validado en pre-commit., Las fixtures E2E llamaban API sin prefijo la ruta api/v1 → cuatrocientos cuatro silenciosos. Se corrigió API_URL., El auth guard mantiene currentUser en memoria tras borrar localStorage → tests de redirect usan browser.newContext()., Flush vs raise: el patrón repo → bool la ruta raíz service → raise la ruta raíz flush DESPUÉS del raise. Flushear antes de un raise esperado rompe tests y oculta errores., pytest-asyncio en modo STRICT requiere @pytest.mark.asyncio por test. y MagicMock como session rompe en flush() — usar AsyncMock..

---

## Capítulo 13: Glosario

- JWT: JSON Web Token, RFC 7519. Token stateless firmado para autenticación. - 2FA/TOTP: Two-Factor Auth con Time-based One-Time Password (RFC seis mil doscientos treinta y ocho). - OAuth2: Protocolo de delegación de autorización — login social con Google. - TOCTOU: Time-Of-Check-To-Time-Of-Use — race condition entre verificar y usar. Se mitiga con updates condicionales atómicos. - CQRS: Command Query Responsibility Segregation — separar lecturas de escrituras. - FTS: Full-Text Search — búsqueda de texto completo (PostgreSQL tsvector). - Cache-aside: Patrón de caché donde la app lee cache, y en miss lee BD y rellena. - Event bus: Publicador/suscriptor en memoria para cross-cutting concerns. - ARQ: Cola de background jobs async nativa de asyncio, con Redis como broker. - mTLS: Mutual TLS — ambos lados presentan certificados (requerido para Swish live). - PaymentProvider: Interfaz abstracta que abstrae Stripe y Swish detrás de un contrato común. - Repository pattern: Capa de acceso a datos que encapsula SQLAlchemy; los services no tocan SQL. - JWT-exempt: Ruta que NO requiere JWT (webhooks de Stripe firman el payload). - Snapshot: Instancia ORM con estado persistente — los mocks de sesión deben ser AsyncMock.

---

Fin del libreto.
