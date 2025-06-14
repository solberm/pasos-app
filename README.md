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

## Uso Local

1. Ejecuta la aplicación:
   ```bash
   python app.py
   ```

2. Abre tu navegador y ve a `http://localhost:5000`

3. Usa la interfaz web para:
   - Calcular pasos entre dos estaciones
   - Encontrar destinos mínimos desde una estación

## Despliegue en Render

### Opción 1: Despliegue Automático (Recomendado)

1. **Conecta tu repositorio a Render**:
   - Ve a [render.com](https://render.com) y crea una cuenta
   - Haz clic en "New +" y selecciona "Web Service"
   - Conecta tu repositorio de GitHub/GitLab
   - Render detectará automáticamente que es una aplicación Flask

2. **Configuración automática**:
   - **Name**: `pasos-app` (o el nombre que prefieras)
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free (para empezar)

3. **Haz clic en "Create Web Service"**

### Opción 2: Despliegue Manual

Si prefieres configurar manualmente:

1. Crea un nuevo Web Service en Render
2. Conecta tu repositorio
3. Usa estas configuraciones:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Environment Variables**: No necesarias para esta aplicación

### Después del Despliegue

- Render te proporcionará una URL pública (ej: `https://tu-app.onrender.com`)
- La aplicación estará disponible para todos los usuarios
- Cada vez que hagas push a tu repositorio, Render actualizará automáticamente la aplicación

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
├── render.yaml         # Configuración para Render
├── runtime.txt         # Versión de Python
├── Procfile           # Configuración para Heroku (compatible)
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