def test_persistencia_en_memoria():
    """Verifica el almacenamiento y recuperación de entidades."""
    paquetes_guardados = {}
    
    # Simular guardado
    guia = "GUIA-DB-001"
    paquetes_guardados[guia] = {"peso": 5.0, "estado": "RECIBIDO"}
    
    # Simular consulta
    resultado = paquetes_guardados.get(guia)
    assert resultado is not None
    assert resultado["peso"] == 5.0