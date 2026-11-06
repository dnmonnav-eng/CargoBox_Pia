from sqlalchemy.orm import Session
from src.infrastructure.models import PaqueteModel
from src.domain import (
    EstadoPaquete, 
    LimiteFisicoExcedido, 
    LimiteReintentosExcedido, 
    SinEvidenciaPOD, 
    InvalidStateTransition
)

ORDEN_ESTADOS = [
    "RECIBIDO",
    "CLASIFICADO",
    "EN_TRANSITO",
    "CENTRO_DESTINO",
    "EN_REPARTO",
    "ENTREGADO"
]

def validar_transicion(estado_actual: str, nuevo_estado: str):
    estados_especiales = ["CENTRO_DESTINO", "DEVUELTO_CANCELADO", "PUNTO_RECOLECCION", "EN_REPARTO"]
    if nuevo_estado in estados_especiales:
        return

    try:
        idx_actual = ORDEN_ESTADOS.index(estado_actual)
        idx_nuevo = ORDEN_ESTADOS.index(nuevo_estado)
    except ValueError:
        return
    
    if idx_nuevo != idx_actual + 1:
        raise InvalidStateTransition(
            f"Transición inválida: No se puede cambiar del estado '{estado_actual}' a '{nuevo_estado}'."
        )


class CargoBoxService:
    
    def registrar_envio(self, db: Session, codigo_guia: str, peso_kg: float, largo_m: float, ancho_m: float, alto_m: float, telefono_cliente: str) -> PaqueteModel:
        dimension_maxima = max(largo_m, ancho_m, alto_m)
        if peso_kg > 30.0 or dimension_maxima > 1.5:
            raise LimiteFisicoExcedido("El paquete excede los límites permitidos (máx 30 kg o 1.5 m por lado).")

        nuevo_paquete = PaqueteModel(
            guia=codigo_guia,
            peso_kg=peso_kg,
            largo_m=largo_m,
            ancho_m=ancho_m,
            alto_m=alto_m,
            telefono_cliente=telefono_cliente,
            estado=EstadoPaquete.RECIBIDO.value,
            intentos_entrega=0,
            evidencia_pod=None
        )
        
        db.add(nuevo_paquete)
        db.commit()
        db.refresh(nuevo_paquete)
        return nuevo_paquete

    def obtener_paquete(self, db: Session, guia: str) -> PaqueteModel:
        paquete = db.query(PaqueteModel).filter(PaqueteModel.guia == guia).first()
        if not paquete:
            raise ValueError("No se encontró un paquete con esa guía.")
        return paquete

    def avanzar_estado(self, db: Session, guia: str, nuevo_estado: str) -> PaqueteModel:
        paquete = self.obtener_paquete(db, guia)
        validar_transicion(paquete.estado, nuevo_estado)
        
        # SI EL PAQUETE VUELVE A ENTRAR EN REPARTO (por ejemplo, tras corregir dirección), 
        # REINICIAMOS LOS INTENTOS A 0 AUTOMÁTICAMENTE.
        if nuevo_estado == "EN_REPARTO":
            paquete.intentos_entrega = 0

        paquete.estado = nuevo_estado
        db.commit()
        db.refresh(paquete)
        return paquete

    def registrar_intento_entrega(self, db: Session, guia: str) -> PaqueteModel:
        paquete = self.obtener_paquete(db, guia)
        
        if paquete.intentos_entrega is None:
            paquete.intentos_entrega = 0
            
        if paquete.intentos_entrega >= 2:
            paquete.estado = "PUNTO_RECOLECCION"
            db.commit()
            raise LimiteReintentosExcedido("Se alcanzó el límite de 2 intentos de entrega. El paquete ya está en resguardo.")
        
        paquete.intentos_entrega += 1
        
        if paquete.intentos_entrega >= 2:
            paquete.estado = "PUNTO_RECOLECCION"
            
        db.commit()
        db.refresh(paquete)
        return paquete

    def procesar_incidencia(self, db: Session, guia: str, tipo_incidencia: str) -> PaqueteModel:
        paquete = self.obtener_paquete(db, guia)
        incidencia = tipo_incidencia.lower()

        if incidencia == "direccion_incorrecta":
            paquete.estado = "CENTRO_DESTINO"
            # Al regresar al centro para corrección, reseteamos intentos para cuando vuelva a salir
            paquete.intentos_entrega = 0
        elif incidencia == "paquete_danado":
            paquete.estado = "CENTRO_DESTINO"
        elif incidencia in ["perdida", "rechazo"]:
            paquete.estado = "DEVUELTO_CANCELADO"
        else:
            raise ValueError("Tipo de incidencia no reconocido.")

        db.commit()
        db.refresh(paquete)
        return paquete

    def completar_entrega_paquete(self, db: Session, guia: str, evidencia: str) -> PaqueteModel:
        if not evidencia or not evidencia.strip():
            raise SinEvidenciaPOD("Falta la evidencia POD requerida.")
            
        paquete = self.obtener_paquete(db, guia)
        validar_transicion(paquete.estado, EstadoPaquete.ENTREGADO.value)
        
        paquete.evidencia_pod = evidencia
        paquete.estado = EstadoPaquete.ENTREGADO.value
        
        db.commit()
        db.refresh(paquete)
        return paquete