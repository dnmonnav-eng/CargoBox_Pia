from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import unicodedata
import uuid

from src.application.service import CargoBoxService
from src.domain import (
    LimiteFisicoExcedido,
    LimiteReintentosExcedido,
    SinEvidenciaPOD,
    InvalidStateTransition,
    CargoBoxDomainError
)
from src.infrastructure.database import engine, Base, get_db
from src.infrastructure.models import PaqueteModel

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CargoBox API",
    version="1.0.0",
    description="API oficial de CargoBox"
)

service = CargoBoxService()

class RegistroPaqueteRequest(BaseModel):
    peso_kg: float = Field(..., gt=0)
    largo_m: float = Field(..., gt=0)
    ancho_m: float = Field(..., gt=0)
    alto_m: float = Field(..., gt=0)
    telefono_cliente: str = Field(..., pattern=r"^\d{10}$")

class EntregaRequest(BaseModel):
    evidencia: str = Field(..., description="Escribe la evidencia (Firma digital / Fotografía del paquete)")

class IncidenciaRequest(BaseModel):
    tipo_incidencia: str = Field(
        ..., 
        description="Escribe EXACTAMENTE una de estas opciones: 'direccion_incorrecta', 'paquete_danado', 'perdida', 'rechazo'"
    )

def normalizar_texto(texto: str) -> str:
    if not texto:
        return ""
    texto_sin_acento = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    return texto_sin_acento.lower().strip().replace(" ", "_")


@app.get("/")
def inicio():
    return {"mensaje": "Bienvenido al sistema logístico de CargoBox"}


@app.post("/paquetes/")
def registrar_paquete(datos: RegistroPaqueteRequest, db: Session = Depends(get_db)):
    try:
        guia_generada = f"CBX-{uuid.uuid4().hex[:8].upper()}"
        paquete = service.registrar_envio(
            db=db,
            codigo_guia=guia_generada, 
            peso_kg=datos.peso_kg, 
            largo_m=datos.largo_m,
            ancho_m=datos.ancho_m,
            alto_m=datos.alto_m,
            telefono_cliente=datos.telefono_cliente
        )
        return {
            "mensaje": f"Paquete recibido con éxito, guía única generada: {paquete.guia}."
        }
    except LimiteFisicoExcedido:
        raise HTTPException(status_code=422, detail="El paquete excede los límites permitidos (máx 30 kg o 1.5 m por lado).")
    except CargoBoxDomainError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/paquetes/{guia}/clasificar")
def clasificar_paquete(guia: str, db: Session = Depends(get_db)):
    try:
        paquete = service.avanzar_estado(db, guia, "CLASIFICADO")
        return {"mensaje": f"El paquete con la guía {paquete.guia} ha sido clasificado correctamente."}
    except (InvalidStateTransition, CargoBoxDomainError) as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError:
        raise HTTPException(status_code=404, detail="No se encontró un paquete con esa guía.")


@app.post("/paquetes/{guia}/despachar-transito")
def despachar_transito(guia: str, db: Session = Depends(get_db)):
    try:
        paquete = service.avanzar_estado(db, guia, "EN_TRANSITO")
        return {"mensaje": f"El paquete con la guía {paquete.guia} se encuentra en Tránsito al Centro de Distribución Destino."}
    except (InvalidStateTransition, CargoBoxDomainError) as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError:
        raise HTTPException(status_code=404, detail="No se encontró un paquete con esa guía.")


@app.post("/paquetes/{guia}/centro-destino")
def llegar_centro_destino(guia: str, db: Session = Depends(get_db)):
    try:
        paquete = service.avanzar_estado(db, guia, "CENTRO_DESTINO")
        return {"mensaje": f"El paquete con la guía {paquete.guia} ha llegado al Centro de Distribución Destino."}
    except (InvalidStateTransition, CargoBoxDomainError) as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError:
        raise HTTPException(status_code=404, detail="No se encontró un paquete con esa guía.")


