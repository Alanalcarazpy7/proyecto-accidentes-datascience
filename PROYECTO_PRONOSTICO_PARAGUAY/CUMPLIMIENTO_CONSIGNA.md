# Correspondencia con la consigna de las tres fases

| Requisito | Evidencia entregada | Estado |
|---|---|---|
| Comprensión del problema, 2–3 páginas | `output/reports/Comprension_del_problema.pdf`, 3 páginas | Generado |
| Fase 1, hasta 20 páginas | `Fase_1_Preparacion_y_EDA.pdf`, 16 páginas | Generado |
| Diccionarios original y final | `output/tables/diccionario_original.csv`, `diccionario_final.csv` | Calculados desde originales |
| Dataset limpio y trazabilidad | `data/processed/serie_mensual.csv`; hashes, inventario y celdas | 108 meses; sin imputar objetivos |
| Limpieza documentada | `bitacora_limpieza.csv`; 60 versiones repetidas coincidentes | Verificada |
| Estadística univariada y bivariada | Descriptivos, correlaciones, contingencias y resúmenes por grupo | Calculados |
| Ocho o más visualizaciones interpretadas | Diez gráficos de Fase 1 y sus interpretaciones en PDF y notebook | Generados |
| Cuatro contrastes y al menos tres familias | Friedman, Wilcoxon, Spearman y regresión robusta HAC | Cuatro familias; adaptaciones por dependencia temporal explicadas |
| Supuestos, estadístico, p, IC y efecto | `contrastes_fase2.csv`, `supuestos_fase2.csv` e informe | Documentados; limitaciones explícitas |
| Corrección múltiple e IC bootstrap | Bonferroni; remuestreo de pares anuales y bloques residuales | Calculados |
| Fase 2, hasta 15 páginas | `Fase_2_Inferencia.pdf`, 10 páginas | Generado |
| Modelos de familias distintas | Ridge, Random Forest, SVR y ETS, además de dos referencias | Cuatro familias aprendidas |
| Búsqueda sin consultar prueba | 22 especificaciones y cuatro cortes anuales; selección congelada | Registrada |
| Partición cronológica | Desarrollo hasta 2022; calibración 2023; prueba 2024 | Implementada |
| Métricas de regresión y referencias | MAE, RMSE, MAPE y R² de prueba; ajuste y validación | Calculadas, incluido R² negativo |
| Análisis de errores e interpretación | Cinco peores meses; residuos; importancia en validación | Incluidos |
| Fase 3, hasta 15 páginas | `Fase_3_Modelado_y_Evaluacion.pdf`, 15 páginas | Generado |
| Modelo serializado y script de inferencia | Dos `.joblib` y `src/inference.py` | Predicciones reproducidas |
| Informe integrador, hasta 30 páginas | `Informe_Integrador.pdf`, 21 páginas | Generado |
| Notebooks y exportaciones HTML | Tres notebooks ejecutados; tres HTML en `output/html` | Sin errores de ejecución |
| README, dependencias y estructura | `README.md`, `requirements.txt`, `/data`, `/src`, `/notebooks`, `/output` | Incluidos |
| Historial de Git | Repositorio local con autoría de asistencia declarada | No simula aportes de integrantes |
| Carátulas, índice y páginas | Presentes en los informes; nombres confirmados | **Legajos pendientes de informar** |
| Revisión e interpretación del grupo | Declaración de IA en los informes y guía de Fase 3 | **Pendiente del grupo, según sección 11** |
| Publicación y entrega a la cátedra | No se enviaron archivos ni mensajes a terceros | **A cargo del grupo** |

Las correcciones listadas en los informes describen cambios técnicos respecto del enfoque anterior. No se inventaron devoluciones de la profesora. Las fechas históricas del calendario de la consigna no se usan como plazos nuevos.

No se creó una presentación final, porque el encargo actual corresponde a las tres fases. La exposición requiere comprensión y participación de los integrantes.
