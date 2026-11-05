# CargoBox - Sistema de Gestión Logística 

## Estructura del Proyecto

El proyecto sigue rigurosamente la estructura modular y de capas solicitada en la arquitectura:

```text
CargoBox_Pia/
├── docs/                 # Documentación (BRD, diagramas BPMN, ADRs, OpenAPI)
├── src/
│   ├── domain.py         # Núcleo de negocio: entidades, Value Objects, eventos y máquina de estados
│   ├── application/
│   │   └── service.py    # Casos de uso y coordinación de la lógica de aplicación
│   ├── infrastructure/   # Repositorios y persistencia de datos
│   └── api/
│       └── api.py        # Endpoints REST con FastAPI y respuestas humanas/empáticas
├── tests/
│   └── test_cargobox.py  # Suite completa de pruebas unitarias con pytest
├── .github/
│   └── workflows/
│       └── ci.yaml       # Pipeline automatizado de CI/CD (GitHub Actions)
├── docker-compose.yml    # Contenedorización para despliegue y pruebas
├── .env.example          # Plantilla de variables de entorno (sin credenciales)
└── README.md             # Instrucciones técnicas, ejecución y demostración
```

---

## Reglas de Negocio Implementadas

1. **Restricciones Físicas:** Todo paquete registrado en sucursal es validado estrictamente. El peso máximo permitido es de **30 kg** y ninguna de sus dimensiones individuales (largo, ancho o alto) puede superar los **1.5 metros**.
2. **Máquina de Estados Logística:** El ciclo de vida del paquete está gobernado por transiciones estrictas:
   `RECIBIDO` `CLASIFICADO` `EN_TRÁNSITO`  `CENTRO_DESTINO`  `EN_REPARTO`  (`ENTREGADO` / `EN_PUNTO_RECOLECCION` / `DEVUELTO` / `PERDIDO`).
3. **Límite de Reintentos:** Las visitas domiciliarias fallidas están limitadas a un máximo de **2 intentos**. Al superar este límite, el sistema transiciona automáticamente el paquete a resguardo en un punto de recolección.
4. **Evidencia Digital Obligatoria (RN-06):** Ninguna entrega puede cerrarse con éxito sin adjuntar la evidencia digital **POD** (fotografía del paquete en domicilio o firma digital del receptor).

---

## Guía de Instalación y Ejecución Local

### 1. Clonar el repositorio y configurar el entorno virtual
Abre tu terminal en la carpeta del proyecto y ejecuta:
```powershell
python -m venv .venv
# Activar en Windows (PowerShell):
.venv\Scripts\Activate.ps1
```

### 2. Instalar dependencias
```powershell
pip install fastapi uvicorn pytest pytest-cov
```

### 3. Ejecutar las pruebas unitarias con cobertura
Para comprobar que el núcleo y los servicios funcionan perfectamente con una cobertura superior al umbral requerido:
```powershell
python -m pytest -v --cov=src --cov-report=term-missing
```

### 4. Levantar el servidor de la API REST
```powershell
python -m uvicorn src.api.api:app --reload
```

### 5. Documentación Interactiva (Swagger UI)
Una vez iniciado el servidor, abre tu navegador e ingresa a:
 **`http://127.0.0.1:8000/docs`**

Aquí podrás interactuar con todos los endpoints operativos:
* Registro de paquetes en sucursal con autogeneración de Guía Única y vinculación de correo del cliente.
* Avance de estados por los centros de distribución y tránsito.
* Registro de intentos fallidos en ruta.
* Cierre de entrega validando la evidencia digital POD.
* Gestión de excepciones e incidencias (direcciones incorrectas, paquetes dañados, devoluciones).

---

## Despliegue con Docker Compose

Para levantar el entorno contenedorizado como lo solicita la rúbrica de producción:
```powershell
docker-compose up --build
```

---

## Calidad y Automatización (CI/CD)
El repositorio cuenta con un pipeline activo en **GitHub Actions** (`.github/workflows/ci.yaml`) que ejecuta automáticamente la suite de pruebas `pytest` en cada `push`, garantizando la estabilidad y calidad continua del código.