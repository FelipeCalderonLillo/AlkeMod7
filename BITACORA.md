# Bitácora de decisiones - ProyectoModulo7

## Estado del documento

Bitácora de decisiones del desarrollo académico de ProyectoModulo7.

El objetivo es registrar decisiones ya tomadas para evitar redefinirlas durante la implementación.

---

## 1. Alcance

El proyecto es una aplicación académica de nivel avanzado desarrollada con Django.

Se prioriza completar los requerimientos funcionales del proyecto sin introducir complejidad que no sea necesaria para el alcance académico.

---

## 2. Framework y base de datos

- Framework: Django.
- Base de datos: MySQL desde el desarrollo.
- Base de datos del proyecto: `bd_alke_mod7`.
- Configuración sensible mediante variables de entorno.
- `.env` fuera del repositorio.
- `.env.example` como referencia.

---

## 3. Usuarios y autenticación

Se utiliza el modelo `User` de Django para autenticación y autorización.

`Perfil` mantiene información adicional mediante relación uno a uno.

El registro requiere:

- username;
- contraseña;
- confirmación de contraseña;
- nombre;
- apellido;
- email;
- fecha de nacimiento.

El usuario debe tener al menos 18 años.

`trabajo` y `biografia` no forman parte del registro inicial y se gestionan desde el perfil.

---

## 4. Estado de usuario y cuenta

Se decidió utilizar `User.is_active` como indicador de estado.

No se agrega un campo `activa` a `Cuenta`.

Motivo:

- el estado de acceso y operación ya está representado por `User.is_active`;
- evita duplicar información;
- permite mantener una implementación simple acorde al alcance académico.

La desactivación es lógica y conserva los datos.

Existe `ActiveUserMiddleware` para cerrar sesiones existentes cuando un usuario es desactivado.

Los usuarios con permisos administrativos no pueden ser desactivados mientras mantengan dichos permisos.

---

## 5. Cuenta

Cada usuario posee una única cuenta.

Decisiones:

- saldo inicial: $500.000;
- saldo mínimo: $0;
- no existe sobregiro;
- no existen retiros;
- no se elimina la cuenta;
- el número de cuenta lo genera el sistema;
- formato `xxx-xxxx-xxxx`.

---

## 6. Transacciones

Se definieron tres tipos:

- depósito;
- transferencia interna;
- transferencia externa.

Las transacciones son históricas e inmutables.

No se permite al usuario editar ni eliminar transacciones.

Los datos de origen y destino se conservan como snapshot histórico.

---

## 7. Transferencias

Las transferencias tienen una etapa de confirmación.

Se utiliza `TransferenciaPendiente` antes de crear la transacción definitiva.

El token es generado automáticamente y tiene una duración de cinco minutos.

Monto mínimo:

```text
$1.000
```

No se utilizan montos con decimales en la interfaz de operaciones.

Las operaciones financieras se ejecutan de forma atómica.

No se permite transferencia interna hacia la propia cuenta.

---

## 8. Contactos

Los contactos pertenecen exclusivamente al usuario que los crea.

El número de cuenta del contacto es generado por el sistema.

El usuario no introduce manualmente dicho número.

Los contactos son inmutables y no eliminables para el usuario.

Bancos definidos:

- Gringotts Wizarding Bank;
- Goliath National Bank;
- Bank's Bank.

---

## 9. Categorías de interés

Categorías definidas:

- Ahorro;
- Inversiones;
- Emprendimiento;
- Viajes.

La relación usuario-categoría es `ManyToMany`.

El usuario gestiona sus propias suscripciones.

El administrador puede crear, editar y eliminar categorías desde Django Admin.

---

## 10. Administración

El administrador puede:

- crear usuarios;
- activar/desactivar usuarios normales;
- administrar categorías;
- consultar información;
- realizar consultas de contraloría.

La contraloría incluye confirmación previa e informa sobre el carácter privado de la información consultada.

Las transacciones son de solo lectura desde Admin.

---

## 11. Historial y reportes

El historial muestra las operaciones asociadas a la cuenta del usuario.

Los reportes utilizan Django ORM.

El reporte predeterminado utiliza los últimos 30 días.

---

## 12. Arquitectura

Se mantiene separación entre:

```text
Templates
    ↓
Views
    ↓
Forms + Services
    ↓
Models / ORM
```

Las reglas de negocio se mantienen principalmente en services.

Las validaciones de entrada corresponden a forms cuando corresponde.

---

## 13. Pruebas

Las pruebas se agrupan en:

- modelos;
- formularios;
- servicios;
- vistas.

Durante el desarrollo se corrigieron las pruebas según las decisiones definitivas del proyecto.

Estado informado antes de la etapa visual:

```text
197 tests OK
```

La suite completa se volverá a ejecutar en la validación final.

---

## 14. Diagrama relacional

El archivo `diagrama.puml` fue actualizado para representar los modelos actuales.

Se incluyeron:

- User;
- Perfil;
- Cuenta;
- Contacto;
- CategoriaInteres;
- TransferenciaPendiente;
- Transaccion.

La relación entre estado del usuario y operación de cuenta se representa mediante `User.is_active`.

---

## 15. Decisiones de implementación crítica

Durante la etapa final de implementación se estableció:

1. Priorizar requerimientos funcionales sobre mejoras no solicitadas.
2. No duplicar funcionalidades ya implementadas.
3. No crear campos o estructuras redundantes.
4. No introducir complejidad de producción en un proyecto académico.
5. Completar primero la implementación funcional.
6. Realizar los tests completos después de terminar la implementación.
7. Consolidar la navegación junto con el UI final.
8. Actualizar el `.puml` antes de cerrar la documentación.
9. Crear un commit/push del estado funcional antes de comenzar el trabajo visual.
10. Crear un branch separado para la implementación del UI final.

---
