from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
from src.application.service import CargoBoxService
from src.domain import (
    LimiteFisicoExcedido,
    LimiteReintentosExcedido,
    SinEvidenciaPOD,
    InvalidStateTransition,
    CargoBoxDomainError
)

app = FastAPI(
    title="CargoBox API",
    version="1.0.0",
    description="API oficial de CargoBox"
)

service = CargoBoxService()

class RegistroPaqueteRequest(BaseModel):
    peso_kg: float
    largo_m: float
    ancho_m: float
    alto_m: float
    correo_cliente: str

class EntregaRequest(BaseModel):
    evidencia: str

class IncidenciaRequest(BaseModel):
    tipo_incidencia: str  


@app.get("/")
def inicio():
    return {"mensaje": "Bienvenido al sistema logístico de CargoBox"}


@app.post("/paquetes/")
def registrar_paquete(datos: RegistroPaqueteRequest):
    """
    Valida los límites físicos (máximo 30 kg o 1.5 metros por lado) y genera la Guía Única.
    """
    try:
        dimension_maxima = max(datos.largo_m, datos.ancho_m, datos.alto_m)
        
        guia_generada = f"CBX-{uuid.uuid4().hex[:8].upper()}"
        
        paquete = service.registrar_envio(
            codigo_guia=guia_generada, 
            peso_kg=datos.peso_kg, 
            dimension_max_m=dimension_maxima
        )
        
        return {
            "mensaje": f"Paquete recibido con éxito, guía única generada: {paquete.guia.codigo}"
        }
        
    except LimiteFisicoExcedido:
        raise HTTPException(
            status_code=422, 
            detail="El paquete excede los límites permitidos (máximo 30 kg o 1.5 metros por lado). No se puede recibir."
        )
    except CargoBoxDomainError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/paquetes/{guia}/clasificar")
def clasificar_paquete(guia: str):
    """Centro de Distribución de Origen: Clasificar paquete y registrar estado CLASIFICADO."""
    try:
        paquete = service.avanzar_a_clasificado(guia)
        return {
            "mensaje": f"El paquete con la guía {paquete.guia.codigo} ha sido clasificado correctamente en el centro de distribución de origen."
        }
    except (InvalidStateTransition, CargoBoxDomainError) as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError:
        raise HTTPException(status_code=404, detail="No se encontró un paquete con esa guía.")


@app.post("/paquetes/{guia}/despachar-transito")
def despachar_transito(guia: str):
    """Despachar paquete y registrar estado EN TRÁNSITO a CD Destino."""
    try:
        paquete = service.despachar_a_transito(guia)
        return {
            "mensaje": f"El paquete con la guía {paquete.guia.codigo} se encuentra ahora en Tránsito al Centro de Distribución Destino."
        }
    except (InvalidStateTransition, CargoBoxDomainError) as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError:
        raise HTTPException(status_code=404, detail="No se encontró un paquete con esa guía.")


@app.post("/paquetes/{guia}/centro-destino")
def llegar_centro_destino(guia: str):
    """Recepción CD Destino y registrar estado CENTRO_DESTINO."""
    try:
        paquete = service.llegar_a_centro_destino(guia)
        return {
            "mensaje": f"El paquete con la guía {paquete.guia.codigo} ha llegado al Centro de Distribución Destino.",
        }
    except (InvalidStateTransition, CargoBoxDomainError) as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError:
        raise HTTPException(status_code=404, detail="No se encontró un paquete con esa guía.")


@app.post("/paquetes/{guia}/iniciar-reparto")
def iniciar_reparto(guia: str):
    """Repartidor: Cargar unidad y registrar estado EN REPARTO."""
    try:
        paquete = service.iniciar_reparto(guia)
        return {
            "mensaje": f"El paquete con la guía {paquete.guia.codigo} se encuentra en Reparto.",
        }
    except (InvalidStateTransition, CargoBoxDomainError) as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError:
        raise HTTPException(status_code=404, detail="No se encontró un paquete con esa guía.")


@app.post("/paquetes/{guia}/intentos-fallidos")
def registrar_intento_fallido(guia: str):
    """Repartidor: Registra ausencia del destinatario (Intento 1 o 2)."""
    try:
        paquete = service.registrar_intento_entrega(guia)
        return {
            "mensaje": f"Se registró visita fallida para la guía {paquete.guia.codigo}. Intentos acumulados: {paquete.intentos_entrega}.",
        }
    except LimiteReintentosExcedido:
        raise HTTPException(
            status_code=422, 
            detail="Se alcanzó el límite de 2 intentos. El paquete fue transferido a resguardo en el punto de recolección."
        )
    except (InvalidStateTransition, CargoBoxDomainError) as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError:
        raise HTTPException(status_code=404, detail="No se encontró un paquete con esa guía.")


@app.post("/paquetes/{guia}/incidencias")
def registrar_incidencia_entrega(guia: str, datos: IncidenciaRequest):
    """Soporte y Operaciones: Dirección incorrecta, Daño, Pérdida."""
    try:
        paquete = service.obtener_paquete(guia)
        if not paquete:
            raise HTTPException(status_code=404, detail="No se encontró un paquete con esa guía.")
        
        incidencia = datos.tipo_incidencia.lower()
        
        if incidencia == "direccion_incorrecta":
            return {"mensaje": f"Incidencia registrada para la guía {guia}: Dirección incorrecta. Soporte contactará al cliente en un plazo menor a 4 horas."}
        elif incidencia == "paquete_danado":
            return {"mensaje": f"Incidencia registrada para la guía {guia}: Paquete dañado. Turnado a Supervisor de Calidad para generar reporte y evaluar compensación."}
        elif incidencia == "perdida_rechazo":
            return {"mensaje": f"Incidencia registrada para la guía {guia}: Pérdida o rechazo prolongado. Se escaló a devolución o cancelación."}
        else:
            return {"mensaje": f"Incidencia general registrada para la guía {guia}: {datos.tipo_incidencia}."}
            
    except ValueError:
        raise HTTPException(status_code=404, detail="No se encontró un paquete con esa guía.")


@app.post("/paquetes/{guia}/entregar")
def completar_entrega(guia: str, datos: EntregaRequest):
    """Destino: Entrega exitosa y registro de evidencia digital POD (Firma/Foto)."""
    try:
        paquete = service.completar_entrega_paquete(guia, datos.evidencia)
        return {
            "mensaje": f"¡Entrega exitosa para la guía {paquete.guia.codigo}! Evidencia registrada correctamente."
        }
    except SinEvidenciaPOD:
        raise HTTPException(
            status_code=422, 
            detail="No se puede cerrar la entrega sin adjuntar la firma o fotografía requerida."
        )
    except (InvalidStateTransition, CargoBoxDomainError) as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError:
        raise HTTPException(status_code=404, detail="No se encontró un paquete con esa guía.")