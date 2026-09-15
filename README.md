# Proyecto Integrador - Data Science (FPUNA)

**Fase 1: Análisis Descriptivo y Exploratorio de Siniestros Viales (Año 2021)**

## Descripción del Proyecto

Este repositorio contiene los entregables y el código fuente correspondientes a la Fase 1 del Proyecto Integrador de la asignatura Ciencia de Datos (FPUNA).

El objetivo del proyecto es realizar un análisis descriptivo y exploratorio de las estadísticas oficiales de personas afectadas en accidentes de tránsito en Paraguay durante el año 2021, aplicando técnicas de procesamiento, análisis estadístico y visualización de datos.

## Estructura del Repositorio

El proyecto respeta la estructura de directorios exigida por la cátedra:

- `/data`: contiene el archivo de datos oficial del anuario de la Policía Nacional (`12.2.1`).
- `/notebooks`: contiene el Jupyter Notebook ejecutable (`.ipynb`) con el análisis, procesamiento y visualizaciones.
- `/src`: contiene scripts auxiliares de código, si aplica.
- `/output`: contiene los archivos generados durante el análisis, incluyendo el dataset procesado y limpio (`accidentes_limpio.csv`) y la exportación del notebook en formato HTML.
- `requirements.txt`: contiene las dependencias necesarias para reproducir el entorno de ejecución.

## Requisitos

Para ejecutar el proyecto se requiere:

- Python 3.9 o superior.
- Jupyter Notebook o Visual Studio Code con soporte para Jupyter.
- Las dependencias especificadas en `requirements.txt`.

## Dependencias

Las librerías necesarias para la ejecución completa del proyecto se encuentran declaradas en el archivo `requirements.txt`.

Para instalarlas, ejecutar desde la raíz del proyecto:

```bash
python -m pip install -r requirements.txt
```

## Instrucciones de Reproducibilidad

1. Clonar el repositorio:

```bash
git clone https://github.com/Alanalcarazpy7/proyecto-accidentes-datascience.git
```

2. Ingresar al directorio del proyecto:

```bash
cd proyecto-accidentes-datascience
```

3. Instalar las dependencias:

```bash
python -m pip install -r requirements.txt
```

4. Abrir el notebook ubicado en:

```text
/notebooks/Fase1_Accidentes_Transito.ipynb
```

5. Ejecutar todas las celdas del notebook en orden, desde el inicio hasta el final, sin modificaciones manuales previas.

6. Los archivos generados durante la ejecución se almacenarán en el directorio `/output`.

## Fuente de Datos

Los datos utilizados corresponden a estadísticas oficiales de siniestros viales registradas en Paraguay durante el año 2021 y utilizadas con fines académicos para el desarrollo del Proyecto Integrador.

## Salidas del Proyecto

La ejecución completa del notebook genera:

- Dataset procesado y limpio.
- Estadísticas descriptivas.
- Tablas de contingencia.
- Análisis de correlaciones.
- Visualizaciones de los datos.

## Reproducibilidad

El proyecto fue estructurado para que el análisis pueda reproducirse a partir de los datos originales. Una vez instaladas las dependencias indicadas en `requirements.txt`, el notebook puede ejecutarse secuencialmente sin modificaciones manuales.
