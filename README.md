# Proyecto Integrador de Ciencia de Datos ? tr?nsito en Brasil

Esta rama (`data-fase-3-brasil`) re?ne la investigaci?n, las tres fases y la mejora del modelo de gravedad de v?ctimas con datos oficiales de PRF Brasil. Se conservan tambi?n los materiales anteriores de Paraguay como contexto del trabajo.

## Por d?nde empezar

- [Mejor opci?n seleccionada: informe breve de la fase 3](PROYECTO_GRAVEDAD_BRASIL/MEJORA_FASE_3/output/INFORME_MEJORA_FASE_3.pdf).
- [Notebook ejecutado de la mejora](PROYECTO_GRAVEDAD_BRASIL/MEJORA_FASE_3/output/Mejora_Fase_3.ipynb).
- [Las tres fases y su reproducci?n](PROYECTO_GRAVEDAD_BRASIL/README.md).
- [M?todo y resultados de la versi?n mejorada](PROYECTO_GRAVEDAD_BRASIL/MEJORA_FASE_3/README.md).

La versi?n elegida usa 31 caracter?sticas. En la nueva prueba de enero a septiembre de 2026, sobre 67.591 v?ctimas, obtuvo AUC 0,845 y F1 macro 0,675; la referencia obtuvo 0,799 y 0,647 respectivamente. La mejora conserva errores importantes y no constituye un modelo cl?nico validado. Los informes declaran el uso de asistencia de IA y las limitaciones del an?lisis.

## Reproducir el proyecto de Brasil

```powershell
cd PROYECTO_GRAVEDAD_BRASIL
python -m pip install -r requirements.txt
```

Continuar con los pasos del README del proyecto y de `MEJORA_FASE_3`. Los informes PDF, notebooks ejecutados, modelos, manifiestos, tablas y datasets limpios Parquet est?n versionados. Los datos originales voluminosos, ZIP de entrega, cach?s y temporales est?n excluidos por `.gitignore`; las URLs, hashes y scripts para obtener las fuentes se conservan.

## Material anterior

Las carpetas de Caminera, investigaci?n de fuentes y pron?stico de Paraguay se mantienen en esta rama por decisi?n del grupo. El trabajo elegido para continuar es la clasificaci?n de v?ctimas de Brasil indicada arriba.

<details>
<summary>Documentaci?n anterior del repositorio</summary>

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


</details>
