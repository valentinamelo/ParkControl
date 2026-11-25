# ParkControl

App web para administrar un parqueadero de carros y motos.
Backend en **Django + Django REST Framework** (API con JWT) y frontend en **Angular 20**.

Los 4 avances de la planeación están completos: login por rol, configuración del administrador,
operación (entrada, tiquete con código de barras, salida con escáner, cobro y mensualidades),
dashboard, reportes PDF/Excel, bitácora, anulación de tiquetes, pruebas y despliegue con Docker.

- [Cómo correrlo en desarrollo](#cómo-correrlo)
- [Despliegue](#despliegue)
- [Pruebas](#pruebas)
- [Manual de usuario](docs/MANUAL.md)

## Avance 1 — Base del proyecto, login y primeras pantallas

- Backend con las 7 apps y todos los modelos: usuarios, configuración, espacios, vehículos, operaciones, mensualidades y reportes.
- Login con JWT por correo; el token lleva el rol (`ADMIN` o `TRABAJADOR`).
- API de solo lectura: espacios (con el vehículo que lo ocupa), vehículos con búsqueda por placa, tarifas, horarios y parqueadero.
- Frontend con sidebar según el rol, guards de ruta e interceptor del token.
- Pantallas: login, dashboard, movimientos, espacios (mapa + detalle), vehículos y configuración (solo admin).
- Redirección por rol: el administrador entra al dashboard y el trabajador a movimientos.

## Avance 2 — Módulo del administrador

- **Usuarios (RF-03):** el administrador crea, edita, desactiva y reactiva usuarios. Desactivar no borra al usuario, solo le impide iniciar sesión. El administrador no puede desactivarse ni quitarse su rol.
- **Espacios (RF-04 a RF-06):** creación uno a uno o en lote (zona + cantidad; si la zona no existe se crea con su tipo de vehículo y la numeración continúa, p. ej. A-06, A-07…). Activar, desactivar y eliminar espacios; un espacio ocupado no se puede desactivar, mover ni eliminar, y uno con historial solo se desactiva. El tipo de vehículo de cada espacio es el de su zona y se cambia desde la tabla de zonas.
- **Tarifas (RF-07):** por hora o por fracción, minutos de gracia y tope diario. Cambiar una tarifa no la modifica: crea una nueva vigente y la anterior queda en el historial, así los tiquetes ya cobrados conservan su valor. También se crean y eliminan tipos de vehículo.
- **Horarios (RF-08)** por día de la semana y **datos del parqueadero** (nombre, NIT, dirección, teléfono).
- **Vehículos (RF-09):** registrar, buscar por placa, editar y eliminar (ambos roles). La placa se guarda normalizada (`abc-123` → `ABC123`).
- Validaciones en los serializers con mensajes en español, que el frontend muestra debajo de cada campo.
- Cada cambio de configuración queda en la bitácora (`reportes.Bitacora`); la pantalla para consultarla llega en el avance 4.
- Permisos: el trabajador lee la configuración pero solo el administrador la cambia (`AdminOSoloLectura`); `usuarios/` es solo para el administrador (`EsAdministrador`).

## Avance 3 — Operación: entradas, salidas, tiquete y mensualidades

- **Entrada (RF-11, RF-12):** al escribir la placa se consulta si el vehículo existe, si ya está dentro o si tiene mensualidad. Si es nuevo, se registra en el mismo formulario. Solo se ofrecen espacios DISPONIBLES del mismo tipo; se preselecciona el primero (o el espacio fijo de la mensualidad). Si la placa es nueva, el tipo se elige solo según su formato: `ABC123` carro, `ABC12D` moto (se puede cambiar). Se genera el tiquete con un código aleatorio, no consecutivo, con la inicial del tipo de vehículo (`C-7K4M2QXR` carro, `M-3HQ8ZK2W` moto), para que no se puedan adivinar ni falsificar los de otros vehículos, con código de barras Code128 listo para imprimir (formato de impresora térmica de 80 mm).
- **Salida (RF-13 a RF-15):** campo con foco para el lector USB (escribe el código y envía Enter), también se puede digitar (sin importar mayúsculas ni el guion: `c7k4m2qxr`) o escanear con la cámara. Muestra tiempo, tarifa y total; se elige el método de pago y el espacio queda libre.
- **Cobro (RF-14):** siempre en el backend (`apps/operaciones/reglas.py`) con la tarifa vigente: `min(⌈(minutos − gracia) / fracción⌉ × valor, tope_diario)`. El tiempo se mide en segundos y cada minuto empezado cuenta (30 s dentro ya cobran la primera hora o fracción si no hay gracia); el tiquete guarda la duración exacta. En estadías de más de 24 h cada día completo cobra el tope. Si la tarifa tiene **valor de primera hora**, la primera hora empezada cuesta ese valor y el resto se cobra por horas o fracciones con el valor normal (la primera hora se cobra una sola vez).
- **Pernoctación:** cada tarifa puede tener un valor por noche. Si lo tiene, las horas se cobran solo dentro del horario de atención y cada noche que el vehículo pasa dentro con el parqueadero cerrado (cada medianoche fuera de horario) se cobra aparte. Ejemplo con horario 06:00–22:00, $4.000 la hora y $15.000 la noche: de lunes 20:00 a martes 08:00 son 4 h ($16.000) + 1 noche ($15.000) = $31.000. Sin valor de pernoctación se cobra el tiempo corrido, como antes.
- **Mensualidades (RF-16 a RF-18):** el admin crea planes en Configuración → Planes mensuales. Ambos roles venden y renuevan: el cliente se busca por documento y se crea si no existe. La vigencia cuenta el día de inicio (30 días desde el 1 llegan hasta el 30). Renovar crea una nueva que empieza al día siguiente de vencer la anterior (o hoy, si ya venció). Con mensualidad vigente la salida es $0 y se usa el espacio fijo, que no se ofrece a otros vehículos.
- **Vehículos dentro (RF-19)** con tiempo y valor a la fecha; la lista y el mapa de espacios se actualizan solos cada 15 s.
- Cada entrada, salida, venta y renovación queda en la bitácora.

**Decisiones sobre las preguntas abiertas de la planeación** (fáciles de cambiar si el equipo decide otra cosa):

- **Entrada fuera de horario:** el trabajador no puede registrarla; el administrador sí, confirmándolo en pantalla. Si un día no tiene horario configurado, no se restringe.
- **Tiquete perdido:** en la salida se escribe la placa en lugar del código y se cobra el tiempo más una multa fija, que el administrador configura en Configuración → Parqueadero (por defecto $10.000).

Tarea diaria opcional (las consultas ya marcan las vencidas al vuelo):

```bash
python manage.py marcar_mensualidades_vencidas
```

## Avance 4 — Integración, reportes y entrega final

- **Dashboard (RF-20):** espacios totales, ocupados y disponibles (por tipo de vehículo), ingresos y movimientos del día, ingresos de la semana y mensualidades por vencer. El trabajador ve solo su turno: los pagos, entradas y salidas que él registró hoy. Se actualiza cada 15 s.
- **Reporte de ingresos (RF-21):** por rango de fechas, tipo de vehículo, método de pago, trabajador y concepto (parqueo o mensualidad), con rangos rápidos (hoy, últimos 7 días, este mes, mes anterior), ingresos por día y desgloses.
- **Exportar (RF-22):** el mismo reporte en PDF (ReportLab) y Excel (openpyxl, con hojas Resumen, Por día y Detalle).
- **Bitácora (RF-23):** quién registró cada entrada, salida, venta, anulación y cambio de configuración, con filtros por fecha, usuario, acción y texto, paginada de a 50.
- **Anular tiquete (RF-24):** solo el administrador y con motivo obligatorio. Un tiquete abierto libera su espacio; uno cerrado deja de contar en los ingresos (así se corrige un cobro). Queda en la bitácora.
- **Pruebas:** 97 pruebas del backend (cálculo de tarifas con casos límite, reglas de entrada y salida, mensualidades, reportes y la matriz de permisos por rol) y 14 de punta a punta con Playwright, incluida una revisión de que ninguna pantalla se desborde en tablet y celular.
- **Despliegue:** un solo contenedor (Django sirve la API y el build de Angular) con PostgreSQL; `docker-compose.yml` para correrlo igual que en producción y `render.yaml` para publicarlo en Render.

## Cómo correrlo

Se necesitan **Python 3.10+** y **Node 20.19+ o 22.12+**. Abre dos terminales en VS Code.

### Terminal 1 — Backend (puerto 8000)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py cargar_datos_iniciales
python manage.py runserver
```

### Terminal 2 — Frontend (puerto 4200)

```bash
cd frontend
npm install
npm start
```

Abre http://localhost:4200

## Usuarios de prueba

| Rol | Correo | Contraseña |
| --- | --- | --- |
| Administrador | admin@parkcontrol.com | Admin123* |
| Trabajador | trabajador@parkcontrol.com | Trabajador123* |
| Administrador | brayan@parkcontrol.com (Brayan Fuertes) | Brayan123* |
| Trabajador | valentina@parkcontrol.com (Valentina Melo) | Valentina123* |
| Trabajador | laura@parkcontrol.com (Laura Gómez) | Laura123* |

El panel de Django está en http://localhost:8000/admin/ (entra con el usuario administrador).

Si cambias de rama o traes cambios del repositorio, vuelve a correr `python manage.py migrate` (y `npm install` si cambió `package.json`).

## Despliegue

En producción todo corre en **un solo servicio**: Django sirve la API en `/api/` y el build de Angular en `/`, así que no hay que configurar CORS ni otra URL para el frontend. La base de datos es PostgreSQL.

### Probarlo como en producción (Docker)

Con Docker Desktop abierto, desde la raíz del repositorio:

```bash
docker compose up --build
```

Abre http://localhost:8080 (mismos usuarios de prueba). La primera vez tarda unos minutos porque compila Angular. Para apagarlo: `docker compose down` (agrega `-v` para borrar también la base).

### Publicarlo en Render

1. Sube el repositorio a GitHub.
2. En https://render.com: **New + → Blueprint**, elige el repositorio. Render lee `render.yaml` y crea la base PostgreSQL y el servicio web.
3. Cuando termine, la app queda en `https://parkcontrol-xxxx.onrender.com`.

En el plan gratuito el servicio se duerme tras 15 minutos sin uso y la primera visita tarda ~1 minuto en despertarlo.

**Importante:** `CARGAR_DATOS_INICIALES=1` crea los usuarios de prueba con las contraseñas de este README. Para la sustentación sirve; para un uso real, entra como administrador, crea los usuarios definitivos, desactiva los de prueba y quita esa variable.

### Variables de entorno

| Variable | Para qué | Por defecto |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Clave secreta (obligatoria en producción) | Una de desarrollo |
| `DJANGO_DEBUG` | `0` en producción | `1` |
| `DATABASE_URL` | `postgres://usuario:clave@host:5432/base` | SQLite (`backend/db.sqlite3`) |
| `DJANGO_ALLOWED_HOSTS` | Dominios separados por coma | `localhost,127.0.0.1` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Orígenes https para entrar al `/admin` | — |
| `DJANGO_CORS_ORIGINS` | Solo si el frontend se publica en otro dominio | — |
| `CARGAR_DATOS_INICIALES` | `1` carga los datos de prueba al arrancar | — |

Render define `RENDER_EXTERNAL_HOSTNAME` y el proyecto lo agrega solo a los hosts permitidos. En otro hosting (Railway, Fly.io) usa el mismo `Dockerfile` y define las variables de la tabla.

## Pruebas

### Backend (Django TestCase)

```bash
cd backend
python manage.py test apps
```

Cubren el cálculo de tarifas con casos límite, las reglas de entrada y salida, mensualidades, reportes, exportes, bitácora, anulación y la matriz de permisos por rol.

### De punta a punta (Playwright)

Corren contra la app levantada con Docker:

```bash
docker compose up -d --build
cd e2e
npm install
npx playwright install chromium
npm test
```

Para otra URL: `PARKCONTROL_URL=https://tu-app.onrender.com npm test`. El informe queda en `e2e/playwright-report` (`npm run reporte`).

## Endpoints

Avance 1:

| Endpoint | Método | Descripción |
| --- | --- | --- |
| `/api/auth/login/` | POST | `{email, password}` → `{access, refresh, usuario}` |
| `/api/auth/refresh/` | POST | Renueva el token de acceso |
| `/api/auth/me/` | GET | Usuario autenticado |
| `/api/espacios/?estado=&tipo=` | GET | Espacios con su ocupante |
| `/api/zonas/` | GET | Zonas |
| `/api/vehiculos/?placa=` | GET | Vehículos, búsqueda por placa |
| `/api/tipos-vehiculo/` | GET | Carro, Moto |
| `/api/tarifas/` | GET | Tarifas vigentes |
| `/api/horarios/` | GET | Horario de atención |
| `/api/parqueadero/` | GET | Datos del parqueadero |

Avance 2 (los CRUD exponen GET, POST, PUT/PATCH y DELETE; escribir es solo para el administrador salvo en vehículos):

| Endpoint | Método | Descripción |
| --- | --- | --- |
| `/api/usuarios/` | CRUD (admin) | DELETE desactiva al usuario en lugar de borrarlo |
| `/api/espacios/` | CRUD | Sin `codigo` al crear, toma el siguiente libre de la zona |
| `/api/espacios/lote/` | POST | `{zona, tipo_vehiculo?, cantidad}` crea varios espacios seguidos |
| `/api/zonas/` | CRUD | Cambiar `tipo_vehiculo` cambia el tipo de todos sus espacios |
| `/api/tipos-vehiculo/` | CRUD | |
| `/api/tarifas/?historial=1` | CRUD | PUT/PATCH crea una tarifa nueva vigente; DELETE la deja sin vigencia |
| `/api/horarios/` | CRUD | |
| `/api/parqueadero/` | GET, PUT, PATCH | |
| `/api/vehiculos/` | CRUD (ambos roles) | No se elimina un vehículo con tiquetes o mensualidades |

Avance 3 (ambos roles salvo los planes, que solo crea el administrador):

| Endpoint | Método | Descripción |
| --- | --- | --- |
| `/api/tiquetes/consultar-placa/?placa=` | GET | Si el vehículo existe, si está dentro y si tiene mensualidad |
| `/api/espacios/disponibles/?tipo=&placa=` | GET | Espacios libres del tipo, sin los fijos de otras mensualidades |
| `/api/tiquetes/entrada/` | POST | `{placa, tipo_vehiculo?, espacio?, marca?, modelo?, color?, forzar?}` |
| `/api/tiquetes/{codigo}/?perdido=1` | GET | Tiquete y cobro calculado al momento |
| `/api/tiquetes/{codigo}/salida/` | POST | `{metodo?, tiquete_perdido?}` cierra, crea el pago y libera el espacio |
| `/api/tiquetes/activos/?placa=` | GET | Vehículos dentro con tiempo y valor a la fecha |
| `/api/tiquetes/?estado=&placa=` | GET | Historial (últimos 100) |
| `/api/clientes/?documento=&q=` | CRUD | |
| `/api/planes-mensuales/?activos=1` | CRUD | DELETE de un plan ya vendido lo desactiva |
| `/api/mensualidades/?estado=&q=` | GET, POST | POST vende: `{documento, nombre, telefono?, correo?, placa, plan, espacio_fijo?, fecha_inicio?, metodo}` |
| `/api/mensualidades/{id}/renovar/` | POST | `{metodo, plan?}` |

Avance 4:

| Endpoint | Método | Rol | Descripción |
| --- | --- | --- | --- |
| `/api/dashboard/resumen/` | GET | Ambos | Ocupación e ingresos de hoy (el trabajador, los de su turno) |
| `/api/reportes/ingresos/?desde=&hasta=&tipo=&metodo=&usuario=&concepto=&formato=` | GET | Admin | `formato` = `json`, `pdf` o `xlsx` |
| `/api/bitacora/?desde=&hasta=&usuario=&accion=&q=&page=` | GET | Admin | Paginada de a 50 |
| `/api/bitacora/acciones/` | GET | Admin | Acciones registradas (para el filtro) |
| `/api/tiquetes/{codigo}/anular/` | POST | Admin | `{motivo}` |
| `/api/salud/` | GET | Público | Health check del hosting |

## Estructura

```
ParkControl/
├── Dockerfile, docker-compose.yml, render.yaml   # despliegue
├── docs/MANUAL.md            # manual de usuario
├── e2e/                      # pruebas de punta a punta (Playwright)
├── backend/
│   ├── parkcontrol/          # settings (por variables de entorno), urls, manejo de errores
│   └── apps/
│       ├── usuarios/         # Usuario con rol, login JWT, permisos
│       ├── configuracion/    # Parqueadero, TipoVehiculo, Tarifa, Horario + datos iniciales
│       ├── espacios/         # Zona, Espacio
│       ├── vehiculos/        # Cliente, Vehiculo
│       ├── operaciones/      # Tiquete, Pago + reglas de cobro (reglas.py)
│       ├── mensualidades/    # PlanMensual, Mensualidad + vigencias (reglas.py)
│       └── reportes/         # Bitacora, dashboard, reporte de ingresos y exportes PDF/Excel
└── frontend/src/app/
    ├── core/                 # auth.service, interceptor, guards, api.service, errores, modelos
    ├── shared/               # layout (sidebar), stat-card, modal, codigo-barras, escaner, graficos
    └── features/             # login, dashboard, espacios, vehiculos, mensualidades,
                              # movimientos/ (lista, entrada, salida, tiquete),
                              # configuracion/ (tarifas, planes, horarios, usuarios, parqueadero),
                              # reportes/ (ingresos, bitacora)
```
