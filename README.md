# Enlace al repositorio

https://github.com/FelipeCalderonLillo/AlkeMod7.git

# ProyectoModulo7

Aplicación web académica desarrollada con Django para la gestión de usuarios, cuentas, depósitos, transferencias, contactos, historial de movimientos, reportes y categorías de interés.

El proyecto utiliza Django como framework web y MySQL como sistema gestor de base de datos desde el entorno de desarrollo.

> **Estado:** implementación funcional completada. Pendiente de consolidación visual, documentación final y validación final antes de la entrega.

---

## 1. Tecnologías

- Python 3.14.6
- Django 6.1.1
- MySQL
- mysqlclient
- python-dotenv
- HTML
- CSS
- JavaScript
- Django ORM
- Django Authentication
- Django Admin

---

## 2. Base de datos

La aplicación utiliza MySQL desde el desarrollo.

Base de datos:

```text
bd_alke_mod7
```

La configuración utiliza variables de entorno:

```text
DB_NAME
DB_USER
DB_PASSWORD
DB_HOST
DB_PORT
```

Las credenciales y otros datos sensibles se mantienen fuera del código mediante `.env`.

El archivo `.env` no forma parte del repositorio. Se mantiene un `.env.example` como referencia para la configuración.

El proyecto utiliza un usuario específico de MySQL para la aplicación, evitando utilizar directamente una cuenta administrativa del servidor.

---

## 3. Estructura general

La estructura principal del proyecto es:

```text
ProyectoModulo7/
├── config/
├── core/
├── templates/
├── static/
├── manage.py
├── .env
├── .env.example
├── .gitignore
└── diagrama.puml
```

La aplicación `core` contiene la lógica principal del proyecto.

---

## 4. Arquitectura

La aplicación sigue una separación de responsabilidades:

```text
Navegador
    ↓
Templates
    ↓
Views
    ↓
Forms + Services
    ↓
Models / ORM
    ↓
MySQL
```

Las vistas se implementan principalmente mediante Class-Based Views (CBV).

Los formularios realizan validaciones de entrada y los servicios concentran las reglas de negocio cuando corresponde.

---

## 5. Autenticación y registro

El proyecto utiliza el sistema de autenticación nativo de Django.

El modelo `User` se utiliza para:

- autenticación;
- nombre de usuario;
- contraseña;
- nombre;
- apellido;
- correo electrónico;
- estado de activación;
- permisos administrativos.

El modelo `Perfil` mantiene información adicional y tiene una relación uno a uno con `User`.

El registro contempla:

- usuario;
- contraseña;
- confirmación de contraseña;
- nombre;
- apellido;
- email;
- fecha de nacimiento.

El usuario debe tener al menos 18 años.

Los campos `trabajo` y `biografia` no forman parte del registro inicial. Se gestionan posteriormente desde el perfil.

---

## 6. Activación y desactivación de usuarios

El estado de activación utiliza el campo estándar:

```text
User.is_active
```

No existe un campo adicional de estado para la cuenta.

La desactivación es lógica y no elimina físicamente los datos.

Existe un middleware propio:

```text
core/middleware.py
```

`ActiveUserMiddleware` detecta una sesión existente perteneciente a un usuario que fue desactivado posteriormente, cierra la sesión y redirige al login mostrando un mensaje.

El flujo es:

```text
Usuario inicia sesión
        ↓
Administrador desactiva la cuenta
        ↓
Usuario realiza una nueva petición
        ↓
Middleware detecta is_active=False
        ↓
Se cierra la sesión
        ↓
Se informa al usuario
        ↓
Redirección al login
```

Las páginas públicas continúan siendo accesibles después del cierre de sesión.

Los usuarios que poseen permisos administrativos no pueden ser desactivados mientras mantengan dichos privilegios. Para desactivar una cuenta administrativa primero deben retirarse sus permisos administrativos.

---

## 7. Cuenta

Cada usuario posee una única cuenta digital.

Características:

- moneda: CLP;
- saldo inicial: $500.000;
- saldo mínimo permitido: $0;
- no existe sobregiro;
- no existen retiros;
- la cuenta no se elimina;
- el número de cuenta es generado por el sistema;
- formato:

```text
xxx-xxxx-xxxx
```

El número de cuenta es único y se utiliza como identificador visible, no como identificador técnico de la cuenta.

El estado operativo de la cuenta depende de `User.is_active`; no existe un campo `Cuenta.activa` adicional.

---

## 8. Operaciones financieras

Los tipos de transacción son:

- Depósito
- Transferencia interna
- Transferencia externa

Las transacciones son históricas e inmutables después de su creación.

No existe edición ni eliminación de transacciones por parte del usuario.

Las operaciones financieras se ejecutan mediante servicios y las operaciones que modifican saldo utilizan transacciones atómicas.

### Depósitos

El depósito es simulado dentro del alcance académico del proyecto.

Reglas principales:

- monto mínimo: $1.000;
- no se utilizan decimales en la interfaz de operaciones;
- el saldo no puede quedar negativo.

### Transferencias internas

Permiten transferir fondos a otra cuenta registrada en la aplicación.

Reglas principales:

- no se permite transferir a la propia cuenta;
- el destinatario debe pertenecer a un usuario activo;
- no requiere contacto;
- monto mínimo: $1.000;
- no se permiten montos con decimales;
- el saldo no puede quedar negativo;
- se permite transferir el saldo completo;
- la operación es atómica.

### Transferencias externas

Utilizan un contacto previamente registrado por el usuario.

