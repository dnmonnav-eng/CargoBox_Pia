# Matriz de trazabilidad

Relaciona cada necesidad y regla del [BRD](../BRD.md) con el código que la implementa, el endpoint que la expone y las pruebas que la verifican.

| BRD | Regla / necesidad | Dominio | Aplicación | Endpoint | Pruebas |
|---|---|---|---|---|---|
| RN-01, NB-02 | Cada paquete tiene una guía única | `GuiaUnica` | `registrar_envio()` | `POST /paquetes/` (genera `CBX-XXXXXXXX`) | `test_registrar_paquete_exitoso`, `test_dominio_guia_invalida` |
| BRD 7.3 | Máximo 30 kg y 1.5 m por lado | `Paquete.__post_init__`, `LimiteFisicoExcedido` | `registrar_envio()` | `POST /paquetes/` → 422 | `test_limite_fisico_excedido_peso`, `test_limite_fisico_excedido_dimension`, `test_dominio_limites_fisicos`, `test_limites_fisicos_extremos`, `test_dominio_peso_negativo_o_cero` |
| RN-03, RN-04 | Progresión secuencial de estados | `clasificar()` … `iniciar_reparto()`, `InvalidStateTransition` | `avanzar_estado()`, `validar_transicion()` | `/clasificar`, `/despachar-transito`, `/centro-destino`, `/iniciar-reparto` → 409 | `test_dominio_flujo_estados_completo`, `test_dominio_transicion_estado_invalida`, `test_flujo_completo_entrega_con_pod` |
| BRD 7.2, NB-08 | Máximo 2 intentos; luego punto de recolección | `registrar_intento_fallido()`, `LimiteReintentosExcedido` | `registrar_intento_entrega()` | `POST /paquetes/{guia}/intentos-fallidos` → 422 | `test_limite_reintentos_maximo_dos`, `test_dominio_flujo_estados_completo` |
| RN-06, NB-04 | Entrega solo con evidencia POD | `completar_entrega()`, `SinEvidenciaPOD` | `completar_entrega_paquete()` | `POST /paquetes/{guia}/entregar` → 422 | `test_entrega_sin_evidencia_pod_falla`, `test_dominio_completar_entrega_y_pod`, `test_flujo_completo_entrega_con_pod` |
| RN-07, NB-05 | Tratamiento de incidencias | `iniciar_devolucion()`, `declarar_perdida()` | `procesar_incidencia()` | `POST /paquetes/{guia}/incidencias` | `test_incidencia_paquete_danado`, `test_incidencia_perdida_o_rechazo`, `test_dominio_devolucion_y_perdida` |
| NB-08 | Falta prolongada de actualización (24 h en tránsito) | `verificar_tiempo_transito()` | — | — | `test_regla_24_horas_en_transito` |
| RN-05, NB-03 | Cada movimiento genera rastreo | Eventos de dominio, `pull_events()` | — | — | `test_dominio_flujo_estados_completo` (verifica `PaqueteRecibido` con `pull_events()`) |
| NB-07 | Información centralizada y persistente | — | Todos los métodos con `db.commit()` | Todos | `test_repositorio_consultar_inexistente`, `test_casos_limite_y_errores`, `test_persistencia_en_memoria` |
| Casos oficiales FIME | Operaciones, beneficios y transiciones del CSV | — | — | — | `test_caso_prueba_profesor` (parametrizado con `tests/datos/casos_prueba.csv`) |
