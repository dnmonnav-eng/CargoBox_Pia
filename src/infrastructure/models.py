from sqlalchemy import Column, String, Float, Integer
from src.infrastructure.database import Base

class PaqueteModel(Base):
    __tablename__ = "paquetes"

    guia = Column(String, primary_key=True, index=True)
    peso_kg = Column(Float, nullable=False)
    largo_m = Column(Float, nullable=False)
    ancho_m = Column(Float, nullable=False)
    alto_m = Column(Float, nullable=False)
    telefono_cliente = Column(String, nullable=False)
    estado = Column(String, nullable=False)
    intentos_entrega = Column(Integer, default=0)
    evidencia_pod = Column(String, nullable=True)