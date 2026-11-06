import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database import Base
from src.infrastructure.models import PaqueteModel
from src.application.service import CargoBoxService
from src.domain import (
    EstadoPaquete,
    LimiteFisicoExcedido,
    LimiteReintentosExcedido,
    SinEvidenciaPOD,
    InvalidStateTransition,
)

# Configuración de base de datos SQLite en memoria para pruebas
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def db_session():
    """Crea y limpia las tablas de la base de datos antes y después de cada prueba."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_registrar_paquete_exitoso(db_session):
    """Valida que un paquete con datos correctos se registre en estado RECIBIDO usando los campos reales de la API."""
    service = CargoBoxService()
    paquete = service.registrar_envio(
        db=db_session,
        codigo_guia="GUIA-001",
        peso_kg=15.0,
        largo_m=1.0,
        ancho_m=0.5,
        alto_m=0.5,
        telefono_cliente="8112345678"
    )
    assert paquete.guia == "GUIA-001"
    assert paquete.estado == EstadoPaquete.RECIBIDO.value
    assert paquete.peso_kg == 15.0


def test_limite_fisico_excedido_peso(db_session):
    """Valida que un paquete que supere los 30 kg rechace el registro de forma estricta."""
    service = CargoBoxService()
    with pytest.raises(LimiteFisicoExcedido):
        service.registrar_envio(
            db=db_session,
            codigo_guia="GUIA-002",
            peso_kg=35.0,  # Excede los 30 kg permitidos
            largo_m=1.0,
            ancho_m=0.5,
            alto_m=0.5,
            telefono_cliente="8112345678"
        )


def test_limite_fisico_excedido_dimension(db_session):
    """Valida que un paquete con dimensiones mayores a 1.5 metros sea rechazado."""
    service = CargoBoxService()
    with pytest.raises(LimiteFisicoExcedido):
        service.registrar_envio(
            db=db_session,
            codigo_guia="GUIA-003",
            peso_kg=10.0,
            largo_m=1.8,  # Excede 1.5 metros por lado
            ancho_m=0.5,
            alto_m=0.5,
            telefono_cliente="8112345678"
        )


def test_flujo_completo_entrega_con_pod(db_session):
    """Valida el ciclo operativo hasta entregar con éxito aportando evidencia digital (POD)."""
    service = CargoBoxService()
    service.registrar_envio(
        db=db_session,
        codigo_guia="GUIA-004",
        peso_kg=5.0,
        largo_m=0.5,
        ancho_m=0.5,
        alto_m=0.5,
        telefono_cliente="8112345678"
    )
    
    # Avanzamos a través de los estados válidos definidos en el servicio
    service.avanzar_estado(db_session, "GUIA-004", "CLASIFICADO")
    service.avanzar_estado(db_session, "GUIA-004", "EN_TRANSITO")
    service.avanzar_estado(db_session, "GUIA-004", "CENTRO_DESTINO")
    service.avanzar_estado(db_session, "GUIA-004", "EN_REPARTO")
    
    paquete_entregado = service.completar_entrega_paquete(db_session, "GUIA-004", "Firma digital del receptor")
    assert paquete_entregado.estado == EstadoPaquete.ENTREGADO.value
    assert paquete_entregado.evidencia_pod == "Firma digital del receptor"


def test_entrega_sin_evidencia_pod_falla(db_session):
    """Valida que no se pueda cerrar una entrega si falta la evidencia (RN-06)."""
    service = CargoBoxService()
    service.registrar_envio(
        db=db_session,
        codigo_guia="GUIA-005",
        peso_kg=5.0,
        largo_m=0.5,
        ancho_m=0.5,
        alto_m=0.5,
        telefono_cliente="8112345678"
    )
    
    paquete = service.obtener_paquete(db_session, "GUIA-005")
    paquete.estado = EstadoPaquete.EN_REPARTO.value
    db_session.commit()
    
    with pytest.raises(SinEvidenciaPOD):
        service.completar_entrega_paquete(db_session, "GUIA-005", "   ")


def test_limite_reintentos_maximo_dos(db_session):
    """Valida que al segundo intento fallido el paquete pase a punto de recolección y bloquee más intentos."""
    service = CargoBoxService()
    service.registrar_envio(
        db=db_session,
        codigo_guia="GUIA-006",
        peso_kg=5.0,
        largo_m=0.5,
        ancho_m=0.5,
        alto_m=0.5,
        telefono_cliente="8112345678"
    )
    
    paquete = service.obtener_paquete(db_session, "GUIA-006")
    paquete.estado = EstadoPaquete.EN_REPARTO.value
    db_session.commit()
    
    # Primer intento fallido
    service.registrar_intento_entrega(db_session, "GUIA-006")
    db_session.refresh(paquete)
    assert paquete.intentos_entrega == 1
    assert paquete.estado == EstadoPaquete.EN_REPARTO.value
    
    # Segundo intento fallido (debe transicionar automáticamente a punto de recolección)
    service.registrar_intento_entrega(db_session, "GUIA-006")
    db_session.refresh(paquete)
    assert paquete.intentos_entrega == 2
    assert paquete.estado == "PUNTO_RECOLECCION"
    
    # Un tercer intento ya no está permitido y lanza la excepción de negocio
    with pytest.raises(LimiteReintentosExcedido):
        service.registrar_intento_entrega(db_session, "GUIA-006")

def test_incidencia_paquete_danado(db_session):
    """Valida la incidencia de paquete dañado y su regreso al centro de destino."""
    service = CargoBoxService()
    service.registrar_envio(
        db=db_session,
        codigo_guia="GUIA-007",
        peso_kg=3.0,
        largo_m=0.3,
        ancho_m=0.3,
        alto_m=0.3,
        telefono_cliente="8112345678"
    )
    service.avanzar_estado(db_session, "GUIA-007", "CLASIFICADO")
    service.avanzar_estado(db_session, "GUIA-007", "EN_TRANSITO")
    service.avanzar_estado(db_session, "GUIA-007", "CENTRO_DESTINO")
    service.avanzar_estado(db_session, "GUIA-007", "EN_REPARTO")

    paquete = service.procesar_incidencia(db_session, "GUIA-007", "paquete_danado")
    assert paquete.estado == "CENTRO_DESTINO"


def test_incidencia_perdida_o_rechazo(db_session):
    """Valida la incidencia de pérdida o rechazo que cancela el envío."""
    service = CargoBoxService()
    service.registrar_envio(
        db=db_session,
        codigo_guia="GUIA-008",
        peso_kg=3.0,
        largo_m=0.3,
        ancho_m=0.3,
        alto_m=0.3,
        telefono_cliente="8112345678"
    )
    service.avanzar_estado(db_session, "GUIA-008", "CLASIFICADO")
    service.avanzar_estado(db_session, "GUIA-008", "EN_TRANSITO")
    service.avanzar_estado(db_session, "GUIA-008", "CENTRO_DESTINO")
    service.avanzar_estado(db_session, "GUIA-008", "EN_REPARTO")

    paquete = service.procesar_incidencia(db_session, "GUIA-008", "rechazo")
    assert paquete.estado == "DEVUELTO_CANCELADO"