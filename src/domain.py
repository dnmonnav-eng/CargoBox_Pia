from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List


# --- EXCEPCIONES DE DOMINIO ---
class CargoBoxDomainError(Exception):
    """Excepción base para errores de negocio en CargoBox."""
    pass

class LimiteFisicoExcedido(CargoBoxDomainError):
    """Lanzada cuando el paquete supera los 30 kg o 1.5 m de dimensión[cite: 10, 48]."""
    pass

class LimiteReintentosExcedido(CargoBoxDomainError):
    """Lanzada al intentar superar el límite máximo de 2 reintentos de entrega[cite: 5, 10, 48]."""
    pass

class SinEvidenciaPOD(CargoBoxDomainError):
    """Lanzada cuando falta la evidencia digital de recepción (POD) (RN-06)[cite: 5, 10, 48]."""
    pass

class InvalidStateTransition(CargoBoxDomainError):
    """Lanzada cuando se intenta una transición de estado no permitida por el flujo operativo."""
    pass


# --- ENUMERACIONES DE ESTADO (Basadas en el Reporte de Arquitectura) ---
class EstadoPaquete(Enum):
    RECIBIDO = "RECIBIDO"
    CLASIFICADO = "CLASIFICADO"
    EN_TRANSITO = "EN_TRANSITO"
    CENTRO_DESTINO = "CENTRO_DESTINO"
    EN_REPARTO = "EN_REPARTO"
    ENTREGADO = "ENTREGADO"
    EN_PUNTO_RECOLECCION = "EN_PUNTO_RECOLECCION"
    DEVUELTO = "DEVUELTO"
    PERDIDO = "PERDIDO"


# --- VALUE OBJECTS INMUTABLES ---
@dataclass(frozen=True)
class GuiaUnica:
    """Identificador alfanumérico exclusivo asignado en el registro inicial[cite: 10]."""
    codigo: str

    def __post_init__(self):
        if not isinstance(self.codigo, str) or not self.codigo.strip():
            raise CargoBoxDomainError("Es necesario proporcionar un número de guía válido.")


# --- EVENTOS DE DOMINIO ---
@dataclass(frozen=True)
class DomainEvent:
    ocurrido_en: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass(frozen=True)
class PaqueteRecibido(DomainEvent):
    guia: str = ""

@dataclass(frozen=True)
class PaqueteEntregado(DomainEvent):
    guia: str = ""
    evidencia: str = ""

@dataclass(frozen=True)
class PaqueteDevuelto(DomainEvent):
    guia: str = ""

@dataclass(frozen=True)
class PerdidaDeclarada(DomainEvent):
    guia: str = ""


