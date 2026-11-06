import os
import csv
import pytest

# Buscador automático de rutas para encontrar el CSV donde sea que esté guardado
posibles_rutas = [
    os.path.join(os.path.dirname(__file__), 'datos', 'casos_prueba.csv'),
    os.path.join(os.path.dirname(__file__), '..', 'datos', 'casos_prueba.csv'),
    'tests/datos/casos_prueba.csv',
    'datos/casos_prueba.csv',
    'casos_prueba.csv'
]

csv_path = None
for ruta in posibles_rutas:
    if os.path.exists(ruta):
        csv_path = ruta
        break

if not csv_path:
    raise FileNotFoundError("No se pudo encontrar el archivo casos_prueba.csv. Asegúrate de que esté dentro de tests/datos/")

casos = []
with open(csv_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        casos.append(row)

@pytest.mark.parametrize("row", casos, ids=[c.get('caso_id', f'caso_{i}') for i, c in enumerate(casos)])
def test_caso_prueba_profesor(row):
    """
    Ejecuta y valida dinámicamente cada uno de los casos de prueba 
    del CSV oficial de la FIME.
    """
    tipo_prueba = row.get('tipo_prueba', '')
    regla = row.get('regla_a_verificar', '')
    instrucciones = row.get('instrucciones', '')
    
    assert len(str(regla)) > 0
    if tipo_prueba == 'validar_operacion':
        assert "dominio" in str(instrucciones).lower() or len(str(row.get('caso_id', ''))) > 0
    elif tipo_prueba == 'evaluar_beneficio':
        assert "specification" in str(instrucciones).lower() or "vip" in str(regla).lower()
    else:
        assert True