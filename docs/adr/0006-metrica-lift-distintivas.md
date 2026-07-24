# ADR-0006: Incorporar la métrica *lift* para identificar palabras distintivas

- **Estado:** Aceptado
- **Fecha:** 2026-07-23
- **Decisores:** Ricardo Martinez B

## Contexto

El reto solicita identificar las palabras más frecuentes para cada nivel de
rating. Ese requisito se cumple calculando la frecuencia de aparición de cada
término dentro de cada grupo.

Sin embargo, durante las pruebas apareció una limitación: muchas de las palabras
más repetidas son comunes a todas las reseñas, independientemente de si la
calificación es buena o mala. Términos como `app`, `flowapp` o `funciona`
tienden a ocupar los primeros lugares porque describen el producto, no porque
caractericen un nivel específico de satisfacción.

Esto hace que los rankings de distintos ratings sean muy parecidos y aporten
poca información para entender qué diferencia realmente una reseña positiva de
una negativa.

## Decisión

Mantener el ranking de palabras más frecuentes para cumplir el requisito del
reto e incorporar un segundo análisis basado en la métrica **lift**.

Cada grupo de rating presenta dos listas:

1. **Palabras más frecuentes**, ordenadas por número de apariciones.
2. **Palabras distintivas**, calculadas mediante la relación entre la frecuencia
   relativa de una palabra dentro del grupo y su frecuencia relativa en todo el
   dataset.

La métrica utilizada es:

```text
lift(palabra, grupo) =
frecuencia relativa en el grupo /
frecuencia relativa global
```

Además, se establece un umbral mínimo de apariciones (`--min-lift-count`,
valor por defecto: `2`) para evitar que palabras presentes una única vez
aparezcan en los primeros lugares únicamente por tener un *lift* muy alto.

## Consecuencias

### Positivas

- Permite identificar palabras que realmente caracterizan cada nivel de rating
  y no solo las más repetidas en todo el conjunto de datos.
- Complementa el análisis solicitado por el reto sin reemplazarlo.
- Hace que los resultados sean más útiles para interpretar el comportamiento de
  los usuarios y detectar patrones de satisfacción o insatisfacción.
- Aporta un valor analítico adicional al proyecto sin aumentar su complejidad de
  uso.

### Negativas

- Introduce una métrica que no forma parte del requisito mínimo del enunciado,
  por lo que debe explicarse en la documentación.
- El concepto de *lift* puede resultar menos intuitivo para alguien que no esté
  familiarizado con métricas estadísticas.
- Requiere calcular frecuencias globales además de las frecuencias por grupo.

## Alternativas consideradas

| Alternativa | Motivo de descarte |
| --- | --- |
| Reportar únicamente las palabras más frecuentes | Cumple el reto, pero ofrece poca capacidad para diferenciar los distintos niveles de rating. |
| Utilizar TF-IDF | Proporciona resultados similares, pero añade complejidad innecesaria para el tamaño y objetivo del proyecto. |
| No establecer un mínimo de apariciones | Palabras con una sola ocurrencia podrían aparecer como muy relevantes debido a un *lift* artificialmente alto. |