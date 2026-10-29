# Taller Mecánico API

API REST para gestionar un taller mecánico: clientes, vehículos, inventario de repuestos, órdenes de servicio y facturación.
Proyecto Programado #1 de Desarrollo de Software IV, UCR Sede del Pacífico.

**Tecnologías:** Python, Django 5.2, Django REST Framework, MySQL y autenticación por token.
No incluye frontend: se prueba con Postman y con las pruebas automatizadas.

La documentación técnica (diagrama ER, relaciones, reglas de negocio, matriz de permisos y catálogo de endpoints) está en [`docs/DOCUMENTACION_TECNICA.md`](docs/DOCUMENTACION_TECNICA.md).

---

## Contenido del proyecto

```
taller-mecanico/
├── taller_backend/        Configuración principal (settings, urls)
│   ├── utilidades.py      Funciones para revisar el rol del usuario
│   └── pruebas_base.py    Preparación común de las pruebas automatizadas
├── clientes/              Cliente  (+ comando cargar_datos)
├── vehiculos/             Vehiculo (+ historial del vehículo)
├── repuestos/             Repuesto (inventario)
├── ordenes/               OrdenServicio y DetalleOrden
├── facturacion/           Factura  (+ reportes)
├── database/              Script SQL para crear la base y el usuario
├── postman/               Colección y entorno de Postman
├── docs/                  Documentación técnica
├── .env.example           Variables de entorno de ejemplo (sin secretos)
└── requirements.txt       Dependencias con versiones
```

Cada aplicación tiene la misma organización: `models.py`, `serializers.py`, `views.py` (vistas con funciones y `@api_view`), `urls.py`, `admin.py`, `tests.py` y sus migraciones.

---

## Requisitos

- Python 3.12, 3.13 o 3.14 (se usa `mysqlclient==2.3.0`).
- MySQL Server 8 y MySQL Workbench (o la consola de MySQL).
- Git y Postman.

---

## Instalación paso a paso

Los comandos se muestran para **Git Bash** y para **CMD/PowerShell de Windows** cuando son distintos.
Todos se ejecutan dentro de la carpeta del proyecto.

### 1. Crear y activar el entorno virtual

```bash
python -m venv .venv
```

Activar:

| Terminal | Comando |
|---|---|
| Git Bash | `source .venv/Scripts/activate` |
| CMD | `.venv\Scripts\activate` |
| PowerShell | `.venv\Scripts\Activate.ps1` |

Al activarse, la terminal muestra `(.venv)` al inicio de la línea.

Si PowerShell no permite ejecutar el script de activación, ejecute una sola vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y vuelva a intentarlo.

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar el archivo .env

Copie el archivo de ejemplo:

| Terminal | Comando |
|---|---|
| Git Bash | `cp .env.example .env` |
| CMD / PowerShell | `copy .env.example .env` |

Abra `.env` y complete:
- `SECRET_KEY`: cualquier texto largo y aleatorio.
- `DB_PASSWORD`: la contraseña que usará en el paso 4.

El archivo `.env` no se sube a GitHub.

### 4. Preparar MySQL

1. Abra `database/taller_mecanico_db.sql` en MySQL Workbench.
2. Cambie `CAMBIAR_POR_CONTRASENA_LOCAL` por la misma contraseña que puso en `DB_PASSWORD`.
3. Ejecute el script completo con un usuario administrador (root).

El script crea la base `taller_mecanico_db`, el usuario `taller_user` y le da permiso sobre la base de pruebas `test_taller_mecanico_db`, que Django necesita para ejecutar las pruebas automatizadas.

Desde la consola también se puede ejecutar así (pide la contraseña de root):

```bash
mysql -u root -p < database/taller_mecanico_db.sql
```

### 5. Ejecutar las migraciones

```bash
python manage.py migrate
```

### 6. Crear roles, usuarios de prueba y datos ficticios

```bash
python manage.py cargar_datos
```

Crea los grupos **Administrador**, **Recepcionista** y **Mecanico**, estos usuarios de prueba y algunos datos ficticios (3 clientes, 4 vehículos y 5 repuestos). Las órdenes y facturas se crean al probar con Postman:

| Usuario | Rol | Contraseña |
|---|---|---|
| `admin_taller` | Administrador | `Taller2026*` |
| `recepcion` | Recepcionista | `Taller2026*` |
| `mecanico1` | Mecánico | `Taller2026*` |
| `mecanico2` | Mecánico | `Taller2026*` |

Son contraseñas de prueba, solo para desarrollo. El comando se puede ejecutar varias veces sin duplicar datos.

**Opcional, superusuario para el panel `/admin/`:**

```bash
python manage.py createsuperuser
```

El superusuario se trata como administrador en la API. Para crear otros usuarios desde `/admin/`, agréguelos al grupo correspondiente (Administrador, Recepcionista o Mecanico).

### 7. Iniciar el servidor

```bash
python manage.py runserver
```

La API queda en `http://127.0.0.1:8000/api/`.

---

## Autenticación

1. Pida un token con `POST /api/token/` y el cuerpo:
   ```json
   { "username": "recepcion", "password": "Taller2026*" }
   ```
2. Envíe el token en cada solicitud con el encabezado:
   ```
   Authorization: Token <token recibido>
   ```

Sin token la API responde **401**. Con un token cuyo rol no tiene permiso responde **403**.

---

## Pruebas automatizadas

```bash
python manage.py test
```

Hay **34 pruebas** repartidas en las cinco aplicaciones (`clientes/tests.py`, `vehiculos/tests.py`, `repuestos/tests.py`, `ordenes/tests.py`, `facturacion/tests.py`). Cubren CRUD, reglas de negocio, permisos (401 y 403), filtros, ordenamiento y paginación.

Para ver el nombre de cada prueba:

```bash
python manage.py test -v 2
```

Django crea y borra automáticamente la base temporal `test_taller_mecanico_db`. Si aparece un error de acceso denegado, revise que se ejecutó el `GRANT` sobre esa base del paso 4.

---

## Postman

1. En Postman: **Import** → seleccione los dos archivos de la carpeta `postman/`:
   - `Taller-Mecanico.postman_collection.json` (40 solicitudes documentadas)
   - `Taller-Mecanico.postman_environment.json` (variables `base_url` y `clave_prueba`)
2. Seleccione el entorno **Taller Mecánico - Local** (arriba a la derecha).
3. Con el servidor encendido y los datos cargados, ejecute las carpetas en orden o toda la colección con **Run collection**.

Las solicitudes de login guardan los tokens automáticamente, y las de creación guardan los ids (`cliente_id`, `vehiculo_id`, `orden_id`, etc.) que usan las siguientes. Cada solicitud tiene descrita su respuesta esperada y una prueba que verifica el código HTTP.

---

## Recorrido completo del taller

| Paso | Solicitud | Rol |
|---|---|---|
| 1. Registrar cliente | `POST /api/clientes/` | Recepcionista |
| 2. Registrar vehículo | `POST /api/vehiculos/` | Recepcionista |
| 3. Abrir orden | `POST /api/ordenes/` | Recepcionista |
| 4. Iniciar reparación | `POST /api/ordenes/{id}/cambiar-estado/` con `{"estado": "EN_REPARACION"}` | Mecánico asignado |
| 5. Registrar repuestos | `POST /api/ordenes/{id}/detalles/` con `{"repuesto": 1, "cantidad": 2}` | Mecánico asignado |
| 6. Finalizar | `POST /api/ordenes/{id}/cambiar-estado/` con `{"estado": "FINALIZADA", "mano_obra": "18000"}` | Mecánico asignado |
| 7. Facturar | `POST /api/facturas/` con `{"orden": id}` | Recepcionista |

La colección de Postman sigue exactamente este recorrido.

---

## Limitaciones conocidas

- La facturación es interna del taller; no se integra con la facturación electrónica de Hacienda.
- No incluye frontend, pagos en línea ni agenda de citas.
- Cada usuario tiene un solo rol (el primer grupo asignado).
- `DEBUG=True` es para desarrollo. Para una demostración sin páginas de depuración, use `DEBUG=False` en el `.env`.
