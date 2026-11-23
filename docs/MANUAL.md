# Manual de usuario de ParkControl

ParkControl registra la entrada y salida de carros y motos, cobra según la tarifa, imprime el tiquete con código de barras y lleva las mensualidades de los clientes frecuentes.

Hay dos tipos de usuario:

- **Trabajador:** registra entradas y salidas, cobra, vende y renueva mensualidades y consulta vehículos y espacios.
- **Administrador:** hace todo lo anterior y además configura el parqueadero (espacios, tarifas, horarios, planes y usuarios), anula tiquetes y consulta reportes y la bitácora.

---

## 1. Entrar y salir

1. Abre la dirección de ParkControl en el navegador.
2. Escribe tu correo y contraseña y pulsa **Iniciar sesión**.
3. El trabajador entra a **Movimientos**; el administrador, al **Dashboard**.

Para terminar el turno pulsa **Cerrar sesión**, abajo en el menú. Si alguien más va a usar el computador, ciérrala siempre: todo lo que se registre queda a tu nombre.

---

## 2. Registrar la entrada de un vehículo

1. Pulsa **Registrar entrada** (en Movimientos o en el Dashboard).
2. Escribe la **placa**. ParkControl la revisa sola y te avisa:
   - **Vehículo nuevo:** elige si es carro o moto. Marca, modelo y color son opcionales.
   - **Vehículo registrado:** muestra sus datos; no tienes que escribir nada más.
   - **Mensualidad vigente:** el vehículo no paga al salir. Si tiene espacio fijo, ya queda elegido.
   - **Ya está dentro:** no se puede registrar dos veces; te lleva a su salida si lo necesitas.
3. A la derecha aparecen los espacios libres para ese tipo de vehículo. El elegido está en amarillo; toca otro si quieres cambiarlo.
4. Pulsa **Registrar y generar tiquete**.
5. Pulsa **Imprimir** y entrega el tiquete al conductor.

Si el parqueadero está fuera del horario de atención, el trabajador no puede registrar la entrada. El administrador ve el botón **Registrar de todas formas**.

---

## 3. Registrar la salida y cobrar

1. Pulsa **Registrar salida**.
2. **Escanea el código de barras** del tiquete con el lector. No hace falta pulsar nada más: el lector escribe el código y lo busca solo.
   - Sin lector: escribe el código (`PC-000123` o solo `123`) y pulsa **Buscar**.
   - Con la cámara: pulsa el botón de la cámara y apunta al código de barras.
3. Revisa el tiempo y el **total a pagar**.
4. Elige el método de pago: **Efectivo**, **Tarjeta** o **Transferencia**.
5. Pulsa **Cobrar … y dar salida**. El espacio queda libre y la pantalla queda lista para el siguiente vehículo.

Si el vehículo tiene mensualidad vigente, el total es $0 y solo pulsas **Dar salida**.

### Tiquete perdido

En lugar del código, escribe la **placa** y pulsa **Buscar**. ParkControl marca *Tiquete perdido* y suma la multa al cobro. Confirma el pago como siempre.

### ¿Cuánto se cobra?

Se cobra cada hora (o fracción, según la tarifa) empezada. Por ejemplo, con $4.000 la hora, 2 horas y 45 minutos se cobran como 3 horas: **$12.000**. Si la tarifa tiene minutos de gracia y el vehículo sale antes de que terminen, no paga. El total de un día nunca pasa del tope diario.

---

## 4. Ver qué hay dentro

- **Movimientos:** lista de los vehículos dentro con el tiempo que llevan y lo que pagarían si salieran ahora, y las últimas salidas. Desde cada fila puedes ir a **Dar salida** o abrir el tiquete para reimprimirlo.
- **Espacios:** el mapa del parqueadero. Negro es ocupado, blanco disponible y gris punteado inactivo. Toca un espacio para ver qué vehículo lo ocupa y desde qué hora.

Las dos pantallas se actualizan solas cada 15 segundos.

---

## 5. Mensualidades

### Vender una mensualidad

