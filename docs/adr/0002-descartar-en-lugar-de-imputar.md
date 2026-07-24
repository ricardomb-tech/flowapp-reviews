# ADR-0002: Descartar registros inválidos en lugar de imputarlos

- **Estado:** Aceptado
- **Fecha:** 2026-07-23
- **Autor:** Ricardo Martinez B

## Contexto

El dataset del reto incluye registros con valores nulos, calificaciones inválidas y duplicados. Antes de realizar cualquier análisis era necesario decidir cómo tratar esos casos.

Las dos alternativas más comunes eran:

1. **Imputar** los valores faltantes o corregir automáticamente algunos registros (por ejemplo, completar un rating nulo con la media o convertir `4.5` en `5`).
2. **Descartar** los registros que no cumplieran las reglas de validación.

Como el objetivo del proyecto es analizar las palabras más frecuentes según el nivel de rating, utilizar calificaciones inventadas o modificadas podría alterar los resultados y llevar a conclusiones incorrectas.

## Decisión

Se decidió conservar únicamente las filas que superan todas las validaciones.

Se descartan los registros que presentan alguno de estos casos:

- texto ausente o vacío;
- rating ausente;
- rating no numérico;
- rating fuera del rango permitido (1–5);
- duplicados exactos;
- duplicados después de normalizar el texto.

Cada descarte queda registrado en `CleaningReport`, indicando el número de línea y el motivo correspondiente.

Como comprobación adicional, el proceso verifica el siguiente invariante:

```text
filas válidas + filas rechazadas = total de filas leídas
```

## Justificación

El análisis posterior depende directamente del valor del rating para agrupar las reseñas. Si una calificación se completa o modifica de forma artificial, esa reseña termina formando parte de un grupo al que realmente no pertenece.

Se prefirió trabajar con un conjunto de datos más pequeño, pero compuesto únicamente por registros válidos y trazables.

## Consecuencias

### Ventajas

- El análisis utiliza únicamente información válida.
- Cada registro descartado puede justificarse mediante un motivo explícito.
- El proceso de limpieza es completamente auditable.

### Desventajas

- El número de reseñas disponibles para el análisis disminuye.
- Algunas reseñas con texto válido se descartan porque no es posible determinar su rating de forma confiable.

## Alternativas consideradas

| Alternativa | Motivo para no adoptarla |
|-------------|--------------------------|
| Imputar el rating con la media | Introduce datos artificiales que pueden sesgar la distribución y el análisis por nivel de rating. |
| Redondear valores como `4.5` | Cambia arbitrariamente la clasificación de la reseña dentro de la escala de evaluación. |