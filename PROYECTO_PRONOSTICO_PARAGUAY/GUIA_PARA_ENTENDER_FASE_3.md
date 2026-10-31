# Qué aprendió el modelo y cómo explicar el resultado

El SVR elegido por validación mejora las dos referencias en 2024, pero no aprende a anticipar bien los picos mensuales. Su capacidad principal es estimar un nivel relativamente estable. Eso es una conclusión del experimento, no un resultado que se haya ocultado para presentar un modelo exitoso.

## 1. Qué significa aprender aquí

Para cada mes de entrenamiento, el modelo recibe únicamente cantidades de meses anteriores y datos de calendario. Compara su predicción con la cantidad observada y ajusta sus parámetros para reducir errores. No recibe la cantidad del propio mes como entrada.

Se usan rezagos de uno, dos, tres, seis y doce meses; promedios anteriores de tres y doce meses; seno y coseno del mes; y días del mes. Son diez representaciones de la historia y el calendario. No son diez mediciones externas nuevas ni aumentan el número de meses disponibles.

Durante el pronóstico de un año completo, después del primer paso algunas entradas ya dependen de predicciones previas. Eso es más difícil que estimar un mes usando siempre el mes anterior real.

## 2. Qué dicen los errores

| Familia | MAE entrenamiento | MAE validación | MAE prueba 2024 |
|---|---:|---:|---:|
| SVR | 23,06 | 24,08 | 10,87 |
| Ridge | 18,36 | 26,24 | 10,67 |
| Random Forest | 12,59 | 30,44 | 32,61 |
| ETS | 20,19 | 31,00 | 31,30 |
| Media de los doce meses previos | 26,46 | 31,47 | 28,58 |
| Mismo mes del año anterior | 38,85 | 37,23 | 36,58 |

MAE se expresa en accidentes por mes: cuanto menor, mejor. Entrenamiento mide ajuste a un paso con historia real; validación y prueba miden doce pasos desde un origen fijo. Las columnas no tienen exactamente el mismo escenario.

Random Forest ajusta mucho más el entrenamiento, pero sus errores aumentan en períodos no usados para ajustarlo. Es un ejemplo de por qué memorizar el historial no basta. El salto también refleja cambios de período y horizonte; no se atribuye todo automáticamente al sobreajuste.

En SVR, un error menor en 2024 que en validación no demuestra que el modelo se haya vuelto mejor con el tiempo: 2024 es otro período y sus cantidades son relativamente estables. Solo hay un año de prueba.

## 3. Por qué se eligió SVR si Ridge tiene menor MAE de prueba

La elección se hizo antes de mirar los errores de 2024, usando la validación temporal de 2019 a 2022. SVR ganó esa comparación. Cambiar a Ridge después de ver prueba usaría el año reservado para seleccionar modelos y dejaría de ser una evaluación independiente del ajuste.

Se informa el resultado de Ridge con transparencia, pero no se redefine al ganador.

## 4. Por qué el R² negativo importa

SVR tiene R² de aproximadamente −0,477 en 2024. Eso significa que su error cuadrático es mayor que el de una constante igual a la media real de ese año. Esa media solo se conoce después de observar el año y no podía usarse como pronóstico operativo desde diciembre de 2023.

Aun así, el R² señala una limitación real: las predicciones están aproximadamente entre 132 y 135 siniestros mensuales, mientras los conteos reales van de 126 a 174. El modelo mejora referencias históricas, pero no explica bien las fluctuaciones mensuales.

MAPE de 7,13% no debe anunciarse como «92,87% de precisión». En regresión, ese complemento no es una métrica de exactitud.

## 5. Qué pronóstico se puede mostrar

El modelo evaluado pronosticó 2024 desde diciembre de 2023. Predijo un total de 1.602,36 siniestros, frente a 1.709 registrados: una subestimación de 106,64, aproximadamente 6,24% del total observado.

Después se reajustó la misma especificación con datos hasta diciembre de 2024 y se produjo una proyección de 2025 de 1.625,09 siniestros. Esa proyección no está validada con 2025 real y no es un pronóstico actualizado de 2027.

La banda mensual es amplia y orientativa. Haber contenido los doce valores de un año no garantiza una cobertura futura del 90%, porque los errores temporales no son necesariamente intercambiables.

## 6. Relación con las fases anteriores

La Fase 1 demuestra qué representan las filas y cómo se obtuvieron. La Fase 2 encuentra asociación de corto plazo con el mes anterior. La Fase 3 comprueba que esa asociación no asegura capacidad de pronóstico anual: la recursión, los cambios de nivel y la poca historia dificultan la generalización.

Una respuesta defendible sería: «Mejoramos dos referencias operativas, pero nuestro modelo estima sobre todo el nivel y no anticipa los picos. Por eso no proponemos usarlo automáticamente para asignar recursos. El siguiente experimento necesita datos más recientes y variables disponibles antes del período a pronosticar».

Esta guía explica resultados calculados. El grupo debe revisarlos y decidir su interpretación según la consigna, declarando la asistencia de IA.
