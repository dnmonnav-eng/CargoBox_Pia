# src/infrastructure/repository.py

class PaqueteRepositoryMemoria:
    """
    Implementación de infraestructura para almacenar y recuperar 
    los paquetes del sistema CargoBox.
    """
    def __init__(self):
        self._almacen = {}

    def guardar(self, paquete):
        self._almacen[paquete.guia.codigo] = paquete
        return paquete

    def obtener_por_guia(self, codigo: str):
        return self._almacen.get(codigo)

    def listar_todos(self):
        return list(self._almacen.values())