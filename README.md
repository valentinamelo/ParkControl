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

## Endpoints del avance 1

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
│       └── reportes/         # Bitacora
└── frontend/src/app/
    ├── core/                 # auth.service, interceptor, guards, api.service, modelos
    ├── shared/               # layout (sidebar), stat-card
    └── features/             # login, dashboard, movimientos, espacios, vehiculos, configuracion
```

## Próximos avances

- **Avance 2:** CRUD del administrador (espacios en lote, tarifas, horarios, usuarios, vehículos).
- **Avance 3:** entrada, tiquete con código de barras, salida con escáner, cobro y mensualidades.
- **Avance 4:** dashboard con ingresos, reportes PDF/Excel, bitácora, pruebas y despliegue.