Reglas principales:

- el contacto pertenece exclusivamente al usuario que lo creó;
- el contacto es inmutable y no eliminable por el usuario;
- monto mínimo: $1.000;
- no se permiten montos con decimales;
- la operación es atómica.

Las transferencias utilizan una etapa de confirmación antes de ejecutar definitivamente la operación.

`TransferenciaPendiente` utiliza un token único y una fecha de expiración. La duración definida para el token es de cinco minutos.

---

## 9. Contactos

Los contactos pertenecen exclusivamente al usuario que los creó.

Contienen:

- nombre;
- apellido;
- banco;
- número de cuenta.

Bancos disponibles:

- Gringotts Wizarding Bank
- Goliath National Bank
- Bank's Bank

El número de cuenta del contacto es generado por el sistema y no es ingresado manualmente por el usuario.

Los contactos no pueden ser modificados ni eliminados por el usuario.

---

## 10. Categorías de interés

Las categorías definidas son:

- Ahorro
- Inversiones
- Emprendimiento
- Viajes

La relación entre usuarios y categorías utiliza `ManyToMany`.

Las categorías son informativas y no representan categorías de transacciones financieras.

El usuario puede gestionar sus propias suscripciones a categorías.

El administrador puede crear, editar y eliminar las categorías desde Django Admin.

---

## 11. Historial y reportes

El historial permite consultar las operaciones realizadas sobre la cuenta.

Las transacciones conservan snapshots de los datos de origen y destino para preservar la información histórica aunque posteriormente cambien datos del usuario.

Los reportes utilizan consultas mediante Django ORM.

El reporte predeterminado considera los últimos 30 días.

---

## 12. Administración

El proyecto utiliza Django Admin.

El administrador puede:

- crear usuarios;
- activar o desactivar usuarios normales;
- administrar categorías de interés;
- consultar información de usuarios;
- consultar historiales de cuentas mediante el procedimiento de contraloría.

Los datos personales del usuario se mantienen fuera de la modificación administrativa ordinaria.

Las transacciones son de solo lectura desde el administrador.

La consulta de historial mediante contraloría incluye una pantalla previa de confirmación e informa que la información es privada y que la consulta debe realizarse únicamente con fines de auditoría.

Las cuentas no pueden ser creadas, modificadas ni eliminadas desde el administrador.

---

## 13. Servicios

La lógica de negocio se organiza en:

```text
core/services/
├── registration.py
├── deposits.py
├── transfers.py
├── contacts.py
├── interests.py
├── profile.py
├── number_generator.py
├── exceptions.py
└── reports.py
```

Esta separación permite mantener las reglas de negocio fuera de las vistas cuando corresponde.

---

## 14. Middleware

El middleware personalizado se encuentra en:

```text
core/middleware.py
```

Actualmente se utiliza:

```text
ActiveUserMiddleware
```

Su función es controlar las sesiones existentes de usuarios que fueron desactivados.

Se ejecuta después de `AuthenticationMiddleware`, por lo que puede comprobar el usuario autenticado asociado a la sesión.

---

## 15. Pruebas

Las pruebas automatizadas se encuentran en:

```text
core/tests/
├── test_models.py
├── test_forms.py
├── test_services.py
└── test_views.py
```

Durante la implementación se fueron agregando y corrigiendo pruebas junto con las funcionalidades.

El último estado informado de la suite es:

```text
197 tests OK
```

La suite completa será ejecutada nuevamente durante la validación final después de la consolidación visual y documental.

---

## 16. Diagrama de base de datos

El proyecto mantiene el modelo relacional en:

```text
diagrama.puml
```

El diagrama fue actualizado para representar el estado actual de los modelos, incluyendo:

- `User`;
- `Perfil`;
- `Cuenta`;
- `Contacto`;
- `CategoriaInteres`;
- `TransferenciaPendiente`;
- `Transaccion`.

La relación de estado de la cuenta utiliza `User.is_active` y no un campo adicional en `Cuenta`.

---

## 17. Alcance académico

El proyecto corresponde a una aplicación académica de nivel avanzado.

El alcance prioriza:

- Django;
- autenticación y autorización;
- modelos y relaciones;
- migraciones;
- Django ORM;
- formularios;
- Class-Based Views;
- servicios;
- transacciones atómicas;
- validaciones;
- Django Admin;
- pruebas automatizadas;
- documentación.

No se agregan mecanismos de infraestructura o seguridad avanzada que no sean necesarios para los requerimientos académicos definidos.

Las posibles mejoras fuera del alcance quedan documentadas como mejoras futuras cuando corresponda.

---

## 18. Estado actual

La implementación funcional principal se encuentra completada.

Se encuentran implementadas:

- configuración Django;
- conexión MySQL;
- variables de entorno;
- autenticación;
- registro;
- confirmación de contraseña;
- perfiles;
- cuentas;
- generación de números de cuenta;
- contactos;
- categorías de interés;
- depósitos;
- transferencias internas;
- transferencias externas;
- confirmación de transferencias;
- transferencias pendientes;
- historial;
- reportes;
- administración mediante Django Admin;
- procedimiento de contraloría;
- activación/desactivación lógica de usuarios;
- middleware para sesiones de usuarios desactivados;
- pruebas automatizadas.

---

## 19. Archivos de referencia

- `README.md`: documentación general del proyecto.
- `diagrama.puml`: modelo relacional.
- `.env.example`: referencia de variables de entorno.
- `.gitignore`: archivos excluidos del control de versiones.
