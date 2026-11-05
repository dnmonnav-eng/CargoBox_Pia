from typing import Optional, List
from src.domain import Paquete, GuiaUnica, EstadoPaquete

class CargoBoxService:
    """
    Capa de Aplicación que coordina los casos de uso y la lógica de negocio
    para la gestión de paquetes de CargoBox, manteniendo el dominio desacoplado.
    """

    def __init__(self):
        # Simulación de repositorio en memoria (diccionario de guías) para este paso
        self._repositorio_paquetes = {}

    def registrar_envio(self, codigo_guia: str, peso_kg: float, dimension_max_m: float) -> Paquete:
        """Caso de uso: Registrar un nuevo paquete en sucursal (CU-01)[cite: 50]."""
        guia = GuiaUnica(codigo=codigo_guia)
        paquete = Paquete(guia=guia, peso_kg=peso_kg, dimension_max_m=dimension_max_m)
        self._repositorio_paquetes[codigo_guia] = paquete
        return paquete

    def obtener_paquete(self, codigo_guia: str) -> Optional[Paquete]:
        """Consulta un paquete por su guía única."""
        return self._repositorio_paquetes.get(codigo_guia)

    def avanzar_a_clasificado(self, codigo_guia: str) -> Paquete:
        """Avanza el paquete al estado clasificado en el centro de distribución."""
        paquete = self.obtener_paquete(codigo_guia)
        if not paquete:
            raise ValueError("No se encontró ningún paquete con la guía proporcionada.")
        paquete.clasificar()
        return paquete
    
    def registrar_intento_entrega(self, codigo_guia: str) -> Paquete:
        """Registra un intento fallido de entrega (respeta el límite de 2)[cite: 5, 10, 48, 50]."""
        paquete = self.obtener_paquete(codigo_guia)
        if not paquete:
            raise ValueError("No se encontró ningún paquete con la guía proporcionada.")
        paquete.registrar_intento_fallido()
        return paquete

    def completar_entrega_paquete(self, codigo_guia: str, evidencia_pod: str) -> Paquete:
        """Finaliza la entrega exigiendo obligatoriamente la evidencia digital POD (RN-06)[cite: 5, 10, 48, 50]."""
        paquete = self.obtener_paquete(codigo_guia)
        if not paquete:
            raise ValueError("No se encontró ningún paquete con la guía proporcionada.")
        paquete.completar_entrega(evidencia=evidencia_pod)
        return paquete

    def despachar_a_transito(self, codigo_guia: str) -> Paquete:
        paquete = self.obtener_paquete(codigo_guia)
        if not paquete:
            raise ValueError("No se encontró ningún paquete.")
        paquete.despachar_a_transito()
        return paquete

    def llegar_a_centro_destino(self, codigo_guia: str) -> Paquete:
        paquete = self.obtener_paquete(codigo_guia)
        if not paquete:
            raise ValueError("No se encontró ningún paquete.")
        paquete.llegar_a_centro_destino()
        return paquete

    def iniciar_reparto(self, codigo_guia: str) -> Paquete:
        paquete = self.obtener_paquete(codigo_guia)
        if not paquete:
            raise ValueError("No se encontró ningún paquete.")
        paquete.iniciar_reparto()
        return paquete