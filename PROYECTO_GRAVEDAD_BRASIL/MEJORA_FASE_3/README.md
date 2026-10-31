# Mejora acotada de la fase 3 — PRF Brasil

Abrir `ABRIR_MEJORA.html`. Este complemento conserva el proyecto original y documenta una segunda versión, seleccionada antes de leer la nueva prueba de 2026. No se amplió la búsqueda después de ver los resultados.

## Experimento

- Ocho configuraciones LightGBM, 24 ajustes CV (2021, 2022, 2023).
- Base de 24 predictores; contexto vehicular; enriquecimiento con trazado y marca aproximada. Cantidades exactas de campos en `output/diccionario_bloques.json`.
- El contexto se forma con TODOS los vehículos identificados del archivo de personas, incluidos ilesos y registros sin persona. Se deduplica `(id,id_veiculo>0)` y se resta el propio al contar otros vehículos. No identifica necesariamente parejas de colisión en accidentes múltiples.
- Ambos modelos se entrenan en 2017–2023; calibración 2024 H1; umbral 2024 H2. Misma población para comparar; las mejoras no se deben a entrenar uno con más años.
- Candidato elegido: `Contexto_regularizado_natural`. Criterio: AP media superior a referencia y mejora en al menos dos cortes, sin seleccionar con 2025/2026.
- 2025 es comparación retrospectiva; 2026 es nueva prueba cronológica, leída después del congelamiento. Período real: 2026-01-01 a 2026-09-30; 67.591 víctimas, 4.610 fallecidas. No es un año completo ni un seguimiento de mortalidad a 30 días.
- 300 bootstrap pareados por accidentes completos, respetando víctimas del mismo evento. La incertidumbre no incluye todos los sesgos de cobertura o cambios temporales.

Los originales de 2026 proceden de los enlaces del portal oficial PRF y se guardan con URL y SHA-256 en `manifiesto_2026.json`. Fueron descargados como ZIP opacos antes de la selección y abiertos después del congelamiento. No se presentó ningún pedido institucional ni se enviaron datos a terceros.

## Reproducir

Este directorio se ubica dentro de `PROYECTO_GRAVEDAD_BRASIL` y utiliza sus dependencias y módulos de `src`. No instalar herramientas nuevas para esta ronda. Desde ese proyecto:

```powershell
python MEJORA_FASE_3/descargar_2026.py
python MEJORA_FASE_3/mejorar.py
python MEJORA_FASE_3/presentar.py
python MEJORA_FASE_3/notebook.py
python MEJORA_FASE_3/inferencia.py --entrada MEJORA_FASE_3/data/ejemplo_inferencia.csv --salida MEJORA_FASE_3/output/ejemplo_predicciones.csv
```

`mejorar.py` reutiliza resultados existentes y verifica hashes; no vuelve a seleccionar con la prueba. El notebook está ejecutado y muestra la auditoría, la búsqueda y las métricas calculadas. Una ejecución desde cero requiere los originales 2017–2025 y 2026, o descargar sus cortes verificables. Repetir retrospectivamente un experimento no convierte un período ya visto en una prueba ciega nueva.

La entrada de inferencia usa características YA preparadas y códigos compatibles. `familia_otro_vehiculo` y conteos requieren el conjunto completo de vehículos del siniestro; no pueden rellenarse desde una sola víctima aislada ni usarse antes de que se conozca el evento.

## Relación con las tres fases

Fase 1: el complemento añade auditoría y documentación del contexto vehicular sin fabricar participantes ni modificar el objetivo. Fase 2: se mantienen las hipótesis y límites originales; la ganancia predictiva no demuestra un efecto causal de estas características. Fase 3: se añade esta comparación y el nuevo modelo serializado como segunda versión. El informe original y su ZIP quedan intactos. Para una entrega consolidada deben incorporarse estas decisiones a la narración, sin confundir 2025 retrospectivo con la prueba nueva.

Las decisiones están en `protocolo.json`, la grilla en `output/grilla_fijada.json`, y el congelamiento con hashes de modelos y fecha UTC en `output/congelamiento.json`. Los resultados y predicciones están en `output/`. Los scripts no inventan integrantes, legajos o aprobaciones docentes. Material de apoyo con IA que el grupo debe revisar y comprender.
