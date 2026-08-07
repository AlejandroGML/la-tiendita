# La Tiendita — Arquitectura y Guía de Estudio — Libreto

Guía de estudio de la arquitectura fullstack de La Tiendita: e-commerce de ropa second-hand con backend hexagonal Litestar/Python + frontend Angular/PrimeNG + PostgreSQL + Redis.

Plataforma e-commerce fullstack para ropa de segunda mano: backend async Python con arquitectura hexagonal (Litestar 2.x), frontend Angular veintidos SPA con PrimeNG, PostgreSQL 16, Redis 7, Stripe payments, GDPR compliance, y worker de background jobs con ARQ. cuatro mil seiscientos dieciocho nodos en el grafo de código, setenta y uno tests E2E pasando, veintiocho specs de OpenSpec documentando cada decisión de arquitectura.

## Capítulo 1: Contexto

La Tiendita nace como proyecto de portafolio profesional con ambición de producción. El objetivo: demostrar end-to-end ownership sobre un sistema completo — desde la arquitectura hexagonal en el backend hasta la UX multi-idioma en el frontend, pasando por decisiones de infraestructura, testing y compliance regulatorio.

¿Por qué? Elegí construir esto como proyecto fullstack en vez de contribuir a open source. Un proyecto propio permite mostrar decisiones de arquitectura con fundamento real: por qué Litestar y no FastAPI, cómo escala CQRS en queries complejas, qué pasa cuando un carrito de invitado se mergea con uno de usuario autenticado.

Métricas del sistema (del grafo de código — graphify, veinticinco julio dos mil veintiséis):

Símbolos totales: valor: cuatro mil seiscientos dieciocho nodos. Relaciones: valor: diez mil cuatrocientos setenta y siete edges. Comunidades detectadas: valor: trescientos cincuenta y seis. Lenguajes: valor: TypeScript (ciento noventa y dos archivos), Python (ciento sesenta y ocho), HTML (setenta y dos), CSS (veintisiete). E2E tests: valor: setenta y uno passing, cero failures. Backend tests: valor: doscientos treinta y cinco passing (treinta archivos).

---

## Capítulo 2: Arquitectura General

El diagrama de arquitectura muestra los siguientes componentes: Cliente. Nginx. Controllers. Services. Repositories. PostgreSQL dieciséis. Redis siete. ARQ Worker. Stripe. Event Bus. Se muestran ocho conexiones entre estos componentes, representando el flujo de datos de la arquitectura.

Pasemos a cliente.

El frontend es una Angular veintidos SPA con standalone components, signals para estado reactivo, y RxJS para flujos asíncronos. Soporta tres idiomas (español, inglés, sueco) vía ngx-translate.

once módulos de features con lazy loading:

Home: ruta: la ruta raíz; descripción: Hero, categorías, nuevos arrivals, sale, newsletter. Auth: ruta: la ruta de login, la ruta de registro; descripción: JWT, 2FA TOTP, registro con consentimiento marketing. Products: ruta: la ruta de productos; descripción: Catálogo con FTS + ocho filtros multi-criterio. Product Detail: ruta: la ruta de detalle de producto; descripción: Galería, variantes, reviews, wishlist, tallas. Cart: ruta: la ruta del carrito; descripción: Guest merge, stock check, shipping. Checkout: ruta: la ruta de pago; descripción: Stripe Elements, resumen, stock reservation. Profile: ruta: la ruta de perfil; descripción: Órdenes, wishlist, datos, 2FA, GDPR export. Admin: ruta: la ruta admin, con comodín; descripción: Dashboard, CRUD productos/usuarios/categorías/órdenes/promos. Legal: ruta: la ruta de privacidad, la ruta de términos; descripción: GDPR, cookies, términos. Sale: ruta: la ruta de ofertas; descripción: Productos en oferta. New Arrivals: ruta: la ruta de novedades; descripción: Últimos productos.

Ahora, nginx.

Reverse proxy en producción: sirve la SPA compilada desde la ruta raíz y redirige la api al backend Litestar. Puerto 80, sin exposición directa de servicios internos.

Hablemos de api gateway.