1. Ve a **Mensualidades** y pulsa **Vender mensualidad**.
2. Escribe el **documento** del cliente. Si ya es cliente, sus datos aparecen solos; si no, escribe su nombre (teléfono y correo son opcionales).
3. Escribe la **placa**, elige el **plan** y la fecha de inicio.
4. Si el cliente tendrá un puesto reservado, elige el **espacio fijo**. Ese espacio no se le ofrecerá a otros vehículos.
5. Elige el método de pago y pulsa **Cobrar y vender**.

### Renovar

Busca la mensualidad (por placa, cliente o documento), pulsa **Renovar**, elige el método de pago y confirma. La renovación empieza al día siguiente de que venza la actual; si ya venció, empieza hoy.

---

## 6. Vehículos

En **Vehículos** puedes buscar por placa, registrar un vehículo, corregir sus datos o eliminarlo. Un vehículo que ya tiene tiquetes o mensualidades no se puede eliminar, porque son parte del historial.

---

## 7. Solo para el administrador

### Dashboard

Muestra la ocupación en tiempo real (en total y por tipo de vehículo), lo que entró, salió y se recaudó hoy, los ingresos de la semana y cuántas mensualidades vencen pronto. El trabajador también tiene dashboard, pero con los datos de su turno.

### Configuración

- **Tarifas:** pulsa **Cambiar** en la tarifa de un tipo de vehículo. Por hora o por fracción, con minutos de gracia y tope diario. Al cambiarla se crea una tarifa nueva y la anterior queda en el **historial**: lo que ya se cobró no cambia. Aquí también se agregan tipos de vehículo (por ejemplo, bicicleta).
- **Planes mensuales:** nombre, tipo de vehículo, días y valor. Un plan que ya se vendió no se borra: se desactiva para que no se venda más.
- **Horarios:** marca los días que se abre y la hora de apertura y cierre. Pulsa **Guardar horario**.
- **Usuarios:** crea trabajadores con su correo y una contraseña de al menos 8 caracteres. **Desactivar** impide que el usuario entre, sin borrar lo que registró.
- **Parqueadero:** nombre, NIT, dirección y teléfono (salen en el tiquete) y el valor de la **multa por tiquete perdido**.

### Espacios

En **Espacios**, el botón **Agregar espacios** crea varios de una vez: escribe la zona (por ejemplo `B`) y la cantidad. Si la zona ya existe, la numeración continúa (B-06, B-07…); si es nueva, elige si es para carros o motos.

Toca un espacio para **desactivarlo** (deja de ofrecerse) o **eliminarlo**. Un espacio ocupado no se puede tocar. En la tabla **Zonas** se cambia el tipo de vehículo de una zona completa.

### Anular un tiquete

Abre el tiquete (desde Movimientos, tocando su código) y pulsa **Anular**. Escribe el motivo; es obligatorio.

- Si el vehículo estaba dentro, el espacio queda libre (por ejemplo, cuando se registró una placa equivocada).
- Si el tiquete ya estaba cobrado, ese cobro deja de contar en los ingresos (así se corrige un cobro mal hecho).

### Reportes

- **Ingresos:** elige el rango (o usa *Hoy*, *Últimos 7 días*, *Este mes*, *Mes anterior*) y, si quieres, filtra por tipo de vehículo, método de pago, trabajador o concepto. Pulsa **Consultar**. Los botones **PDF** y **Excel** descargan el mismo reporte.
- **Bitácora:** quién hizo cada entrada, salida, venta, anulación y cambio de configuración, y cuándo. Filtra por fecha, usuario, acción o un texto (por ejemplo, una placa o un código de tiquete).

---

## 8. Problemas frecuentes

| Qué pasa | Qué hacer |
| --- | --- |
| "No hay conexión con el servidor" | Revisa el internet. Si sigue, avisa al administrador. |
| El lector no escribe nada | Haz clic en el campo del código y vuelve a escanear. Si no, escribe el código a mano. |
| La cámara no abre | Acepta el permiso de cámara del navegador. Si no, usa el lector o escribe el código. |
| "No hay espacios disponibles" | Todos los espacios de ese tipo están ocupados o inactivos. |
| "No hay tarifa vigente" | El administrador debe crear la tarifa de ese tipo de vehículo en Configuración → Tarifas. |
| La sesión se cerró sola | La sesión dura 8 horas. Vuelve a iniciar sesión. |
