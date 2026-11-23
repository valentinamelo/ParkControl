# ParkControl

App web para administrar un parqueadero de carros y motos.
Backend en **Django + Django REST Framework** (API con JWT) y frontend en **Angular 20**.

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

- **Entrada (RF-11, RF-12):** al escribir la placa se consulta si el vehículo existe, si ya está dentro o si tiene mensualidad. Si es nuevo, se registra en el mismo formulario. Solo se ofrecen espacios DISPONIBLES del mismo tipo; se preselecciona el primero (o el espacio fijo de la mensualidad). Se genera el tiquete consecutivo `PC-000123` con código de barras Code128 listo para imprimir (formato de impresora térmica de 80 mm).
- **Salida (RF-13 a RF-15):** campo con foco para el lector USB (escribe el código y envía Enter), también se puede digitar (`PC-000123`, `pc000123` o `123`) o escanear con la cámara. Muestra tiempo, tarifa y total; se elige el método de pago y el espacio queda libre.
- **Cobro (RF-14):** siempre en el backend (`apps/operaciones/reglas.py`) con la tarifa vigente: `min(⌈(minutos − gracia) / fracción⌉ × valor, tope_diario)`. En estadías de más de 24 h cada día completo cobra el tope.
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

El panel de Django está en http://localhost:8000/admin/ (entra con el usuario administrador).

## Pruebas del backend

```bash
cd backend
python manage.py test apps
```

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

## Estructura

```
ParkControl/
├── backend/
│   ├── parkcontrol/          # settings y urls
│   └── apps/
│       ├── usuarios/         # Usuario con rol, login JWT, permisos
│       ├── configuracion/    # Parqueadero, TipoVehiculo, Tarifa, Horario + datos iniciales
│       ├── espacios/         # Zona, Espacio
│       ├── vehiculos/        # Cliente, Vehiculo
│       ├── operaciones/      # Tiquete, Pago + reglas de cobro (reglas.py)
│       ├── mensualidades/    # PlanMensual, Mensualidad + vigencias (reglas.py)
│       └── reportes/         # Bitacora + helper para registrar acciones
└── frontend/src/app/
    ├── core/                 # auth.service, interceptor, guards, api.service, errores, modelos
    ├── shared/               # layout (sidebar), stat-card, modal, codigo-barras, escaner
    └── features/             # login, dashboard, espacios, vehiculos, mensualidades,
                              # movimientos/ (lista, entrada, salida, tiquete),
                              # configuracion/ (tarifas, planes, horarios, usuarios, parqueadero)
```

## Próximos avances

- **Avance 4:** dashboard con ingresos, reportes PDF/Excel, bitácora, pruebas y despliegue.