catorce controllers Litestar mapean rutas REST a servicios. Cada controller:

 Recibe request con schemas Pydantic v2 validados automáticamente, Aplica guards (JWT, admin, optional auth) antes de entrar al handler, Delega lógica al service correspondiente y Retorna Response tipada con serialización automática.

Se ilustra la implementación con ProductController, list_products.

Veamos ahora servicios.

dieciocho servicios de negocio — cada uno con una responsabilidad única. El grafo de código identifica a ProductService como campeón cross-cutting (mayor betweenness centrality: 0.074, ciento cinco edges), conectando catálogo, variantes, caché, eventos y admin.

Servicios clave:

product_service.py: responsabilidad: Catálogo, CRUD, filtros, caché; conexiones: ciento cinco edges. auth_service.py: responsabilidad: Registro, login, refresh, 2FA, delete cascade; conexiones: más de sesenta edges. cart_service.py: responsabilidad: CRUD carrito, guest merge, stock check; conexiones: más de cincuenta edges. order_service.py: responsabilidad: Crear orden, stock reservation, estados; conexiones: más de cuarenta y cinco edges. stripe_service.py: responsabilidad: PaymentIntent, webhooks, refund; conexiones: más de treinta edges. email_service.py: responsabilidad: Transaccionales (confirmación, orden, reset); conexiones: más de veinticinco edges. audit_service.py: responsabilidad: Log de acciones con actor/acción/entidad; conexiones: —. dashboard_service.py: responsabilidad: Métricas admin (revenue, órdenes, usuarios); conexiones: —.

Consejo: Litestar resuelve automáticamente los parámetros de función como dependencias inyectadas. async def list_products(self, product_service: ProductService) — Litestar instancia o reusa ProductService según su scope configurado (singleton por defecto). Cero boilerplate de DI.

En cuanto a repositorios.

Capa de acceso a datos con repository pattern + SQLAlchemy 2.x async. Cada repositorio hereda de BaseRepository que expone CRUD genérico con AsyncSession.

Para queries complejas (dashboard, catálogo con filtros), se usa CQRS ligero:

Se ilustra la implementación con get_products_with_filters, search, category_slug.

Pasemos a persistencia.

 PostgreSQL dieciséis: datos relacionales + full-text search (tsvector con triggers automáticos). Alembic maneja migraciones que se aplican al iniciar la app. y Redis siete: cache-aside con TTL configurable por recurso (productos: cinco min, categorías: treinta min) + LRU eviction quinientos doce MB. También funciona como broker de ARQ para background jobs..

Información: La invalidación de caché se dispara por event bus: cuando un producto se actualiza, product_service emite ProductUpdated, el handler de caché escucha e invalida las keys relevantes. Sin dependencias circulares.

Ahora, event bus.

Infraestructura de publicador/suscriptor en memoria para cross-cutting concerns:

El diagrama de flujo muestra cómo se conectan los componentes: EventBus notifica hacia CacheInvalidationHandler. EventBus notifica hacia AuditLogHandler. EventBus notifica hacia NewsletterHandler.

El bus es síncrono y en memoria (no Redis pub/sub). Decisión deliberada: para el volumen actual, añadir un message broker introduce complejidad sin beneficio. Si escala, migrar a Redis Streams o NATS es trivial porque los handlers ya están desacoplados.

Hablemos de background jobs.

ARQ (Async Redis Queue) ejecuta tareas asíncronas fuera del ciclo request-response:

 Procesamiento de imágenes (redimensionar, convertir a WebP), Envío de emails transaccionales (reset password, confirmación orden, welcome) y Cleanup de tokens expirados.

¿Por qué? ARQ sobre Celery: este proyecto es async-first (Litestar + SQLAlchemy async). Celery requiere un thread pool separado para bridge sync/async. ARQ corre nativamente en el event loop de asyncio, solo necesita Redis (sin RabbitMQ), y el código de worker usa los mismos patrones async que la API. Para este tamaño de deploy, simplicidad gana.

Veamos ahora stripe.

