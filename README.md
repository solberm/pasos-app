# SCMM - Sistema de Cálculo de Métricas de Metro

Esta es una aplicación web desarrollada en Flask que permite calcular rutas mínimas entre estaciones del metro de Madrid y encontrar los destinos más cercanos desde una estación específica.

## Características

- **Cálculo de Pasos**: Calcula la ruta mínima entre dos estaciones del metro
- **Destinos Mínimos**: Encuentra los 20 destinos más cercanos desde una estación de origen
- **Interfaz Web**: Interfaz gráfica moderna y fácil de usar
- **API REST**: Endpoints JSON para integración con otras aplicaciones

## Instalación

1. Clona o descarga este repositorio
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

1. Ejecuta la aplicación:
   ```bash
   python app.py
   ```

2. Abre tu navegador y ve a `http://localhost:5000`

3. Usa la interfaz web para:
   - Calcular pasos entre dos estaciones
   - Encontrar destinos mínimos desde una estación

## API Endpoints

### Calcular Pasos
- **URL**: `/api/pasos`
- **Método**: `POST`
- **Body**: 
  ```json
  {
    "origen": "1-SOL",
    "destino": "2-CUATRO CAMINOS"
  }
  ```
- **Respuesta**:
  ```json
  {
    "pasos": 5,
    "ruta": ["1SOL", "1TRIBUNAL", "1BILBAO", "1CUATROCAMINOS", "2CUATROCAMINOS"]
  }
  ```

### Destinos Mínimos
- **URL**: `/api/destinos`
- **Método**: `POST`
- **Body**:
  ```json
  {
    "origen": "1-SOL"
  }
  ```
- **Respuesta**:
  ```json
  {
    "resultados": [
      [2, "1-TRIBUNAL"],
      [3, "1-BILBAO"],
      [4, "1-CUATRO CAMINOS"]
    ]
  }
  ```

## Estructura del Proyecto

```
├── app.py              # Aplicación principal Flask
├── data.py             # Datos de estaciones y correspondencias
├── requirements.txt    # Dependencias de Python
├── templates/          # Plantillas HTML
│   └── index.html     # Interfaz principal
├── README.md          # Este archivo
├── icono.ico          # Icono de la aplicación
└── marca_agua.png     # Imagen de marca de agua
```

## Algoritmo

La aplicación utiliza el algoritmo de Dijkstra para encontrar las rutas mínimas entre estaciones, considerando:

- Conexiones directas entre estaciones consecutivas
- Correspondencias entre líneas
- Excepciones de coste entre estaciones específicas
- Depósitos y sus asociaciones

## Autor

Zala - v.2.22.100

## Licencia

Este proyecto es de uso interno para el sistema de metro de Madrid. 