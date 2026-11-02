"""Explicaciones compartidas por los informes y los notebooks."""
F1_TITULOS = {
 'f1_01_clases.png':'Cantidad de heridos y fallecidos',
 'f1_02_histograma_edad.png':'Cómo se distribuyen las edades',
 'f1_03_cajas_edad.png':'Comparación de edades entre los grupos',
 'f1_04_serie_temporal.png':'Cambios a lo largo del tiempo',
 'f1_05_vehiculos.png':'Diferencias según el vehículo',
 'f1_06_dispersion.png':'Edad y antigüedad del vehículo',
 'f1_07_correlaciones.png':'Relaciones entre variables numéricas',
 'f1_08_dia_hora.png':'Diferencias por día y horario',
 'f1_09_faltantes.png':'Información que falta en los registros',
 'f1_10_contexto.png':'Otros vehículos en el accidente',
}
F1_TEXTOS = {
 'f1_01_clases.png':'En los datos de desarrollo hay 38.619 fallecidos entre 573.747 víctimas: alrededor del 7 %. Los heridos son muchos más. Por eso, en la fase 3 no alcanza con contar los aciertos totales: también debemos revisar si el modelo identifica a los fallecidos.',
 'f1_02_histograma_edad.png':'La edad mediana es de 35 años en heridos y 39 en fallecidos. La mediana deja la mitad de los casos a cada lado. Usamos proporciones para comparar los grupos sin que la mayor cantidad de heridos tape a los fallecidos.',
 'f1_03_cajas_edad.png':'Los dos grupos comparten muchas edades. Aunque los fallecidos tienen una edad central algo mayor, conocer la edad no alcanza para saber cómo terminará un caso. No eliminamos una edad válida solo por estar alejada de las demás.',
 'f1_04_serie_temporal.png':'La cantidad de víctimas y la proporción de fallecidos cambian entre meses y años. Esto puede relacionarse con la circulación y con la forma de registrar los casos. El gráfico cuenta víctimas registradas, no todos los viajes. Por eso evaluamos respetando el orden de los años.',
 'f1_05_vehiculos.png':'La proporción de fallecidos cambia según el vehículo. Calculamos cada porcentaje dentro de su grupo. Esto no demuestra que un vehículo sea más seguro por viaje: aquí observamos personas que ya resultaron heridas o fallecidas.',
 'f1_06_dispersion.png':'Cada punto representa un caso. Mostramos 3.000 heridos y 3.000 fallecidos para que ambos grupos se vean; esa selección solo se usa en el gráfico. Los puntos se mezclan bastante: estas dos características no separan completamente los resultados.',
 'f1_07_correlaciones.png':'El mapa resume qué variables tienden a cambiar juntas de forma lineal. Las coordenadas indican ubicación, no una característica personal. Una correlación no demuestra que una variable cause el resultado ni garantiza que ayude a predecir.',
 'f1_08_dia_hora.png':'Los colores muestran la proporción de fallecidos por día y hora, usando celdas con al menos 30 víctimas. Estas diferencias nos llevan a estudiar la noche en la fase 2. No podemos separar aquí el horario de otros factores, como cuánto se circula o qué choques ocurren.',
 'f1_09_faltantes.png':'No todos los registros tienen la misma información. Conservamos las víctimas y marcamos lo desconocido. LightGBM admite números faltantes; en los modelos que necesitan completarlos, aprendemos el reemplazo solo con entrenamiento.',
 'f1_10_contexto.png':'Relacionamos los vehículos mediante el identificador real del accidente. Así sabemos si aparecen otros vehículos pesados, motos o vehículos ligeros. La categoría de varios vehículos no indica exactamente quién chocó con quién. Estas diferencias no prueban causas.',
}
F3_TEXTOS = {
 '01_busqueda_CV.png':'Probamos ocho configuraciones en tres cortes de tiempo. En cada corte entrenamos con años anteriores y evaluamos en el siguiente. Elegimos según la validación, sin usar 2026 para ajustar parámetros.',
 '02_comparacion_2026.png':'Evaluamos ambos modelos sobre las mismas víctimas de enero a septiembre de 2026. El modelo final de 31 variables mejora a la referencia de 24 variables. Los dos mantienen sus puntos de decisión elegidos con 2024.',
 '03_curvas_2026.png':'Las curvas permiten comparar distintos puntos de decisión. AUC resume si el modelo suele asignar mayor riesgo a fallecidos que a heridos. La curva precisión-recall combina cuántos fallecidos encuentra y cuántas alertas acierta. AUC 0,845 no significa 84,5 % de aciertos.',
 '04_confusion_2026.png':'De 4.610 fallecidos, identificamos 1.953 y clasificamos 2.657 como heridos. Además, el modelo marca como fallecidos a 3.277 heridos: esas son las falsas alarmas. Frente a la referencia encuentra 132 fallecidos más y genera 717 falsas alarmas menos.',
 'f3_05_generalizacion.png':'El modelo rinde mejor con los datos usados para aprender: AP es 0,456 en entrenamiento, 0,358 en validación y 0,352 en 2026. Parte del rendimiento de entrenamiento no se mantiene en casos posteriores. La cercanía entre validación y prueba es favorable, pero no garantiza el mismo resultado en cualquier año.',
 'f3_06_calibracion.png':'Calibrar significa ajustar los porcentajes de riesgo. Si muchos casos reciben un riesgo del 20 %, buscamos que cerca de 20 de cada 100 hayan terminado en fallecimiento. Usamos enero-junio de 2024 para ese ajuste. La curva revisa grupos; no garantiza lo que le pasará a una persona.',
 'f3_07_importancia.png':'Mezclamos los valores de una variable en una muestra de validación y observamos cuánto empeora el modelo. Una caída mayor indica que esa información ayudaba más. Dos variables parecidas pueden reemplazarse parcialmente. Importancia para predecir no significa que sea una causa.',
 'f3_08_umbrales.png':'Con la decisión elegida encontramos cerca de 42 de cada 100 fallecidos y acertamos cerca de 37 de cada 100 alertas de fallecimiento. Al bajar la exigencia para alertar encontramos cerca de 81 de cada 100 fallecidos, pero solo unas 17 de cada 100 alertas son correctas. Detectar más implica aceptar más falsas alarmas.',
}