Integración con Stripe para pagos con tarjeta. Flujo:

 primero, Frontend crea PaymentIntent vía endpoint la ruta stripe, create-payment-intent. segundo, Stripe Elements renderiza el formulario de pago en el frontend. tercero, Al confirmar, Stripe redirige a webhook la ruta stripe, webhook. cuarto, Webhook verifica firma, crea la orden, vacía carrito, envía email.

Se ilustra la implementación con create_payment_intent, dict.

Cuidado: El webhook de Stripe DEBE verificar la firma con stripe.Webhook.construct_event(). Sin verificación, cualquier persona puede enviar un POST falso marcando órdenes como pagadas. Este proyecto lo implementa correctamente.

---

## Capítulo 3: Flujos Clave End-to-End

En cuanto a auth jwt con 2fa.

El siguiente diagrama de secuencia describe el flujo entre: Usuario, Angular SPA, AuthController, AuthService, PostgreSQL. Usuario POST la ruta de login {email, password} hacia Angular SPA Angular SPA Request hacia AuthController AuthController authenticate(email, password) hacia AuthService AuthService SELECT user + bcrypt verify hacia PostgreSQL Si se cumple la condición de que totp enabled, AuthService requires_2fa: true hacia AuthController AuthController cuatrocientos uno + 2FA required hacia Angular SPA Angular SPA Mostrar input TOTP hacia Usuario Usuario Ingresar código seis dígitos hacia Angular SPA Angular SPA POST la ruta login, 2fa {code} hacia AuthController AuthController verify_totp(code) hacia AuthService y aquí termina esta parte del flujo. AuthService generate access_token + refresh_token hacia AuthService AuthService tokens hacia AuthController AuthController doscientos {access_token, refresh_token} hacia Angular SPA Angular SPA localStorage.setItem + currentUser signal hacia Angular SPA

El sistema usa rotación de tokens: el access token expira en quince minutos, el refresh token en siete días. El interceptor HTTP de Angular detecta 401, renueva con el refresh token, y re-intenta la petición original — transparente para el usuario.

Información: 2FA solo se requiere para usuarios con rol admin. El guard admin_guard verifica JWT + TOTP antes de permitir acceso a la ruta admin, con comodín. Los usuarios normales solo necesitan email + password.

Pasemos a checkout con stock reservation.

El siguiente diagrama de secuencia describe el flujo entre: Usuario, Angular, CheckoutController, OrderService, StockService, Stripe, Redis. Usuario Click "Pagar" hacia Angular Angular POST la ruta checkout {cart_id, shipping} hacia CheckoutController CheckoutController create_order() hacia OrderService OrderService reserve_stock(items) hacia StockService StockService SETNX stock-lock:{variant_id} (TTL 30s) hacia Redis StockService Verificar stock >= cantidad hacia StockService StockService Disminuir stock_available hacia StockService StockService stock reservado hacia OrderService OrderService Calcular total + shipping hacia OrderService OrderService create_payment_intent() hacia Stripe Stripe client_secret hacia OrderService OrderService {order_id, client_secret} hacia CheckoutController CheckoutController doscientos hacia Angular Angular stripe.confirmPayment() hacia Stripe Stripe payment confirmed hacia Angular Stripe POST la ruta stripe, webhook hacia CheckoutController CheckoutController confirm_order(order_id) hacia OrderService OrderService status → paid, cart → emptied hacia OrderService

Advertencia: La reserva de stock usa locks distribuidos en Redis (SETNX con TTL 30s). Si el pago no se completa en cinco minutos, un job de ARQ libera el stock reservado. Esto evita el problema clásico de "carritos abandonados agotando inventario".

Ahora, guest cart merge.

Cuando un usuario no autenticado agrega productos al carrito y luego inicia sesión:

