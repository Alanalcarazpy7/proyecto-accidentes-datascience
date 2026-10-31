# Cómo interpretar la fase 3 y el desbalance

**Sí hay mejora en la discriminación con más información real.** En las mismas víctimas de Brasil de 2025, AUC pasa de 0,619 (sexo/edad) a 0.806; AP de 0,104 a 0.302; F1 macro de 0,512 a 0.651. La mejora de AP tiene IC bootstrap por accidente aproximadamente 0,187–0,211. No es porcentaje de exactitud ni comparación causal entre países.

Una regla que responde siempre herido acierta 93,26% porque fallecidos son 6,74%. Detecta cero fallecidos. Por eso exactitud alta sola no sirve.

| Regla fijada antes de prueba | Detecta de cada 100 fallecidos | Acierta de cada 100 alertas de fallecimiento | Falsas alarmas en 2025 |
|---|---:|---:|---:|
| Siempre herido | 0 | 0 (ninguna alerta) | 0 |
| Umbral 0,50 | 7,40 | 58,05 | 323 |
| Umbral principal 0,1866 | 40,58 | 31,78 | 5.264 |
| Mayor detección, umbral 0,0415 | 81,98 | 13,51 | 31.721 |

**Qué hicimos:** entrenamiento con todos los casos reales; comparación de pesos sin tocar prueba; selección por AP temporal; calibración con 2024 H1 y prevalencia natural; umbral con 2024 H2; evaluación de todos los puntos congelados en 2025. No inventamos fallecidos, no duplicamos víctimas para inflar N ni balanceamos el examen. SMOTE no es necesario para tener un experimento válido y aquí no se utilizó.

**Precisión** responde cuántas alertas fueron correctas. **Recall** responde cuántos fallecidos reales fueron detectados. **F1 de fallecidos** combina ambas; **F1 macro** promedia las dos clases. **AP** resume el ordenamiento de casos en la curva precisión-recall y depende de la prevalencia. **AUC-ROC** mide discriminación. **Brier/calibración** examinan las probabilidades, sin prometer certeza individual.

El umbral principal detecta 2.452 de 6.043 fallecidos, omite 3.591 y clasifica erróneamente como fallecidos a 5.264 heridos. El punto de mayor detección omite 1.089 fallecidos. Decidir cuál conviene depende del costo de perder un caso frente al de una falsa alarma; no se ha definido una aplicación clínica ni una política institucional.

**Qué aprendió:** tipo de siniestro, vehículo, municipio, rol, ruralidad y edad aportan información. La importancia por permutación se midió en validación; no equivale a causalidad. AP de entrenamiento 0,395 frente a 0,298 en validación y 0,302 en prueba muestra optimismo en el ajuste: más filas no elimina el sobreajuste.

**Comparación anterior:** Paraguay tenía AUC 0,581, F1 macro 0,530, precisión 23,24% y recall 45,41%. Brasil mejora discriminación y precisión al punto principal, pero su recall principal es menor. Las poblaciones, prevalencias y divisiones son diferentes. La comparación controlada dentro de Brasil es la evidencia más clara del aporte de más variables.

**Frase defendible:** “El nuevo dataset permitió relacionar características reales y superar ampliamente al modelo de solo sexo y edad en el mismo año de prueba. No logramos una predicción perfecta; mostramos la sensibilidad del resultado al umbral, las falsas alarmas y los fallecidos no detectados”.
