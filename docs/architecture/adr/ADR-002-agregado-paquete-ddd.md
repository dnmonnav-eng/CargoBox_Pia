# ADR-002: `Paquete` como raíz del agregado con State Machine

- **Estado:** Aceptada
- **Fecha:** 2026-11-05
- **Equipo:** Equipo 14 — CargoBox

## Contexto

El negocio rastrea paquetes. Todos los cambios relevantes (estado, intentos, evidencia) pertenecen a un paquete, y el BRD exige una progresión secuencial de estados (RN-03) con un catálogo cerrado (RN-04). Sin un punto de control único, cualquier parte del código podría poner un paquete en `ENTREGADO` sin pasar por reparto ni tener POD.

## Decisión

Modelar `Paquete` como raíz del agregado en `src/domain/__init__.py`:

- El estado solo cambia por métodos con precondición explícita (`clasificar`, `despachar_a_transito`, `llegar_a_centro_destino`, `iniciar_reparto`, `registrar_intento_fallido`, `completar_entrega`, `iniciar_devolucion`, `declarar_perdida`).
- Una transición inválida lanza `InvalidStateTransition`.
- `GuiaUnica` es un Value Object inmutable (`frozen=True`).
- Los hechos relevantes se registran como eventos de dominio y se extraen con `pull_events()`.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Estado como texto libre que cualquier capa modifica | No garantiza la secuencia; permite estados inexistentes |
| Librería externa de máquinas de estado (`transitions`) | Agrega una dependencia para nueve estados que se expresan bien con métodos |
| Tabla de transiciones en base de datos | Las reglas quedarían fuera del código y serían difíciles de probar |

## Consecuencias

- **Positivas:** las reglas se leen en el mismo lugar donde se aplican; las pruebas del dominio no necesitan base de datos; los nombres de los métodos coinciden con el lenguaje del negocio.
- **Negativas:** agregar un estado implica agregar un método y su prueba. La capa de aplicación también valida transiciones con `validar_transicion()`, lo que hoy duplica parte de la lógica.