El siguiente diagrama de secuencia describe el flujo entre: Guest (localStorage), Angular, AuthService, CartService, PostgreSQL. Guest (localStorage) localStorage cart_id = "abc-ciento veintitres" hacia Guest (localStorage) Guest (localStorage) Iniciar sesión hacia Angular Angular POST la ruta de login hacia AuthService AuthService JWT + user_id hacia Angular Angular POST la ruta cart, merge {guest_cart_id: "abc-ciento veintitres"} hacia CartService CartService Buscar guest cart hacia PostgreSQL CartService Buscar user cart (o crear) hacia PostgreSQL Repitiendo el siguiente paso mientras cada item del guest cart, CartService Si mismo variant_id → sumar cantidades hacia CartService CartService Si no existe → mover al user cart hacia CartService y aquí termina esta parte del flujo. CartService Eliminar guest cart hacia PostgreSQL CartService user_cart actualizado hacia Angular Angular actualizar cart signal hacia Angular

---

## Capítulo 4: Arquitectura del Frontend

Hablemos de estructura de features.

Veamos ahora state management.

La app usa dos estrategias según el caso:

Angular Signals: uso: Estado local + compartido simple; ejemplo: currentUser(), cartCount(), theme(). RxJS BehaviorSubject: uso: Flujos asíncronos multi-consumidor; ejemplo: CategoryService.categories$, CartService.cart$.

Los servicios de auth y carrito exponen signals computadas que se actualizan automáticamente:

En cuanto a guards e interceptors.

Pasemos a multi-idioma (i18n).

Tres archivos JSON con claves estructuradas:

ngx-translate carga el archivo correspondiente según navigator.language o preferencia guardada. El language switcher en el header persiste la selección en localStorage.

---

## Capítulo 5: Decisiones Técnicas y Tradeoffs

Cada decisión de arquitectura, framework y librería tiene una razón concreta. Acá están todas — ordenadas por categoría, con el qué, el por qué, y qué se rechazó.

Ahora, arquitectura.

¿Por qué arquitectura hexagonal (ports & adapters)?

¿Por qué? Separar el dominio (services) de la infraestructura (controllers, repositories, BD) permite tres cosas críticas para este proyecto: (uno) los servicios se testean sin BD ni HTTP — solo mocks de repositorios, (dos) cambiar PostgreSQL por otra cosa toca solo los repositories y models, no el dominio, y (tres) las reglas de negocio viven en UN lugar — no duplicadas entre controllers y frontend. El repository pattern además centraliza las queries para que el CQRS sea limpio.

Rechazado: MVC plano (models-views-controllers sin separación de servicios). En MVC, la lógica de negocio tiende a acumularse en controllers o models, creando acoplamiento. Para un e-commerce con dieciocho servicios de negocio distintos, ese acoplamiento haría el código inmantenible.

¿Por qué repository pattern y no ORM directo en services?

Se ilustra la implementación con ProductService, get_products.

Se ilustra la implementación con ProductService, get_products.

¿Por qué? El repository pattern crea una frontera clara: los services no saben SQL ni SQLAlchemy — solo hablan con interfaces de repositorio. Esto permite: (uno) mockear repositorios en tests unitarios sin BD, (dos) centralizar queries complejas (CQRS) en un solo lugar, y (tres) si mañana migro a MongoDB, solo cambio los repositorios, no los dieciocho servicios.

¿Por qué event bus en memoria y no message broker?

¿Por qué? El event bus resuelve cross-cutting concerns (audit log, cache invalidation, emails) sin acoplar servicios entre sí. Usar un broker (Redis pub/sub, RabbitMQ) añadiría complejidad operacional (latencia de red, manejo de reconexión, ordering guarantees) sin beneficio en este volumen. El bus síncrono en memoria ejecuta los handlers en el mismo request, lo que es correcto para acciones que DEBEN pasar antes del commit (audit log). Si escala, migrar a Redis Streams es trivial porque los handlers ya están desacoplados por interfaz.

¿Por qué cache-aside y no write-through o write-back?

¿Por qué? Cache-aside es el patrón más simple y resiliente: si Redis cae, la app sigue funcionando (lee directo de BD, solo más lento). Write-through acopla escritura a la disponibilidad de Redis. Write-back puede perder datos si Redis muere antes del flush. Para un e-commerce donde la consistencia de inventario y órdenes es crítica, cache-aside + invalidación por event bus da el balance correcto: lecturas rápidas, escrituras seguras.

¿Por qué JWT y no server sessions?