@app.post("/paquetes/{guia}/iniciar-reparto")
def iniciar_reparto(guia: str, db: Session = Depends(get_db)):
    try:
        paquete = service.avanzar_estado(db, guia, "EN_REPARTO")
        return {"mensaje": f"El paquete con la guía {paquete.guia} se encuentra en Reparto."}
    except (InvalidStateTransition, CargoBoxDomainError) as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError:
        raise HTTPException(status_code=404, detail="No se encontró un paquete con esa guía.")


@app.post("/paquetes/{guia}/intentos-fallidos")
def registrar_intento_fallido(guia: str, db: Session = Depends(get_db)):
    """Registra intento fallido. Al llegar al 2do intento, el paquete se transfiere al Punto de Recolección / Resguardo más cercano."""
    try:
        paquete = service.registrar_intento_entrega(db, guia)
        if paquete.intentos_entrega >= 2:
            return {
                "mensaje": f"Se registró el 2do intento fallido. Se ha alcanzado el límite de intentos: el paquete ha sido transferido a resguardo en el Punto de Recolección."
            }
        return {
            "mensaje": f"Visita fallida registrada (Intento {paquete.intentos_entrega} de 2)."
        }
    except LimiteReintentosExcedido as e:
        raise HTTPException(status_code=422, detail="Se alcanzó el límite de 2 intentos. El paquete ya se encuentra en resguardo (Punto de Recolección).")
    except (InvalidStateTransition, CargoBoxDomainError) as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError:
        raise HTTPException(status_code=404, detail="No se encontró un paquete con esa guía.")


@app.post("/paquetes/{guia}/incidencias")
def registrar_incidencia_entrega(guia: str, datos: IncidenciaRequest, db: Session = Depends(get_db)):
    """
    Escribe la incidencia. Opciones válidas:
    - 'direccion_incorrecta' 
    - 'paquete_danado' 
    - 'perdida' 
    - 'rechazo' 
    """
    try:
        limpio = normalizar_texto(datos.tipo_incidencia)
        
        opciones_validas = ["direccion_incorrecta", "paquete_danado", "perdida", "rechazo"]
        if limpio not in opciones_validas:
            raise HTTPException(
                status_code=400, 
                detail=f"Incidencia no válida. Debes escribir exactamente una de estas opciones: {opciones_validas}"
            )

        paquete = service.procesar_incidencia(db, guia, limpio)
        
        if limpio == "direccion_incorrecta":
            return {
                "mensaje": f"Dirección Incorrecta para la guía {guia}. El paquete ha regresado al Centro de Distribución de Destino. Soporte contactará al cliente al teléfono {paquete.telefono_cliente} en menos de 4 horas.",
                "estado_actual": paquete.estado
            }
        elif limpio == "paquete_danado":
            return {
                "mensaje": f"Paquete Dañado para la guía {guia}. El paquete ha regresado al Centro de Distribución de Destino para su valoración y reporte por Supervisor de Calidad.",
                "estado_actual": paquete.estado
            }
        elif limpio == "perdida":
            return {
                "mensaje": f"Incidencia de Pérdida para la guía {guia}. Se ha iniciado el proceso de reclamación y compensación para el cliente.",
                "estado_actual": paquete.estado
            }
        elif limpio == "rechazo":
            return {
                "mensaje": f"Rechazo para el paquete con la guía {guia}. El paquete se ha regresado al origen y se aplicará el cobro correspondiente por devolución.",
                "estado_actual": paquete.estado
            }
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidStateTransition as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.post("/paquetes/{guia}/entregar")
def completar_entrega(guia: str, datos: EntregaRequest, db: Session = Depends(get_db)):
    try:
        paquete = service.completar_entrega_paquete(db, guia, datos.evidencia)
        return {"mensaje": f"¡Entrega exitosa para la guía {paquete.guia}!"}
    except SinEvidenciaPOD:
        raise HTTPException(status_code=422, detail="No se puede cerrar la entrega sin la evidencia requerida.")
    except (InvalidStateTransition, CargoBoxDomainError) as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError:
        raise HTTPException(status_code=404, detail="No se encontró un paquete con esa guía.")