# --- ENTIDAD RAÍZ (AGGREGATE ROOT) ---
@dataclass
class Paquete:
    guia: GuiaUnica
    peso_kg: float
    dimension_max_m: float
    estado: EstadoPaquete = EstadoPaquete.RECIBIDO
    intentos_entrega: int = 0
    evidencia_pod: Optional[str] = None
    eventos: List[DomainEvent] = field(default_factory=list)

    def __post_init__(self):
        # REGLA 1: Restricciones físicas (Máximo 30 kg y 1.5 m)[cite: 10, 48]
        if self.peso_kg <= 0 or self.peso_kg > 30.0:
            raise LimiteFisicoExcedido("El paquete excede el límite máximo de peso permitido de 30 kg[cite: 10, 48].")
        if self.dimension_max_m <= 0 or self.dimension_max_m > 1.5:
            raise LimiteFisicoExcedido("La dimensión del paquete excede el tamaño máximo permitido de 1.5 metros[cite: 10, 48].")
        
        # Registrar evento inicial si el paquete es nuevo
        if not self.eventos and self.estado == EstadoPaquete.RECIBIDO:
            self.eventos.append(PaqueteRecibido(guia=self.guia.codigo))

    def _registrar_evento(self, evento: DomainEvent):
        self.eventos.append(evento)

    def pull_events(self) -> List[DomainEvent]:
        """Extrae y limpia los eventos acumulados."""
        pendientes = self.eventos
        self.eventos = []
        return pendientes

    # --- FLUKO OPERATIVO Y TRANSACCIONES ---
    def clasificar(self):
        if self.estado != EstadoPaquete.RECIBIDO:
            raise InvalidStateTransition("El paquete debe ser recibido en sucursal antes de poder clasificarse.")
        self.estado = EstadoPaquete.CLASIFICADO

    def despachar_a_transito(self):
        if self.estado != EstadoPaquete.CLASIFICADO:
            raise InvalidStateTransition("El paquete debe estar clasificado antes de salir a ruta de tránsito.")
        self.estado = EstadoPaquete.EN_TRANSITO

    def llegar_a_centro_destino(self):
        if self.estado != EstadoPaquete.EN_TRANSITO:
            raise InvalidStateTransition("El paquete debe estar en tránsito para registrar su llegada al centro de destino.")
        self.estado = EstadoPaquete.CENTRO_DESTINO

    def iniciar_reparto(self):
        if self.estado != EstadoPaquete.CENTRO_DESTINO:
            raise InvalidStateTransition("El paquete debe estar en el centro de destino para poder salir a reparto.")
        self.estado = EstadoPaquete.EN_REPARTO

    def registrar_intento_fallido(self):
        """REGLA 2: Límite de 2 reintentos antes de ir a punto de recolección."""
        if self.intentos_entrega >= 2:
            raise LimiteReintentosExcedido("Se ha alcanzado el límite máximo de 2 visitas a domicilio. El envío pasa a resguardo en punto de recolección.")
            
        if self.estado != EstadoPaquete.EN_REPARTO:
            raise InvalidStateTransition("Solo se pueden registrar visitas fallidas cuando el paquete está en reparto.")
        
        self.intentos_entrega += 1
        if self.intentos_entrega >= 2:
            self.estado = EstadoPaquete.EN_PUNTO_RECOLECCION
        else:
            self.estado = EstadoPaquete.EN_REPARTO

    def enviar_a_punto_recoleccion(self):
        if self.estado not in [EstadoPaquete.CENTRO_DESTINO, EstadoPaquete.EN_REPARTO]:
            raise InvalidStateTransition("No es posible transferir el envío a un punto de recolección en su etapa actual.")
        self.estado = EstadoPaquete.EN_PUNTO_RECOLECCION

    def completar_entrega(self, evidencia: str):
        """REGLA 3: Evidencia digital POD obligatoria (RN-06)[cite: 5, 10, 48]."""
        if self.estado != EstadoPaquete.EN_REPARTO:
            raise InvalidStateTransition("Solo se puede finalizar la entrega si el paquete está actualmente en repartidor.")
        
        if not evidencia or not evidencia.strip():
            raise SinEvidenciaPOD("No se puede completar la entrega sin adjuntar la firma digital o fotografía del receptor[cite: 5, 10, 48].")
        
        self.evidencia_pod = evidencia.strip()
        self.estado = EstadoPaquete.ENTREGADO
        self._registrar_evento(PaqueteEntregado(guia=self.guia.codigo, evidencia=self.evidencia_pod))

    def iniciar_devolucion(self):
        if self.estado not in [EstadoPaquete.EN_PUNTO_RECOLECCION, EstadoPaquete.EN_REPARTO, EstadoPaquete.CENTRO_DESTINO]:
            raise InvalidStateTransition("El paquete no cumple con las condiciones operativas para iniciar devolución a origen.")
        self.estado = EstadoPaquete.DEVUELTO
        self._registrar_evento(PaqueteDevuelto(guia=self.guia.codigo))

    def declarar_perdida(self):
        if self.estado == EstadoPaquete.ENTREGADO:
            raise InvalidStateTransition("No es posible declarar como perdido un envío que ya fue entregado exitosamente.")
        self.estado = EstadoPaquete.PERDIDO
        self._registrar_evento(PerdidaDeclarada(guia=self.guia.codigo))