Escalado horizontal: jwt: Stateless — cualquier instancia valida; server sessions: Requiere sesión compartida (Redis/DB). Mobile/OAuth: jwt: Nativo — token en header; server sessions: Cookies con CORS son complejas en mobile. Invalidación: jwt: Refresh token rotation + blacklist; server sessions: Borrar sesión en store. Tamaño: jwt: aproximadamente quinientos bytes self-contained; server sessions: Session ID + lookup en cada request.

¿Por qué? JWT permite escalar horizontalmente sin estado compartido: cualquier instancia de la API puede validar un token con solo la firma (secret compartido). Las sessions requieren un store compartido (Redis o DB) que se consulta en CADA request autenticada. Para un deploy que puede crecer a múltiples instancias, JWT elimina un punto de falla. El tradeoff (invalidación) se maneja con refresh token rotation de siete días — si un token se compromete, expira rápido.

Hablemos de stack de backend.

¿Por qué Litestar y no FastAPI?

Dependency Injection: litestar: Nativo con scopes (singleton, request, connection); fastapi (rechazado): Requiere python-dependency-injector externo. Guards de auth: litestar: Declarativos tipados como decoradores; fastapi (rechazado): Dependencias como callables manuales. Event system: litestar: Señales incorporadas (para event bus); fastapi (rechazado): No nativo — requiere librería. OpenAPI: litestar: Generación desde tipos Python, muy configurable; fastapi (rechazado): Automática pero menos flexible. Maturidad: litestar: Más nuevo, menos comunidad; fastapi (rechazado): Estándar de facto, enorme comunidad.

Consejo: La pregunta real en entrevista no es "¿Litestar o FastAPI?" sino "¿por qué elegiste una alternativa menos popular?". Respuesta: Litestar resuelve mejor los problemas CONCRETOS de este proyecto — DI scoped para servicios que comparten sesión de BD, guards declarativos para rutas admin/públicas, y señales integradas para el event bus. FastAPI es excelente, pero Litestar eliminó tres dependencias externas y aproximadamente doscientas líneas de boilerplate. El tradeoff aceptado: menos talent pool y documentación comunitaria.

¿Por qué SQLAlchemy 2.x async y no SQLModel o Tortoise?

¿Por qué? SQLAlchemy 2.x es el ORM más maduro del ecosistema Python (más de quince años), con soporte async nativo desde 2.0, ecosistema enorme (Alembic para migraciones, tipos GIS, FTS), y permite mezclar ORM y SQL crudo según convenga (esencial para CQRS). SQLModel (de FastAPI) es un wrapper sobre SQLAlchemy que acopla modelo de BD a schema de API — viola la separación de capas. Tortoise es async-native pero tiene un ecosistema más pequeño y menos herramientas. SQLAlchemy gana por madurez, flexibilidad y ecosystem.

¿Por qué Pydantic v2 para DTOs?

¿Por qué? Pydantic v2 (escrito en Rust) valida y serializa de cinco a diez veces más rápido que v1. Permite definir DTOs (Data Transfer Objects) con tipos Python puros que Litestar usa para validación automática de requests y generación de OpenAPI. Alternativa: dataclasses no valida tipos en runtime ni genera schema. marshmallow es más lento y menos integrado con type checkers. Pydantic v2 es el estándar de facto en Python moderno para validación de datos en boundaries.

¿Por qué PostgreSQL dieciséis y no MySQL o SQLite?

Full-Text Search: postgresql dieciséis: tsvector nativo con ranking; mysql ocho: LIMITADO (sin ranking decente); sqlite: LIMITADO (FTS5 básico). JSON columns: postgresql dieciséis: JSONB con indexación y operadores; mysql ocho: JSON sin indexación eficiente; sqlite: JSON1 como extensión. Tipos avanzados: postgresql dieciséis: UUID, ARRAY, Range, tsvector; mysql ocho: Más limitado; sqlite: Limitado. Concurrency: postgresql dieciséis: MVCC (lectores no bloquean escritores); mysql ocho: MVCC pero con gotchas; sqlite: Single-writer lock.

