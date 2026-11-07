# ADR-004: Persistencia con SQLAlchemy y SQLite

- **Estado:** Aceptada
- **Fecha:** 2026-11-05
- **Equipo:** Equipo 14 — CargoBox

## Contexto

El BRD pide información centralizada y persistente (NB-07). El sistema se ejecuta en las máquinas del equipo, en GitHub Actions y en Docker, y las pruebas deben poder correr sin instalar un servidor de base de datos.

## Decisión

- Usar SQLAlchemy como ORM con el modelo `PaqueteModel` (tabla `paquetes`).
- Usar SQLite como motor: `cargobox.db` en desarrollo y producción de demostración, `sqlite:///:memory:` en pruebas.
- Leer la cadena de conexión desde la variable de entorno `DATABASE_URL`.
- Inyectar la sesión con `Depends(get_db)` para que cada petición abra y cierre la suya.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| PostgreSQL desde el inicio | Requiere un servidor en cada máquina y en CI; se puede adoptar después cambiando `DATABASE_URL` |
| Archivos JSON | Sin transacciones ni consultas; riesgo de corrupción con escrituras simultáneas |
| SQL escrito a mano | Más código repetitivo y sin portabilidad entre motores |

## Consecuencias

- **Positivas:** cero instalación; las pruebas usan una base nueva en memoria en cada ejecución; migrar a PostgreSQL solo requiere cambiar la variable.
- **Negativas:** SQLite no está pensado para muchas escrituras concurrentes. En un contenedor, `cargobox.db` se pierde si no se monta un volumen.
