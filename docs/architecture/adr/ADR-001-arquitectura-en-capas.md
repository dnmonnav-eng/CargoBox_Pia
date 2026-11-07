# ADR-001: Arquitectura en capas (Clean Architecture)

- **Estado:** Aceptada
- **Fecha:** 2026-11-05
- **Equipo:** Equipo 14 — CargoBox

## Contexto

CargoBox necesita un sistema cuyas reglas (límites físicos, reintentos, evidencia POD, incidencias) cambian con la operación, mientras que el framework web y la base de datos deberían poder cambiar sin afectar esas reglas. La rúbrica del PIA también exige separar `src/` en `domain`, `application`, `infrastructure` y `api`.

## Decisión

Organizar el código en cuatro capas con dependencias hacia adentro:

- `src/domain/`: entidades, Value Objects, eventos y excepciones, sin importar FastAPI ni SQLAlchemy.
- `src/application/`: `CargoBoxService` con los casos de uso.
- `src/infrastructure/`: configuración de SQLAlchemy, modelo `PaqueteModel` y repositorio en memoria.
- `src/api/`: endpoints FastAPI que traducen HTTP a llamadas al servicio y excepciones a códigos de estado.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Un solo archivo con toda la lógica en los endpoints | Mezcla reglas con HTTP; imposible probar el dominio sin levantar el servidor |
| MVC clásico (modelo = tabla) | Acopla las reglas al ORM; las invariantes quedarían en el modelo de base de datos |
| Arquitectura hexagonal completa (puertos y adaptadores con interfaces para todo) | Más ceremonia de la que necesita un sistema de este tamaño |

## Consecuencias

- **Positivas:** el dominio se prueba con objetos Python puros; cambiar de base de datos solo afecta `infrastructure/`; la estructura coincide con la rúbrica.
- **Negativas:** hay más archivos y es necesario mapear entre `PaqueteModel` (persistencia) y `Paquete` (dominio). Hoy el servicio trabaja directamente sobre `PaqueteModel`; ver la deuda técnica en [05-decisiones-tecnicas.md](../05-decisiones-tecnicas.md).