¿Por qué? PostgreSQL se eligió por dos features críticas para e-commerce: Full-Text Search nativo (tsvector con triggers automáticos) permite buscar productos sin añadir Elasticsearch, y JSONB permite almacenar metadatos flexibles (variantes, atributos) con indexación. MySQL tendría FTS limitado y SQLite no soporta concurrencia para un sistema con background workers escribiendo.

¿Por qué Redis siete (cache + queue) y no Memcached + RabbitMQ?

¿Por qué? Redis hace dos trabajos aquí: cache-aside con TTL configurable y broker de ARQ para background jobs. Usar Memcached (solo cache) + RabbitMQ (solo queue) añadiría un servicio más que operar. Redis siete tiene data structures ricas (strings, sets, sorted sets, streams), persistencia opcional, y LRU eviction nativo. Para este tamaño, un servicio que hace dos cosas > dos servicios especializados.

¿Por qué python-jose para JWT y no PyJWT?

¿Por qué? python-jose soporta más algoritmos (incluyendo EdDSA que PyJWT añadió tarde) y tiene mejor manejo de claims. Ambos son válidos. La diferencia clave: python-jose está más alineado con flujos OAuth2/OIDC, que será necesario cuando se implemente Google OAuth real. PyJWT es más simple si solo necesitas firmar/verificar tokens. Como el roadmap incluye OAuth, python-jose fue la elección forward-compatible.

¿Por qué PyOTP para 2FA?

¿Por qué? PyOTP implementa TOTP (RFC seis mil doscientos treinta y ocho) y HOTP (RFC cuatro mil doscientos veintiséis) — los estándares que usan Google Authenticator, Authy y 1Password. Generar un secret base32 y validar códigos de seis dígitos en tres líneas. Alternativas: speakeasy (Node.js, no aplica), o implementar TOTP manual (innecesario y propenso a errores). PyOTP es la opción canónica en Python.

¿Por qué bcrypt para passwords y no argon2?

¿Por qué? bcrypt tiene veinticinco años de batalla probada y es el estándar de la industria. argon2 (ganador de la Password Hashing Competition dos mil quince) es teóricamente superior (resistente a GPU/ASIC) pero requiere librerías nativas (argon2-cffi) que pueden fallar al compilar en algunos entornos. Para un portafolio que prioriza "funciona en cualquier Linux sin drama", bcrypt via passlib es la elección pragmática. Si escalara a producción con amenazas reales, migrar a argon2 es cambiar una línea en passlib.CryptContext.

¿Por qué Stripe y no MercadoPago la ruta raíz PayPal?

¿Por qué? Stripe tiene la mejor documentación técnica, SDK maduro para Python, webhooks con firma criptográfica, y Stripe Elements para formularios PCI-compliant sin tocar datos de tarjeta. MercadoPago es fuerte en LATAM pero con documentación fragmentada. PayPal tiene fees altos y UX invasiva. Para un proyecto de portafolio dirigido al mercado sueco/europeo, Stripe es la opción que más reclutadores reconocen. El webhook verifica firma con stripe.Webhook.construct_event() — crítico de seguridad.

Veamos ahora stack de frontend.

¿Por qué Angular veintidos y no React o Vue?

Opinión de estructura: angular veintidos: Opinable — modular por diseño; react diecinueve: Libre — requiere decisiones; vue tres: Semi-opinable. TypeScript: angular veintidos: Nativo, first-class; react diecinueve: Opcional (JSX mezcla); vue tres: Soporte pero opcional. Forms complejos: angular veintidos: Reactive Forms + validación; react diecinueve: Librerías externas (react-hook-form); vue tres: VueUse pero menos maduro. Enterprise-scale: angular veintidos: DI, módulos lazy, guards nativos; react diecinueve: Requiere arquitectura manual; vue tres: Similar a React. Signals: angular veintidos: Nativas desde v17; react diecinueve: useEffect/useMemo (diferente); vue tres: ref/reactive.

¿Por qué? Angular se eligió porque su estructura opinable (DI, módulos, guards, interceptores) fuerza una arquitectura consistente sin debates de "¿cómo organizamos esto?". Para un e-commerce con once features, auth con guards, interceptores HTTP y formularios complejos (checkout, admin product form), Angular da las herramientas nativas. React las requiere ensamblar de múltiples librerías. El tradeoff: curva de aprendizaje más alta, pero el resultado es más predecible y mantenible en escala.

