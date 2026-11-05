import pytest
from src.domain import (
    GuiaUnica,
    Paquete,
    EstadoPaquete,
    LimiteFisicoExcedido,
    LimiteReintentosExcedido,
    SinEvidenciaPOD,
    InvalidStateTransition,
)
from src.application.service import CargoBoxService


def test_registrar_paquete_exitoso():
    """Valida que un paquete con datos correctos se registre en estado RECIBIDO."""
    service = CargoBoxService()
    paquete = service.registrar_envio("GUIA-001", 15.0, 1.0)
    assert paquete.guia.codigo == "GUIA-001"
    assert paquete.estado == EstadoPaquete.RECIBIDO
    assert paquete.peso_kg == 15.0


def test_limite_fisico_excedido_peso():
    """Valida que un paquete que supere los 30 kg rechace el registro de forma estricta."""
    with pytest.raises(LimiteFisicoExcedido):
        Paquete(guia=GuiaUnica("GUIA-002"), peso_kg=35.0, dimension_max_m=1.0)


def test_limite_fisico_excedido_dimension():
    """Valida que un paquete con dimensiones mayores a 1.5 metros sea rechazado."""
    with pytest.raises(LimiteFisicoExcedido):
        Paquete(guia=GuiaUnica("GUIA-003"), peso_kg=10.0, dimension_max_m=1.8)

def test_flujo_completo_entrega_con_pod():
    """Valida el ciclo operativo hasta entregar con éxito aportando evidencia digital (POD)."""
    service = CargoBoxService()
    service.registrar_envio("GUIA-004", 5.0, 0.5)
    service.avanzar_a_clasificado("GUIA-004")
    service.despachar_a_transito("GUIA-004")
    service.llegar_a_centro_destino("GUIA-004")
    service.iniciar_reparto("GUIA-004")
    
    paquete_entregado = service.completar_entrega_paquete("GUIA-004", "Firma digital del receptor")
    assert paquete_entregado.estado == EstadoPaquete.ENTREGADO
    assert paquete_entregado.evidencia_pod == "Firma digital del receptor"


def test_entrega_sin_evidencia_pod_falla():
    """Valida que no se pueda cerrar una entrega si falta la evidencia (RN-06)."""
    service = CargoBoxService()
    service.registrar_envio("GUIA-005", 5.0, 0.5)
    
    paquete = service.obtener_paquete("GUIA-005")
    paquete.estado = EstadoPaquete.EN_REPARTO
    
    with pytest.raises(SinEvidenciaPOD):
        service.completar_entrega_paquete("GUIA-005", "   ")


def test_limite_reintentos_maximo_dos():
    """Valida que al segundo intento fallido el paquete pase a punto de recolección y bloquee más intentos."""
    service = CargoBoxService()
    service.registrar_envio("GUIA-006", 5.0, 0.5)
    
    paquete = service.obtener_paquete("GUIA-006")
    paquete.estado = EstadoPaquete.EN_REPARTO
    
    # Primer intento fallido
    service.registrar_intento_entrega("GUIA-006")
    assert paquete.intentos_entrega == 1
    assert paquete.estado == EstadoPaquete.EN_REPARTO
    
    # Segundo intento fallido (debe transicionar automáticamente a punto de recolección)
    service.registrar_intento_entrega("GUIA-006")
    assert paquete.intentos_entrega == 2
    assert paquete.estado == EstadoPaquete.EN_PUNTO_RECOLECCION
    
    # Un tercer intento ya no está permitido y lanza la excepción de negocio
    with pytest.raises(LimiteReintentosExcedido):
        service.registrar_intento_entrega("GUIA-006")