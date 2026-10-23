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
│       ├── operaciones/      # Tiquete, Pago
│       ├── mensualidades/    # PlanMensual, Mensualidad
│       └── reportes/         # Bitacora + helper para registrar acciones
└── frontend/src/app/
    ├── core/                 # auth.service, interceptor, guards, api.service, errores, modelos
    ├── shared/               # layout (sidebar), stat-card, modal
    └── features/             # login, dashboard, movimientos, espacios, vehiculos,
                              # configuracion/ (tarifas, horarios, usuarios, parqueadero)
```

## Próximos avances

- **Avance 3:** entrada, tiquete con código de barras, salida con escáner, cobro y mensualidades.
- **Avance 4:** dashboard con ingresos, reportes PDF/Excel, bitácora, pruebas y despliegue.