¿Por qué PrimeNG y no Angular Material?

Angular Material (CDK + Components) es el estándar, pero:

Tablas con sort, filter, pagination: primeng: p-table nativo, uno componente; angular material: Requiere MatTableDataSource + config manual. Multi-select con chips: primeng: p-multiSelect listo; angular material: No existe — hay que construir. File upload con preview: primeng: p-fileUpload con templates; angular material: No existe. Iconos completos (más de dos mil quinientos): primeng: PrimeIcons incluido; angular material: Material Icons (limitado, sin e-commerce). Dark mode: primeng: Toggle nativo con variables CSS; angular material: Requiere tema custom. Form validation visual: primeng: Integrado con p-input; angular material: Manual con mat-error.

Error común: No confundir "más popular" con "mejor para tu caso de uso". Angular Material es sobresaliente para dashboards empresariales. Pero una tienda necesita multi-select para filtros, file upload para imágenes de producto, y dos mil quinientos iconos (moda, pagos, redes sociales). PrimeNG cubre esto sin componentes custom. La decisión fue técnica, no estética.

¿Por qué Signals + RxJS y no NgRx?

¿Por qué? NgRx (Redux para Angular) añade cuatro conceptos (actions, reducers, selectors, effects) y boilerplate significativo. Es excelente para apps con estado global complejo y time-travel debugging. Pero La Tiendita tiene estado mayoritariamente local por feature: el carrito vive en CartService, auth en AuthService, catálogo en ProductService. Angular Signals (estado reactivo simple) + RxJS BehaviorSubject (flujos asíncronos multi-consumidor) cubren el cien% de los casos sin el overhead. YAGNI — si el estado global se complica, migrar a NgRx es incremental.

¿Por qué ngx-translate y no i18n nativo de Angular?

¿Por qué? El i18n nativo de Angular (@angular/localize) compila un build POR idioma — tres builds para es/en/sv. ngx-translate carga archivos JSON en runtime, permitiendo cambiar idioma sin recargar la app. Para un e-commerce con un language switcher en el header (UX crítica para mercado multilingüe sueco), el cambio en caliente de ngx-translate es no-negociable. El tradeoff: ngx-translate añade una dependencia y los pipes pueden impactar performance en listas grandes (mitigado con pure: false controlado).

¿Por qué Tailwind CSS v3 + PrimeUI y no SCSS puro?

¿Por qué? Tailwind da utility classes para layouts y spacing rápido sin escribir CSS custom. PrimeUI provee el design system de PrimeNG (colores, sombras, tipografía) como variables CSS. Juntos: Tailwind estructura, PrimeUI tematiza. Alternativa: SCSS custom desde cero = semanas de trabajo en un design system. Para un portafolio donde el foco es arquitectura y UX, no pixel-pushing CSS, esta combinación es la más productiva. El riesgo (Tailwind purista genera HTML verbose) se mitiga extrando componentes Angular.

En cuanto a infraestructura.

¿Por qué Docker multi-stage y no imágenes planas?

¿Por qué? Multi-stage build separa el contexto de build (compiladores, node_modules, devDependencies) del runtime final. Resultado: imagen de producción de aproximadamente ciento cincuenta MB en vez de aproximadamente ochocientos MB. Menos superficie de ataque, deploys más rápidos, menos costo de bandwidth. Para Python: python:3.14-slim como base runtime. Para Angular: build con node, sirve con nginx:alpine (aproximadamente treinta MB).

¿Por qué Nginx como reverse proxy y no exponer la API directo?

¿Por qué? Nginx como reverse proxy da cuatro beneficios: (uno) termination de TLS/SSL centralizado, (dos) servir archivos estáticos de la SPA sin pasar por Python, (tres) rate limiting y protección DDoS a nivel de edge, y (cuatro) poder rotar instancias de backend sin que el cliente lo note. Exponer uvicorn directo al internet es un anti-patrón — no maneja TLS, no sirve estáticos eficientemente, y no protege contra tráfico malicioso.

