# ADR-006: Integración continua con GitHub Actions y contenedores Docker

- **Estado:** Aceptada
- **Fecha:** 2026-11-05
- **Equipo:** Equipo 14 — CargoBox

## Contexto

El PIA exige pruebas automatizadas con cobertura de al menos 80%, un pipeline activo y una solución contenerizada que cualquiera pueda levantar igual. Varias personas suben cambios al mismo repositorio.

## Decisión

- Workflow `.github/workflows/ci.yaml` que se ejecuta en cada `push` y `pull_request` a `main`: instala dependencias con Python 3.10 y corre `pytest` con `--cov-fail-under=80`.
- `Dockerfile` basado en `python:3.10-slim` que instala `requirements.txt` y arranca `uvicorn src.api.api:app` en el puerto 8000.
- `docker-compose.yml` para levantar el servicio `cargobox-api` con `APP_ENV=production`.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Correr las pruebas solo en local | Nadie garantiza que se corran antes de cada push |
| Jenkins o GitLab CI | El repositorio ya vive en GitHub; Actions no requiere servidor propio |
| Desplegar sin contenedor | El entorno cambiaría entre máquinas (versiones de Python, dependencias) |

## Consecuencias

- **Positivas:** cada push muestra en verde o rojo si se rompió algo; el historial de Actions sirve como evidencia; la imagen usa la misma versión de Python que el CI.
- **Negativas:** hoy el umbral de cobertura del CI se mide sobre `src/application` y Compose levanta solo la API. Ambos puntos están en la deuda técnica.