¿Por qué GitHub Actions y no Jenkins o GitLab CI?

¿Por qué? GitHub Actions es nativo del repositorio (cero setup de infra), tiene marketplace de actions reutilizables, y minutos gratuitos para proyectos open source. Jenkins requiere mantener un servidor. GitLab CI requiere migrar de GitHub. Para un proyecto que ya está en GitHub, Actions es la opción de menor fricción. El tradeoff: menos control que Jenkins self-hosted, pero suficiente para CI/CD de este tamaño.

Pasemos a anti-patrones evitados.

¿Por qué NO microservicios?

Cuidado: Para un proyecto de este tamaño (un desarrollador, e-commerce de portafolio), microservicios serían over-engineering. Añadirían: complejidad de deployment (más de ocho servicios), latencia de red entre servicios, consistencia distribuida (sagas, outbox pattern), y observabilidad compleja (distributed tracing). La arquitectura hexagonal modular permite extraer un microservicio cuando un módulo lo justifique por carga — pero partir ahí es prematuro. Monolith first, extraer después.

¿Por qué NO GraphQL y REST sí?

¿Por qué? GraphQL brilla cuando hay múltiples clientes con necesidades de datos distintas (mobile quiere menos campos que desktop). Para este proyecto con un solo cliente (Angular SPA) y endpoints bien definidos, REST es más simple: caché HTTP nativo, semántica de status codes, y tooling más maduro. GraphQL añade complejidad (resolvers, N+uno prevention con DataLoader, schema federation) sin beneficio acá. Si el día de mañana hay un mobile nativo con necesidades distintas, GraphQL sería el camino.

¿Por qué NO event sourcing?

¿Por qué? Event sourcing (guardar cada cambio como evento inmutable) da auditoría perfecta y time-travel, pero añade complejidad masiva: event store, proyecciones, snapshots, y eventual consistency. El audit log tradicional (tabla con actor/acción/entidad/timestamp) cubre el requisito de compliance a una fracción del costo. Event sourcing se justifica en sistemas financieros o de inventario hiper-regulado. Para un e-commerce de portafolio, es innecesario.

---

## Capítulo 6: Infraestructura

Ahora, docker compose (dev).

Se ilustra la implementación con services, postgres, redis, api, frontend.

Hablemos de producción.

En producción se agrega docker-compose.prod.yml que:

 Reemplaza el frontend dev por nginx:alpine sirviendo la SPA compilada, La API corre con uvicorn (no --reload), ARQ worker se ejecuta como servicio separado y Volúmenes persistentes para uploads y BD.

Se ilustra la implementación con services, nginx, volumes.

---

## Capítulo 7: Testing

Veamos ahora estrategia por capa.

Backend unit: framework: pytest + pytest-asyncio; archivos: treinta; resultado: doscientos treinta y cinco passed, veintiocho skipped (env). Backend integration: framework: pytest + httpx; archivos: Incluido en unit; resultado: —. Frontend unit: framework: Karma + Jasmine; archivos: cincuenta y cinco specs; resultado: Configurado. E2E: framework: Playwright; archivos: cincuenta y cinco specs; resultado: setenta y uno passed, cero failures.

En cuanto a patrones de testing usados.

Se ilustra la implementación con test_login_returns_tokens_for_valid_credentials.

Consejo: Los tests E2E usan fixtures con seed determinista: cada spec siembra exactamente los datos que necesita y limpia al terminar. Esto permite correr tests en paralelo sin interferencia.

Pasemos a lecciones aprendidas del testing e2e.

 Los tres JSON i18n tenían una coma faltante en la línea ciento noventa y dos — toda la app mostraba keys crudas. Hoy está validado en pre-commit., Las fixtures E2E llamaban API sin prefijo la ruta api/v1 → cuatrocientos cuatro silenciosos en register/login. Se corrigió el API_URL en todas las fixtures. y El auth guard de Angular mantiene currentUser en memoria incluso tras borrar localStorage → los tests de redirect ahora usan browser.newContext() para sesión fresca..

---

Fin del libreto.
